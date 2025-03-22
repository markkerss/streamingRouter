import asyncio
import time
from vllm import AsyncLLMEngine, AsyncEngineArgs, SamplingParams
import re
from client_library.clientLibrary import ClientLibrary
from threading import Thread
from datasets import load_dataset

class Main:
  def __init__(self) -> None:
    engine_args = AsyncEngineArgs(model="meta-llama/Llama-3.1-8B", gpu_memory_utilization=0.5, enforce_eager=True)
    self.llm = AsyncLLMEngine.from_engine_args(engine_args)
    self.sampling_params = SamplingParams(temperature=0.7, max_tokens=100)
    self.matches = set()
    self.translationRouter = ClientLibrary("translation")
    self.calculatorRouter = ClientLibrary("calculator")
    self.callsNeeded = 0
    self.callsHappened = 0
    self.callResults = {}
    self.ccnet = load_dataset()

  async def generate_streaming(self, prompt):
    results_generator = self.llm.generate(prompt, self.sampling_params, request_id=time.monotonic())
    async for request_output in results_generator:
      text = request_output.outputs[0].text
      matches = re.findall(r'\[.*?\]', text)
      if len(matches) > 0 and matches[-1] not in self.matches:
        self.callsNeeded += 1
        Thread(target=self.callRouter, args=(matches[-1], self.callsNeeded), daemon=True).start()
        self.matches.add(matches[-1])
   
    while self.callsNeeded > self.callsHappened:
      time.sleep(1)
    
    def replace_request(match):
      replace_request.counter += 1
      return self.callResults[replace_request.counter - 1]
    
    replace_request.counter = 1
    result = re.sub(r'\[.*?\]', replace_request, text)
    print(result)

  def callRouter(self, request, chunkId):
    print("Calling router with this request", request)
    match = re.search(r'\[(.*?)\("([^"]*?)"\)\]', request)
    print("matches", match)
    if match:
      api_call = match.group(1)
      value = match.group(2)
      print("api_call", api_call)
      print("value", value)
      result = None
      print(f"API Call: {api_call}, Value: {value}")
      if api_call == "Translate":
        result = self.translationRouter.run_query(value)
      if api_call == "Calculator":
        result = self.calculatorRouter.run_query(value)
      self.callResults[chunkId] = result[0]
      self.callsHappened += 1
  
  def run(self):
    input_text = """If Sarah travels for 3.5 hours at 55 mph, she will have traveled __ miles.
    The English translation of the Italian word "bella" is __.
    If 12 books cost $15.75 each, the total cost is __ dollars.
    The English translation of the Italian word "amico" is __."""

    prompt = f"""
    Your task is to enhance the given text by inserting API calls for arithmetic calculations and translations.

    For arithmetic expressions, insert a call using the [Calculator("expression")] API where "expression" represents the calculation.
    For translations, insert a call using the [Translate("word")] API where "word" is the Italian word to be translated into English.

    Few-shot examples:

    Example 1:
    Input: If Bob travels 3 hours in a car doing 50 mph, he will have traveled __ miles.
    Output: If Bob travels 3 hours in a car doing 50 mph, he will have traveled [Calculator("3*50")] miles.

    Example 2:
    Input: The English translation of the Italian word "grazie" is __.
    Output: The English translation of the Italian word "grazie" is [Translate("grazie")].

    Example 3:
    Input: If 10 items cost $2.50 each, the total cost is __ dollars.
    Output: If 10 items cost $2.50 each, the total cost is [Calculator("10*2.50")] dollars.

    Example 4:
    Input: The English translation of the Italian word "ciao" is __.
    Output: The English translation of the Italian word "ciao" is [Translate("ciao")].

    Now, process the following input text by filling in the blanks with the appropriate API calls.

    Input:
    {input_text}

    Output:
    """
    asyncio.run(self.generate_streaming(prompt))

if __name__ == "__main__":
  Main().run()

