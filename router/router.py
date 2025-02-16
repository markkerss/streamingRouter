import grpc
from generated import router_pb2, router_pb2_grpc
from concurrent import futures
from queue import Queue
from threading import Thread
import json

from google.protobuf.empty_pb2 import Empty

class Router():
    def __init__(self):
        self.stubs = {
          "simple": router_pb2_grpc.RouterStub(grpc.insecure_channel("localhost:50052"))
        }
        self.requestQs = {}
    
    # def _receive_requests(self, request_iterator):
    #     def _route_request_call(job_id):
    #       self.stubs["simple"].RouteRequest(self._generate_requests(job_id))

    #     start_generate = False
    #     for request in request_iterator:
    #         requestJson = json.loads(request.info)
    #         if not start_generate:
    #           Thread(target=_route_request_call, args=(requestJson.get("job_id"),), daemon=True).start()
    #           start_generate = True
    #         if requestJson["job_id"] not in self.requestQs:
    #           self.requestQs[requestJson["job_id"]] = Queue()
    #         print(f"Receiving this {requestJson['data']} on the middleware")
    #         self.requestQs[requestJson.get("job_id")].put(request)

    def _generate_requests(self, job_id):
        while True:
            request = self.requestQs[job_id].get()
            print(f"Sending this {json.loads(request.info)['data']} to the server!")
            yield request

    def RouteRequest(self, request_iterator, context):
      def _route_request_call(job_id):
          self.stubs["simple"].RouteRequest(self._generate_requests(job_id))
      start_generate = False
      for request in request_iterator:
          requestJson = json.loads(request.info)
          if not start_generate:
            Thread(target=_route_request_call, args=(requestJson.get("job_id"),), daemon=True).start()
            start_generate = True
          if requestJson["job_id"] not in self.requestQs:
            self.requestQs[requestJson["job_id"]] = Queue()
          print(f"Receiving this {requestJson['data']} on the middleware")
          self.requestQs[requestJson.get("job_id")].put(request)
      return Empty()
        
    def ReceiveResponse(self, request, context):
      requestJson = json.loads(request.info)
      stub = self.stubs[requestJson["service_name"]]
      return stub.ReceiveResponse(request)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = Router()
    router_pb2_grpc.add_RouterServicer_to_server(servicer, server)
    server.add_insecure_port("[::]:50051")
    server.start()

    print("Middleware Service Running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
