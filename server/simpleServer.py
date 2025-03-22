from serverTemplate import ServerTemplate

class SimpleServer(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="simple", port=port)
    
  def add_query(self, chunk):
    return chunk + " bob!"
  
  def run_query(self, chunks):
    return chunks

def serve():
  server = SimpleServer()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()