from client_library.clientLibrary import ClientLibrary

class Main:
  def __init__(self):
    pass
  
  def run(self):
    financialAdvisor = ClientLibrary("financial_advisor")

    response = financialAdvisor.run_query("Create a stock portfolio for a 30 year old with interest in exposure to Mag 7 stocks, and bonds")
    print(response)


if __name__ == "__main__":
  Main().run()