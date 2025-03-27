from serverTemplate import ServerTemplate
from crewai import Agent, LLM, Task
import time

class InvestmentAdvisorAgent(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="investment_advisor", port=port)
    
    llm = LLM(
      model="ollama/llama3.1:8b",
      base_url="http://localhost:11434",
    )

    self.agent = Agent(
      role="Investment Advisor",
      goal="Provide detailed investment analysis and recommendations",
      backstory="A certified investment advisor with expertise in investment analysis and recommendations, with a track record of successful client relationships.",
      llm=llm
    )
    
  def add_query(self, chunk):
    return chunk
  
  def run_query(self, chunks):
    prompt = " ".join(chunks)
    task = Task(
      description=prompt,
      agent=self.agent,
      expected_output="Detailed investment analysis and recommendations"
    )
    start_task_time = time.time()
    response = self.agent.execute_task(task)
    print("Task completed", time.time() - start_task_time)
    return [response]

def serve():
  server = InvestmentAdvisorAgent()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()