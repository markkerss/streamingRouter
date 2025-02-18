from client_library.clientLibrary import ClientLibrary
from threading import Thread

class Main:
  def __init__(self):
    self.list = ["cat", "dog", "giraffe", "elephant", "lemur"]
  
  def run(self):
    simpleServer = ClientLibrary("simple")
    for i in range(2):
      simpleServer.add_query(self.list[i])
    print(simpleServer.run_query(self.list[2]))
    print(simpleServer.run_query(self.list[3]))
  
  def run2(self):
    simpleServer = ClientLibrary("simple")
    for i in range(3):
      simpleServer.add_query(self.list[i])
    print(simpleServer.run_query(self.list[3]))
    print(simpleServer.run_query(self.list[4]))

if __name__ == "__main__":
  main = Main()
  Thread(target=main.run(), daemon=True).start()
  Thread(target=main.run2(), daemon=True).start()