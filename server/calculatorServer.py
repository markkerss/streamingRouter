from generated import router_pb2_grpc
import grpc
from concurrent import futures
from serverTemplate import ServerTemplate
import requests

class CalculatorServer(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="calculator", port=port)
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
  server = CalculatorServer()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()