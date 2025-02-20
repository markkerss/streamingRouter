from generated import router_pb2_grpc
import grpc
from concurrent import futures
from serverTemplate import ServerTemplate
from urllib.parse import urlencode
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
        print(response.json(), response)
        result.append(response.json()[1])
    return result

def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  router_pb2_grpc.add_RouterServicer_to_server(CalculatorServer(), server)
  server.add_insecure_port("[::]:50053")
  server.start()
  print("Simple Service Running on port 50053")
  server.wait_for_termination()

if __name__ == "__main__":
  serve()