from client_library.clientLibrary import ClientLibrary

class Main:
  def __init__(self):
    self.list = ["cat", "dog", "giraffe", "elephant", "lemur"]
  
  def run(self):
    simpleServer = ClientLibrary("simple")
    for i in range(2):
      simpleServer.add_query(self.list[i])
    print(simpleServer.run_query(self.list[2]))
    print(simpleServer.run_query(self.list[3]))

if __name__ == "__main__":
  Main().run()