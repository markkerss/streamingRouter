from client_library.clientLibrary import ClientLibrary
import time
class Main:
  def __init__(self):
    pass
  
  def run(self):
    start_time = time.time()
    financialAdvisor = ClientLibrary("financial_advisor")

    response = financialAdvisor.run_query("Create a stock portfolio for a 30 year old with interest in exposure to Mag 7 stocks, and bonds")
    print(response[0])
    elapsed_time = time.time() - start_time
    print(f"Time taken: {elapsed_time} seconds")

if __name__ == "__main__":
  Main().run()