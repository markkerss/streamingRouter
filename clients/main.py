from client_library.clientLibrary import ClientLibrary

class Main:
  def __init__(self):
    self.list = ["cat", "dog", "giraffe", "elephant", "lemur", "tiger", "zebra", "kangaroo", "panda", "hippopotamus"]
    self.list2 = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew", "kiwi", "lemon"]
  
  def run(self):
    simpleServer = ClientLibrary("simple")
    simpleServer2 = ClientLibrary("simple")
    for i in range(4):
      simpleServer.add_query(self.list[i])
      simpleServer2.add_query(self.list2[i])
    print(simpleServer.run_query(self.list[4]))
    print(simpleServer2.run_query(self.list2[4]))
    
    for i in range(5, 8):
      simpleServer.add_query(self.list[i])
      simpleServer2.add_query(self.list2[i])
    print(simpleServer.run_query(self.list[8]))
    print(simpleServer2.run_query(self.list2[8]))
    
    print(simpleServer.run_query(self.list[9]))
    print(simpleServer2.run_query(self.list2[9]))

if __name__ == "__main__":
  Main().run()