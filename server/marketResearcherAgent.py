from serverTemplate import ServerTemplate
from crewai import Agent
from utils.vllm import VLLMLLM

class MarketResearcherAgent(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="market_researcher", port=port)

    vllm_llm = VLLMLLM(
      model_name="meta-llama/Llama-3.1-8B",
      tensor_parallel_size=1
    )

    self.agent = Agent(
      role="Market Researcher",
      goal="Provide detailed market research and recommendations",
      backstory="A certified market researcher with expertise in market research and analysis, with a track record of successful client relationships.",
      llm=vllm_llm
    )
    
  def add_query(self, chunk):
    return chunk
  
  def run_query(self, chunks):
    result = []
    for chunk in chunks:
      response = self.agent.run(chunk)
      result.append(response)
    return result

def serve():
  server = MarketResearcherAgent()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()