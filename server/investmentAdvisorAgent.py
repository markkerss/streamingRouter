from serverTemplate import ServerTemplate
from crewai import Agent
from utils.vllm import VLLMLLM

class InvestmentAdvisorAgent(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="investment_advisor", port=port)

    vllm_llm = VLLMLLM(
      model_name="meta-llama/Llama-3.1-8B",
      tensor_parallel_size=1
    )

    self.agent = Agent(
      role="Investment Advisor",
      goal="Provide detailed investment analysis and recommendations",
      backstory="A certified investment advisor with expertise in investment analysis and recommendations, with a track record of successful client relationships.",
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
  server = InvestmentAdvisorAgent()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()