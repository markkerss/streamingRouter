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
      self.requestProcessingQ = Queue()
      self.lastRequestProcessingQ = Queue()
      self.responseProcessingQ = Queue()
      self.requestServerAddressMap = {}

      print("Router initialized with dynamic server registration")

      self.requestProcessingThread = Thread(
        target=self._process_requests,
        daemon=True
      ).start()

      self.responseProcessingThread = Thread(
        target=self._process_responses,      
        daemon=True
      ).start()

    def _generate_requests(self, address):
      while True:
        request = self.requestQs[address].get()
        print(f"Sending this {json.loads(request.info)['data']} to the server!")
        yield request

    def _open_server_pipe(self, address):
      self.serverStubs[address].RouteRequestChunks(self._generate_requests(address))

    def _block_until_req_avail(self, request_id, requestStore, backoff=1):
      while True:
        if request_id in requestStore:
          break
        time.sleep(backoff)

    def RegisterServer(self, request, context):
      """Register a server with the router"""
      service_name = request.service_name
      address = request.address
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
      if address in self.serverStubs:
        del self.serverStubs[address]
      return Empty()
    
    def _get_server_address(self, request_id, service_name):
      if request_id not in self.requestServerAddressMap:
        server_address = self.loadBalancer.get_server(service_name)
        self.requestServerAddressMap[request_id] = server_address
      else:
        server_address = self.requestServerAddressMap[request_id]
      
      return server_address
    
    def _process_requests(self):
      while True:
        request, is_final = self.requestProcessingQ.get()
        requestJson = json.loads(request.info)
        service_name = requestJson["service_name"]
        request_id = requestJson["request_id"]
        request_address = requestJson["request_address"]

        print(f"Processing request {request_id} from {request_address}", is_final)
        
        if request_id not in self.clientStubs:
          self.clientStubs[request_id] = router_pb2_grpc.RouterStub(grpc.insecure_channel(request_address))
        
        server_address = self._get_server_address(request_id, service_name)
        if not is_final:
          self.loadBalancer.increment_load(service_name, server_address)
          self.loadBalancer.print_all_server_loads()
          self.requestQs[server_address].put(request)
          print(f"Sent chunk of request {request_id} to {server_address}")
        else:
          self.serverStubs[server_address].RouteLastRequestChunk(request)
          print(f"Sent final chunk of request {request_id} to {server_address}")
        
    def RouteRequestChunks(self, request_iterator, context):
      for request in request_iterator:
        self.requestProcessingQ.put((request, False))
      return Empty()
        
    def RouteLastRequestChunk(self, request, context):
      self.requestProcessingQ.put((request, True))
      return Empty()
    
    def _process_responses(self):
      while True:
        response = self.responseProcessingQ.get()
        responseJson = json.loads(response.info)
        request_id = responseJson["request_id"]
        service_name = responseJson["service_name"]

        self._block_until_req_avail(request_id, self.clientStubs)
        self._block_until_req_avail(request_id, self.requestServerAddressMap)
        server_address = self.requestServerAddressMap[request_id]

        self.clientStubs[request_id].ReceiveResponse(response)
        del self.clientStubs[request_id]
        del self.requestServerAddressMap[request_id]
        self.loadBalancer.decrement_load(service_name, server_address)
        self.loadBalancer.print_all_server_loads()

    def ReceiveResponse(self, response, context):
      responseJson = json.loads(response.info)
      print("Received response", flush=True)
      self.responseProcessingQ.put(response)
      print(f"Received response for request {responseJson['request_id']}", responseJson["data"], flush=True)
      return Empty()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    servicer = Router()
    router_pb2_grpc.add_RouterServicer_to_server(servicer, server)
    server.add_insecure_port(f"{ROUTER_IP}:{ROUTER_PORT}")
    server.start()

    print(f"Router Service Running on {ROUTER_IP}:{ROUTER_PORT}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
