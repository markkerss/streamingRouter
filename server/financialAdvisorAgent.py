from serverTemplate import ServerTemplate
from crewai import Agent
from utils.vllm import VLLMLLM
import re
from client_library.clientLibrary import ClientLibrary

class FinancialAdvisorAgent(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="financial_advisor", port=port)
    
    vllm_llm = VLLMLLM(
      model_name="meta-llama/Llama-3.1-8B",
      tensor_parallel_size=1
    )

    self.agent = Agent(
      role="Financial Advisor",
      goal="Provide personalized financial advice and portfolio recommendations",
      backstory="A certified financial advisor with expertise in portfolio management and wealth planning, with a track record of successful client relationships.",
      llm=vllm_llm
    )
    
  def add_query(self, chunk):
    return chunk
  
  def run_query(self, chunks):
    # Combine chunks into a single prompt
    user_query = " ".join(chunks)
    
    # Create the base prompt with instructions for contacting experts
    prompt = f"{user_query}\n\nAs a Financial Advisor, you have the capability to contact specialized experts if needed:\n- You can contact a financial analyst for detailed financial analysis\n- You can contact a market researcher for market trends and data\n- You can contact an investment advisor for specific investment recommendations\n\nIf you need to use any of these resources, you MUST explicitly state which expert you want to contact and what specific information you are requesting from them. For example:\n'I am contacting the financial analyst to analyze the debt-to-income ratio and provide insights on debt consolidation options.'\n'I am contacting the market researcher to gather data on emerging market trends in renewable energy sectors.'\n'I am contacting the investment advisor to recommend specific ETFs for a low-risk retirement portfolio.'\n\nPlease provide comprehensive financial advice based on the query, utilizing these resources if necessary."
    
    # Get initial response from the agent
    response = self.agent.run(prompt)
    
    # Check for financial analyst requests
    analyst_requests = re.findall(r"I am contacting the financial analyst to (.*?)(?:\.|$)", response, re.IGNORECASE)
    if analyst_requests or "contact financial analyst" in response.lower():
      # Extract the specific request or use the full response
      analyst_query = analyst_requests[0] if analyst_requests else response
      analyst_response = self._contact_financial_analyst(analyst_query)
      follow_up_prompt = f"{prompt}\n\nFinancial Analyst Response: {analyst_response}\n\nPlease incorporate this analysis into your advice."
      response = self.agent.run(follow_up_prompt)
    
    # Check for market researcher requests
    researcher_requests = re.findall(r"I am contacting the market researcher to (.*?)(?:\.|$)", response, re.IGNORECASE)
    if researcher_requests or "contact market researcher" in response.lower():
      researcher_query = researcher_requests[0] if researcher_requests else response
      researcher_response = self._contact_market_researcher(researcher_query)
      follow_up_prompt = f"{prompt}\n\nMarket Researcher Response: {researcher_response}\n\nPlease incorporate this market data into your advice."
      response = self.agent.run(follow_up_prompt)
    
    # Check for investment advisor requests
    advisor_requests = re.findall(r"I am contacting the investment advisor to (.*?)(?:\.|$)", response, re.IGNORECASE)
    if advisor_requests or "contact investment advisor" in response.lower():
      advisor_query = advisor_requests[0] if advisor_requests else response
      advisor_response = self._contact_investment_advisor(advisor_query)
      follow_up_prompt = f"{prompt}\n\nInvestment Advisor Response: {advisor_response}\n\nPlease incorporate these investment recommendations into your advice."
      response = self.agent.run(follow_up_prompt)
    
    response = self.agent.run(response + "Given the above information, provide a comprehensive financial advice and portfolio recommendations.")
    
    return [response]
  
  def _contact_financial_analyst(self, prompt):
    client = ClientLibrary("financial_analyst")
    response = client.run_query(prompt)
    return response[0]

  def _contact_market_researcher(self, prompt):
    client = ClientLibrary("market_researcher")
    response = client.run_query(prompt)
    return response[0]
  
  def _contact_investment_advisor(self, prompt):
    client = ClientLibrary("investment_advisor")
    response = client.run_query(prompt)
    return response[0]

def serve():
  server = FinancialAdvisorAgent()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()