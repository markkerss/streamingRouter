from generated import router_pb2_grpc, router_pb2
import json
from google.protobuf.empty_pb2 import Empty
from abc import abstractmethod, ABC 
import time
import grpc
from threading import Lock
from concurrent import futures
from config import get_router_address

class ServerTemplate(ABC, router_pb2_grpc.RouterServicer):
  def __init__(self, service_name, port=None):
    """
    Initialize a server with dynamic registration to the router.
    
    Args:
        service_name: Name of the service to register with the router
        port: Optional port number. If None, a port will be dynamically allocated
    """
    self.service_name = service_name
    self.port = port
    self.requests = {}
    self.lock = Lock()
    self.server = None
    self.address = None
    
    # Start the server with dynamic or specified port
    self._start_server()
    
    # Connect to the router using the address from config
    router_address = get_router_address()
    routerChannel = grpc.insecure_channel(f"localhost:{router_address}")
    self.routerStub = router_pb2_grpc.RouterStub(routerChannel)
    
    # Register this server with the router
    self._register_with_router()

  def _start_server(self):
    """Start the server with a dynamically allocated port or specified port"""
    self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    router_pb2_grpc.add_RouterServicer_to_server(self, self.server)
    
    if self.port is None:
      # Dynamically allocate a port
      port = self.server.add_insecure_port("[::]:0")
      self.address = f"localhost:{port}"
    else:
      # Use the specified port
      self.server.add_insecure_port(f"[::]:{self.port}")
      self.address = f"localhost:{self.port}"
      
    self.server.start()
    print(f"{self.service_name} Service running on {self.address}")

  def _register_with_router(self):
    """Register this server with the router"""
    try:
      server_info = router_pb2.ServerInfo(
        service_name=self.service_name,
        address=self.address
      )
      self.routerStub.RegisterServer(server_info)
      print(f"Successfully registered {self.service_name} with router at {self.address}")
    except Exception as e:
      print(f"Failed to register with router: {str(e)}")
      # You might want to retry or exit here depending on your requirements

  def _add_req_to_dict(self, request):
    requestJson = json.loads(request.info)
    requestData = self.add_query(requestJson["data"])
    print(f"Received data in server: {requestData}")
    requestJson["data"] = requestData
    modifiedRequest = router_pb2.Request(info=json.dumps(requestJson))
    print("finished modifying data")
    request_id = requestJson["request_id"]
    if request_id not in self.requests:
      self.requests[request_id] = {}
    self.requests[request_id][requestJson["chunk_id"]] = modifiedRequest
    print("finished admin work on server for requst")

  def RouteRequestChunks(self, request_iterator, context):
    for request in request_iterator:
      self._add_req_to_dict(request)
    return Empty()

  def _block_until_req_avail(self, request_id, requestStore, backoff=1):
    while True:
      with self.lock:
        if request_id in requestStore:
          break
      time.sleep(backoff)

  def RouteLastRequestChunk(self, request, context):
    requestJson = json.loads(request.info)

    # Ensure all chunks have arrived
    chunk_ids = set([i for i in range(requestJson["chunk_id"] + 1)])
    self._block_until_req_avail(requestJson["request_id"], self.requests)
    while True:
      req_dict_chunk_ids = set(self.requests[requestJson["request_id"]].keys())
      if chunk_ids.issubset(req_dict_chunk_ids):
        break
      time.sleep(1)
    print("all chunks have arrived")

    chunksOfData = [json.loads(chunkInfo.info)["data"] for chunkInfo in self.requests[requestJson["request_id"]].values()]
    del self.requests[requestJson["request_id"]]
    newData = self.run_query(chunksOfData)
    response = router_pb2.Response(info=json.dumps({
      "data": newData,
      "request_id": requestJson["request_id"],
      "service_name": requestJson["service_name"],
      "request_ip": requestJson["request_ip"]
    }))

    print("Sending response from server to router")
    self.routerStub.ReceiveResponse(response)

    return Empty()

  def ReceiveResponse(self, request, context):
    context.abort(grpc.StatusCode.UNIMPLEMENTED, "ReceiveResponse is not implemented.")

  def wait_for_termination(self):
    """Wait for the server to terminate"""
    if self.server:
      self.server.wait_for_termination()

  @abstractmethod
  def add_query(self, chunk) -> str:
    pass

  @abstractmethod
  def run_query(self, chunks) -> str:
    pass