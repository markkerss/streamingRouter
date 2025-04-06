from serverTemplate import ServerTemplate
from crewai import Agent, LLM, Task
import time
class FinancialAnalystAgent(ServerTemplate):
  def __init__(self, port=None, ip="localhost"):
    super().__init__(service_name="financial_analyst", port=port, ip=ip)

    llm = LLM(
      model="ollama/llama3.1:8b",
      base_url="http://localhost:11434",
      temperature=0.5,
      max_tokens=500,
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
    start_task_time = time.time()
    task = Task(
      description=prompt,
      agent=self.agent,
      expected_output="Detailed financial analysis and recommendations"
    )
    response = self.agent.execute_task(task)
    print("Task completed", time.time() - start_task_time)
    return [response]

def serve():
  server = FinancialAnalystAgent()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()