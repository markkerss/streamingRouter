import json
import asyncio
import sys
import parse
from transformers import AutoTokenizer
from client_library.clientLibrary import ClientLibrary
import time

client = ClientLibrary("parrotserve")

def load_workloads(branches_num: int):
    """Returns something like:

    {"shared_prompt": xxx, "diverged_prompt": xxx, "output_len": xxx}

    """

    tokenizer = AutoTokenizer.from_pretrained("hf-internal-testing/llama-tokenizer")

    with open("../router/data/log_3_round.jsonl", encoding="utf8") as f:
        log = [json.loads(line) for line in f.readlines()]

    # Replicate round
    replicate_num = 3
    replicated = []
    for _ in range(replicate_num):
        replicate_body = log[2:].copy()
        replicated.extend(replicate_body)
    log.extend(replicated)

    ret = []

    for i, round in enumerate(log):
        idx = i
        if idx > 3:
            idx = idx % 2 + 2

        queries = round[f"r{idx}_queries"]
        responses = round[f"r{idx}_responses"]

        previous_prompt = None
        shared_prompt = ""

        round_info = []

        counter = 0

        batch_sum = 0

        for kk in range(branches_num):
            keys = list(queries.keys())
            if len(keys) == 1:
                k = keys[0]
            else:
                k = keys[kk % 8]

            counter += 1

            query = queries[k]
            response = responses[k]

            prompt = query["system"] + query["user_msg"]
            prompt_len = len(tokenizer.encode(prompt, add_special_tokens=False))

            output = response["choices"][0]["message"]["content"]
            output_len = len(tokenizer.encode(output, add_special_tokens=False))

            batch_sum += prompt_len + output_len

            if previous_prompt is None:
                previous_prompt = prompt
            elif shared_prompt == "":
                # Find common prefix.
                for j in range(min(len(prompt), len(previous_prompt))):
                    if prompt[j] != previous_prompt[j]:
                        break
                shared_prompt = prompt[:j]

            round_info.append({"output_len": output_len})

        print("batch_sum: ", batch_sum, flush=True)

        for info in round_info:
            info["shared_prompt"] = shared_prompt
            info["diverged_prompt"] = prompt[len(shared_prompt) :]
            info["shared_prompt_len"] = len(
                tokenizer.encode(shared_prompt, add_special_tokens=False)
            )
            info["diverged_prompt_len"] = len(
                tokenizer.encode(info["diverged_prompt"], add_special_tokens=False)
            )

        ret.append(round_info)

    return ret


def execute(workloads):
    for round_info in workloads:
        for info in round_info:
            client.run_query(json.dumps(info))


def main(branches_num: int):
    print("branches_num: ", branches_num, flush=True)

    workloads = load_workloads(branches_num)
    start = time.time()
    execute(workloads)
    print(f"Time: {time.time() - start:.4f} (s)", flush=True)

    # Browse the log to get the max allocated memory.
    max_num_tokens = 0
    with open("../ParrotServe/artifact/figure17/log/engine_noOS.log", "r") as f:
        lines = f.readlines()
        for line in lines:
            result = parse.parse(
                "{pre}num_cached_tokens: {num_tokens}",
                line,
            )
            if result is not None:
                max_num_tokens = max(max_num_tokens, int(result["num_tokens"]))
    print(f"blocks_num:  {max_num_tokens // 16}", flush=True)


if __name__ == "__main__":
    for bn in [4, 8, 12, 16]:
        main(bn)