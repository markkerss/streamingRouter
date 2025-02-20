from generated import router_pb2_grpc
import grpc
from concurrent import futures
from serverTemplate import ServerTemplate

class SimpleServer(ServerTemplate):
  def add_query(self, chunk):
    return chunk + " bob!"
  
  def run_query(self, chunks):
    return chunks

def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  router_pb2_grpc.add_RouterServicer_to_server(SimpleServer(), server)
  server.add_insecure_port("[::]:50052")
  server.start()
  print("Simple Service Running on port 50052")
  server.wait_for_termination()

if __name__ == "__main__":
  serve()