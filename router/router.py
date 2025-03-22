import grpc
from generated import router_pb2_grpc
from concurrent import futures
from queue import Queue
from threading import Thread, Lock
import json
from collections import defaultdict
import time

from google.protobuf.empty_pb2 import Empty
from config import ROUTER_PORT

class Router(router_pb2_grpc.RouterServicer):
    def __init__(self):
      self.serverStubs = {}
      self.clientStubs = {}
      self.serverPipes = set()
      self.requestQs = defaultdict(Queue)
      self.responses = {}
      self.lock = Lock()
      print("Router initialized with dynamic server registration")

    def _generate_requests(self, service_name):
      while True:
        request = self.requestQs[service_name].get()
        print(f"Sending this {json.loads(request.info)['data']} to the server!")
        yield request

    def _open_server_pipe(self, service_name):
      self.serverStubs[service_name].RouteRequestChunks(self._generate_requests(service_name))

    def _process_req(self, request):
      requestJson = json.loads(request.info)
      service_name = requestJson["service_name"]
      request_id = requestJson["request_id"]
      
      with self.lock:
        if service_name not in self.serverStubs:
          print(f"Error: Service '{service_name}' not registered with router")
          return False
          
        if service_name not in self.serverPipes:
          Thread(
            target=self._open_server_pipe,
            args=(service_name,),
            daemon=True
          ).start()
          self.serverPipes.add(service_name)
        if request_id not in self.clientStubs:
          self.clientStubs[request_id] = router_pb2_grpc.RouterStub(grpc.insecure_channel(requestJson["request_ip"]))
      
      return True

    def _block_until_req_avail(self, request_id, requestStore, backoff=1):
      while True:
        with self.lock:
          if request_id in requestStore:
            break
        time.sleep(backoff)

    def RegisterServer(self, request, context):
      """Register a server with the router"""
      service_name = request.service_name
      address = request.address
      
      with self.lock:
        self.serverStubs[service_name] = router_pb2_grpc.RouterStub(grpc.insecure_channel(address))
        print(f"Registered server '{service_name}' at address '{address}'")
      
      return Empty()

    def RouteRequestChunks(self, request_iterator, context):
      for request in request_iterator:
        success = self._process_req(request)
        if not success:
          return Empty()
          
        service_name = json.loads(request.info)["service_name"]
        self.requestQs[service_name].put(request)
      return Empty()
        
    def RouteLastRequestChunk(self, request, context):
      success = self._process_req(request)
      if not success:
        return Empty()
        
      requestJson = json.loads(request.info)
      request_id = requestJson["request_id"]
      stub = self.serverStubs[requestJson["service_name"]]
      stub.RouteLastRequestChunk(request)

      self._block_until_req_avail(request_id, self.responses)
      self._block_until_req_avail(request_id, self.clientStubs)
      response = self.responses[request_id]
      self.clientStubs[request_id].ReceiveResponse(response)
      del self.responses[request_id]
      del self.clientStubs[request_id]
      
      return Empty()

    def ReceiveResponse(self, response, context):
      responseJson = json.loads(response.info)
      print("Received response on the middleware", responseJson["data"])
      self.responses[responseJson["request_id"]] = response
      return Empty()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = Router()
    router_pb2_grpc.add_RouterServicer_to_server(servicer, server)
    server.add_insecure_port(f"[::]:{ROUTER_PORT}")
    server.start()

    print(f"Router Service Running on {ROUTER_PORT}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
