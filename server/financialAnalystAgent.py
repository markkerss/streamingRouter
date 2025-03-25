from serverTemplate import ServerTemplate
from crewai import Agent, LLM, Task
import os
from langchain_community.llms.vllm import VLLMOpenAI
from langchain_community.llms.ollama import Ollama
class FinancialAnalystAgent(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="financial_analyst", port=port)

    llm = LLM(
      model="ollama/llama3.1:8b",
      base_url="http://localhost:11434",
    )

    self.agent = Agent(
      role="Financial Analyst",
      goal="Provide detailed financial analysis and recommendations",
      backstory="A certified financial analyst with expertise in financial modeling and valuation, with a track record of successful client relationships.",
      llm=llm
    )
    
  def add_query(self, chunk):
    return chunk
  
  def run_query(self, chunks):
    prompt = " ".join(chunks)
    task = Task(
      description=prompt,
      agent=self.agent,
      expected_output="Detailed financial analysis and recommendations"
    )
    response = self.agent.execute_task(task)
    return [response]

def serve():
  server = FinancialAnalystAgent()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()