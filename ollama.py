import requests
import time
def generate_with_ollama(prompt, model="llama3.1:8b"):
    url = "http://localhost:11434/api/generate"
    
    data = {
        "model": model,  # The model you want to use
        "prompt": prompt,
        "stream": False,  # Set to True if you want streaming responses
        # "parameters": {
        #     "max_tokens": 400,
        # },
        "options": {
            "num_predict": 10
        }
    }
    
    start_time = time.time()
    response = requests.post(url, json=data)
    end_time = time.time()
    
    response = response.json()['response']
    print(response)
    print(f"Time taken: {end_time - start_time} seconds\n", "Length of response: ", len(response))
    with open("response.txt", "w") as f:
        f.write(response)
    return response

for i in range(5):
  expert_responses = ""
  user_query = "Create a stock portfolio for a 30 year old with interest in exposure to Mag 7 stocks, and bonds"
  analyst_query = f"Please analyze the following query from a financial analysis perspective: '{user_query}'. Provide detailed financial analysis that would be helpful for a financial advisor."
  print("Financial Analyst:")
  expert_responses += generate_with_ollama(analyst_query)

  researcher_query = f"Please analyze the following query from a market research perspective: '{user_query}'. Provide relevant market trends and data that would be helpful for a financial advisor."
  print("Market Researcher:")
  expert_responses += generate_with_ollama(researcher_query)

  advisor_query = f"Please analyze the following query from an investment perspective: '{user_query}'. Provide specific investment recommendations that would be helpful for a financial advisor."
  print("Investment Advisor:")
  expert_responses += generate_with_ollama(advisor_query)

  print("Financial Advisor:")
  advisor_query = f"Client Query: {user_query}\n\n{expert_responses}\n\nBased on the insights from all three experts, please provide a comprehensive and integrated financial advice response for the client. Incorporate the most relevant information from each expert into a cohesive recommendation."
  final_response = generate_with_ollama(advisor_query)
  