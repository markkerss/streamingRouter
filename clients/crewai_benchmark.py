from crewai import Agent, Crew, Task, Process, LLM
import time
class FinancialAdvisorCrew:
  def crew(self) -> Crew:
    start_time = time.time()
    user_query = "Create a stock portfolio for a 30 year old with interest in exposure to Mag 7 stocks, and bonds"
    llm = LLM(
      model="ollama/llama3.1:8b",
      base_url="http://localhost:11434",
      temperature=0.5,
      max_tokens=500
    )

    financialAdvisor = Agent(
      role="Financial Advisor",
      goal="Provide personalized financial advice and portfolio recommendations",
      backstory="A certified financial advisor with expertise in portfolio management and wealth planning, with a track record of successful client relationships.",
      verbose=True,
      llm=llm
    )

    financialAnalyst = Agent(
      role="Financial Analyst",
      goal="Provide a detailed analysis of the financial situation of the client",
      backstory="A financial analyst with expertise in financial modeling and analysis, with a track record of successful client relationships.",
      verbose=True,
      llm=llm
    )

    investmentAdvisor = Agent(
      role="Investment Advisor",
      goal="Provide personalized investment advice and portfolio recommendations",
      backstory="A certified investment advisor with expertise in portfolio management and wealth planning, with a track record of successful client relationships.",
      verbose=True,
      llm=llm
    ) 

    marketResearcher = Agent(
      role="Market Researcher",
      goal="Provide detailed market research and recommendations",
      backstory="A certified market researcher with expertise in market research and analysis, with a track record of successful client relationships.",
      verbose=True,
      llm=llm
    ) 
    
    task_one = Task(
      description=f"Please analyze the following query from a financial analysis perspective: '{user_query}'. Provide detailed financial analysis that would be helpful for a financial advisor.",
      agent=financialAnalyst,
      expected_output="Initial financial analysis and thoughts"
    )

    task_two = Task(
      description=f"Please analyze the following query from a market research perspective: '{user_query}'. Provide relevant market trends and data that would be helpful for a financial advisor.",
      expected_output="A report summarizing key trends in the market.",
      agent=marketResearcher
    )

    task_three = Task(
      description=f"Please analyze the following query from an investment perspective: '{user_query}'. Provide specific investment recommendations that would be helpful for a financial advisor.",
      expected_output="A personalized investment portfolio recommendation.",
      agent=investmentAdvisor
    )

    task_four = Task(
      description=f"Client Query: {user_query}\n\nBased on the insights from all three experts, please provide a comprehensive and integrated financial advice response for the client. Incorporate the most relevant information from each expert into a cohesive recommendation.",
      agent=financialAdvisor,
      expected_output="Comprehensive financial advice and portfolio recommendations",
      output_file="result_crewai.md",
      context=[task_one, task_two, task_three]
    )

    crew = Crew(
      agents=[financialAdvisor, financialAnalyst, investmentAdvisor, marketResearcher],
      tasks=[task_one, task_two, task_three, task_four],
      process=Process.sequential,
      verbose=True,
      cache=False
    )
    
    crew.kickoff()
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")

    print(f"Advisor task prompt: {task_four.output.description}")

if __name__ == "__main__":
  FinancialAdvisorCrew().crew()