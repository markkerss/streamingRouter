from serverTemplate import ServerTemplate
from crewai import Agent, Task, LLM
from client_library.clientLibrary import ClientLibrary

class FinancialAdvisorAgent(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="financial_advisor", port=port)
    print("=== Initializing Financial Advisor Agent ===")
    
    llm = LLM(
      model="ollama/llama3.1:8b",
      base_url="http://localhost:11434",
    )

    print("LLM initialized")

    self.agent = Agent(
      role="Financial Advisor",
      goal="Provide personalized financial advice and portfolio recommendations",
      backstory="A certified financial advisor with expertise in portfolio management and wealth planning, with a track record of successful client relationships.",
      llm=llm
    )

    print("Agent initialized successfully")
    
  def add_query(self, chunk):
    return chunk
  
  def run_query(self, chunks):
    # Combine chunks into a single prompt
    user_query = " ".join(chunks)
    print(f"Processing query with {len(chunks)} chunks")
    
    print("Contacting financial analyst...")
    analyst_query = f"Please analyze the following query from a financial analysis perspective: '{user_query}'. Provide detailed financial analysis that would be helpful for a financial advisor."
    analyst_response = self._contact_financial_analyst(analyst_query)
    print("Received response from financial analyst")
    analyst_response = f"\nFinancial Analyst Response: {analyst_response}"
    
    # Always contact market researcher regardless of initial response
    print("Contacting market researcher...")
    researcher_query = f"Please analyze the following query from a market research perspective: '{user_query}'. Provide relevant market trends and data that would be helpful for a financial advisor."
    researcher_response = self._contact_market_researcher(researcher_query)
    print("Received response from market researcher")
    researcher_response = f"\nMarket Researcher Response: {researcher_response}"
    
    # Always contact investment advisor regardless of initial response
    print("Contacting investment advisor...")
    advisor_query = f"Please analyze the following query from an investment perspective: '{user_query}'. Provide specific investment recommendations that would be helpful for a financial advisor."
    advisor_response = self._contact_investment_advisor(advisor_query)
    print("Received response from investment advisor")
    advisor_response = f"\nInvestment Advisor Response: {advisor_response}"
    
    expert_responses = analyst_response + researcher_response + advisor_response
    
    # Final comprehensive response task
    print("Creating final task with all expert responses")
    final_task = Task(
      description=f"Client Query: {user_query}\n\n{expert_responses}\n\nBased on the insights from all three experts, please provide a comprehensive and integrated financial advice response for the client. Incorporate the most relevant information from each expert into a cohesive recommendation.",
      agent=self.agent,
      expected_output="Comprehensive financial advice and portfolio recommendations"
    )
    
    print("Executing final financial advisor task...")
    final_response = self.agent.execute_task(final_task)
    print("Final response generated")
    print(f"Final response length: {len(final_response)} characters")
    
    return [final_response]
  
  def _contact_financial_analyst(self, prompt):
    try:
      print("Connecting to financial analyst service")
      client = ClientLibrary("financial_analyst")
      response = client.run_query(prompt)
      print("Successfully received response from financial analyst service", response)
      return response[0]
    except Exception as e:
      print(f"ERROR: Error contacting financial analyst: {str(e)}")
      return "Error: Unable to contact financial analyst service."

  def _contact_market_researcher(self, prompt):
    try:
      print("Connecting to market researcher service")
      client = ClientLibrary("market_researcher")
      response = client.run_query(prompt)
      print("Successfully received response from market researcher service", response)
      return response[0]
    except Exception as e:
      print(f"ERROR: Error contacting market researcher: {str(e)}")
      return "Error: Unable to contact market researcher service."
  
  def _contact_investment_advisor(self, prompt):
    try:
      print("Connecting to investment advisor service")
      client = ClientLibrary("investment_advisor")
      response = client.run_query(prompt)
      print("Successfully received response from investment advisor service", response)
      return response[0]
    except Exception as e:
      print(f"ERROR: Error contacting investment advisor: {str(e)}")
      return "Error: Unable to contact investment advisor service."

def serve():
  print("=== Starting Financial Advisor Agent server ===")
  server = FinancialAdvisorAgent()  # Dynamic port
  print("Server started, waiting for termination")
  server.wait_for_termination()

if __name__ == "__main__":
  serve()