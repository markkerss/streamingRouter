from client_library.clientLibrary import ClientLibrary

class Main:
  def __init__(self):
    self.list = ["cat", "dog", "giraffe", "elephant", "lemur"]
  
  def run(self):
    simpleServer = ClientLibrary("simple")
    for animal in self.list:
      simpleServer.add_query(animal)

    print(simpleServer.run_query())

if __name__ == "__main__":
  Main().run()