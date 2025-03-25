from serverTemplate import ServerTemplate
from crewai import Agent, LLM, Task
import os
from langchain_community.llms.ollama import Ollama
class MarketResearcherAgent(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="market_researcher", port=port)

    llm = LLM(
      model="ollama/llama3.1:8b",
      base_url="http://localhost:11434",
    )

    self.agent = Agent(
      role="Market Researcher",
      goal="Provide detailed market research and recommendations",
      backstory="A certified market researcher with expertise in market research and analysis, with a track record of successful client relationships.",
      llm=llm
    )
    
  def add_query(self, chunk):
    return chunk
  
  def run_query(self, chunks):
    prompt = " ".join(chunks)
    task = Task(
      description=prompt,
      agent=self.agent,
      expected_output="Detailed market research and recommendations"
    )
    response = self.agent.execute_task(task)
    return [response]

def serve():
  server = MarketResearcherAgent()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()