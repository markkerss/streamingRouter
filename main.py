from client_library.clientLibrary import ClientLibrary
import time

class Main:
  def __init__(self):
    self.list = ["cat", "dog", "giraffe", "elephant", "lemur"]
  
  def run(self):
    simpleServer = ClientLibrary("simple")
    for animal in self.list:
      simpleServer.add_query(animal)
    
    while True:
      response = simpleServer.run_query()
      if len(response) != 0:
        print(response)

if __name__ == "__main__":
  Main().run()