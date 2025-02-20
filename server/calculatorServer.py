from generated import router_pb2_grpc
import grpc
from concurrent import futures
from serverTemplate import ServerTemplate
import requests

class CalculatorServer(ServerTemplate):
  def __init__(self):
    super().__init__()
    self.baseUrl = "http://api.mathjs.org/v4/?expr="

  def add_query(self, chunk):
    return chunk
  
  def run_query(self, chunks):
    result = []
    for chunk in chunks:
      print("this chunk", chunk)
      response = requests.get(self.baseUrl, params={"expr":chunk})
      if response.ok:
        result.append(response.json()[1])
    return result

def serve():
  portNum = "50053"
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  router_pb2_grpc.add_RouterServicer_to_server(CalculatorServer(), server)
  server.add_insecure_port(f"[::]:{portNum}")
  server.start()
  print(f"Calculator Service Running on port {portNum}")
  server.wait_for_termination()

if __name__ == "__main__":
  serve()