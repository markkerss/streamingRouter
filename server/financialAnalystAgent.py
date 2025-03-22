from serverTemplate import ServerTemplate
from crewai import Agent
from utils.vllm import VLLMLLM

class FinancialAnalystAgent(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="financial_analyst", port=port)

    vllm_llm = VLLMLLM(
      model_name="meta-llama/Llama-3.1-8B",
      tensor_parallel_size=1
    )

    self.agent = Agent(
      role="Financial Analyst",
      goal="Provide detailed financial analysis and recommendations",
      backstory="A certified financial analyst with expertise in financial modeling and valuation, with a track record of successful client relationships.",
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
  server = FinancialAnalystAgent()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()