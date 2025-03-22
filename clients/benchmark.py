import json
from transformers import AutoTokenizer
from client_library.clientLibrary import ClientLibrary
import time
import multiprocessing as mp

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


def execute(workloads, barrier):
    client = ClientLibrary("parrotserve")
    barrier.wait()
    
    for round_info in workloads:
        for i in range(len(round_info) - 1):
            client.add_query(json.dumps(round_info[i]))
        result = client.run_query(json.dumps(round_info[len(round_info) - 1]))
        if len(result) > 0:
            with open("benchmark_output.txt", "a") as output_file:
                output_file.write(str(result[0]) + "\n")

def main():
    workloads = load_workloads(1)
    for num_clients in [8]:
        print(f"\nTesting with {num_clients} clients...")
        start = time.time()
        # Create a barrier to synchronize start
        barrier = mp.Barrier(num_clients)
        
        # Create and start client processes
        processes = []
        for _ in range(num_clients):
            p = mp.Process(
                target=execute,
                args=(workloads, barrier)
            )
            processes.append(p)
            p.start()
        
        # Wait for all processes to complete
        for p in processes:
            p.join()

        print(f"Clients: {num_clients}, Time: {time.time() - start:.4f} (s)", flush=True)

if __name__ == "__main__":
    main()