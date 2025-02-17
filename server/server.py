from generated import router_pb2_grpc, router_pb2
import json
import grpc
from concurrent import futures
from queue import Queue
from serverTemplate import ServerTemplate

class SimpleServer(ServerTemplate):
  def __init__(self):
    self.jobQs = {}

  def add_query(self, request):
    requestJson = json.loads(request.info)
    if requestJson["job_id"] not in self.jobQs:
      self.jobQs[requestJson["job_id"]] = Queue()
    print(f"Receiving this ${json.loads(request.info)['data']} in the server!")
    self.jobQs[requestJson["job_id"]].put(request)
  
  def run_query(self, jobId):
    result = []
    while True:
      if jobId in self.jobQs:
        break
    while not self.jobQs[jobId].empty():
      data = json.loads(self.jobQs[jobId].get().info)["data"]
      result.append(data)
    return router_pb2.Response(info=json.dumps(result))

def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  router_pb2_grpc.add_RouterServicer_to_server(SimpleServer(), server)
  server.add_insecure_port("[::]:50052")
  server.start()
  print("Summarization Service Running on port 50052")
  server.wait_for_termination()

if __name__ == "__main__":
  serve()