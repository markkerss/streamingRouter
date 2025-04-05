import grpc
from generated import router_pb2_grpc
from concurrent import futures
from queue import Queue
from threading import Thread, Lock
import json
from collections import defaultdict
import time
from google.protobuf.empty_pb2 import Empty
from config import ROUTER_IP, ROUTER_PORT
from loadBalancer import LoadBalancer

class Router(router_pb2_grpc.RouterServicer):
    def __init__(self):
      self.serverStubs = {}
      self.clientStubs = {}
      self.loadBalancer = LoadBalancer()
      self.requestQs = defaultdict(Queue)
      self.requestServerAddressMap = {}
      self.responses = {}
      self.lock = Lock()
      print("Router initialized with dynamic server registration")

    def _generate_requests(self, address):
      while True:
        request = self.requestQs[address].get()
        # print(f"Sending this {json.loads(request.info)['data']} to the server!")
        yield request

    def _open_server_pipe(self, address):
      self.serverStubs[address].RouteRequestChunks(self._generate_requests(address))

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
        self.loadBalancer.add_server(service_name, address)
        if address not in self.serverStubs:
          self.serverStubs[address] = router_pb2_grpc.RouterStub(grpc.insecure_channel(address))
          Thread(
            target=self._open_server_pipe,
            args=(address, ),
            daemon=True
          ).start()
        print(f"Registered server '{service_name}' at address '{address}'")
      
      return Empty()
    
    def RemoveServer(self, request, context):
      service_name = request.service_name
      address = request.address
      self.loadBalancer.remove_server(service_name, address)
      with self.lock:
        del self.serverStubs[address]
      return Empty()
    
    def _get_server_address(self, request_id, service_name):
      server_address = None
      if request_id not in self.requestServerAddressMap:
        server_address = self.loadBalancer.get_server(service_name)
        self.requestServerAddressMap[request_id] = server_address
      else:
        server_address = self.requestServerAddressMap[request_id]
      
      return server_address

    def RouteRequestChunks(self, request_iterator, context):
      for request in request_iterator:
        requestJson = json.loads(request.info)
        service_name = requestJson["service_name"]
        request_id = requestJson["request_id"]
        request_address = requestJson["request_address"]
        if request_id not in self.clientStubs:
          self.clientStubs[request_id] = router_pb2_grpc.RouterStub(grpc.insecure_channel(request_address))
        
        server_address = self._get_server_address(request_id, service_name)
        self.loadBalancer.increment_load(service_name, server_address)
        self.requestQs[server_address].put(request)
      return Empty()
        
    def RouteLastRequestChunk(self, request, context):
      requestJson = json.loads(request.info)
      request_id = requestJson["request_id"]
      service_name = requestJson["service_name"]
      request_address = requestJson["request_address"]
      if request_id not in self.clientStubs:
        self.clientStubs[request_id] = router_pb2_grpc.RouterStub(grpc.insecure_channel(request_address))
      
      server_address = self._get_server_address(request_id, service_name)
      self.loadBalancer.increment_load(service_name, server_address)
      print(f"Load after increment: {self.loadBalancer.get_all_server_loads()}")
      self.serverStubs[server_address].RouteLastRequestChunk(request)

      request_id = requestJson["request_id"]
      self._block_until_req_avail(request_id, self.responses)
      self._block_until_req_avail(request_id, self.clientStubs)
      response = self.responses[request_id]
      self.clientStubs[request_id].ReceiveResponse(response)
      del self.responses[request_id]
      del self.clientStubs[request_id]
      del self.requestServerAddressMap[request_id]
      
      return Empty()

    def ReceiveResponse(self, response, context):
      responseJson = json.loads(response.info)
      request_id = responseJson["request_id"]
      service_name = responseJson["service_name"]
      server_address = self.requestServerAddressMap[request_id]
      self.loadBalancer.decrement_load(service_name, server_address)
      print(f"Load after decrement: {self.loadBalancer.get_all_server_loads()}")
      # print("Received response on the middleware", responseJson["data"])
      self.responses[request_id] = response

      return Empty()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = Router()
    router_pb2_grpc.add_RouterServicer_to_server(servicer, server)
    server.add_insecure_port(f"{ROUTER_IP}:{ROUTER_PORT}")
    server.start()

    print(f"Router Service Running on {ROUTER_IP}:{ROUTER_PORT}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
