import grpc
from generated import router_pb2_grpc
from concurrent import futures
from queue import Queue
from threading import Thread, Lock
import json
from collections import defaultdict
import time

from google.protobuf.empty_pb2 import Empty

class Router(router_pb2_grpc.RouterServicer):
    def __init__(self):
      self.serverStubs = {
        "simple": router_pb2_grpc.RouterStub(grpc.insecure_channel("localhost:50052"))
      }
      self.clientStubs = {}
      self.serverPipes = set()
      self.requestQs = defaultdict(Queue)
      self.responses = {}
      self.lock = Lock()

    def _generate_requests(self, service_name):
        while True:
          request = self.requestQs[service_name].get()
          print(f"Sending this {json.loads(request.info)['data']} to the server!")
          yield request

    def _run_route_chunks(self, service_name):
      self.serverStubs[service_name].RouteRequestChunks(self._generate_requests(service_name))
      
    def _process_req(self, request):
      requestJson = json.loads(request.info)
      service_name = requestJson["service_name"]
      request_id = requestJson["request_id"]
      with self.lock:
        if service_name not in self.serverPipes:
          Thread(
            target=self._run_route_chunks,
            args=(service_name,),
            daemon=True
          ).start()
          self.serverPipes.add(service_name)
        if request_id not in self.clientStubs:
          self.clientStubs[request_id] = router_pb2_grpc.RouterStub(grpc.insecure_channel(requestJson["request_ip"]))

    def RouteRequestChunks(self, request_iterator, context):
      for request in request_iterator:
        self._process_req(request)   
        service_name = json.loads(request.info)["service_name"]
        self.requestQs[service_name].put(request)
      return Empty()
        
    def RouteLastRequestChunk(self, request, context):
      self._process_req(request)
      requestJson = json.loads(request.info)
      stub = self.serverStubs[requestJson["service_name"]]
      stub.RouteLastRequestChunk(request)
      this_req_id = requestJson["request_id"]
      while True:
        print("Waiting for response on middleware")
        with self.lock:
          if this_req_id in self.responses:
            break
        time.sleep(1)
      response = self.responses[this_req_id]
      del self.responses[this_req_id]
      while True:
        with self.lock:
          if this_req_id in self.clientStubs:
            print("Sent response to client from middleware")
            self.clientStubs[this_req_id].ReceiveResponse(response)
            break
        time.sleep(1)
      return response

    def ReceiveResponse(self, response, context):
      print("Received response on the middleware", response)
      responseJson = json.loads(response.info)
      self.responses[responseJson["request_id"]] = response
      return Empty()

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
