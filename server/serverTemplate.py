from generated import router_pb2_grpc, router_pb2
import json
from google.protobuf.empty_pb2 import Empty
from abc import abstractmethod, ABC 
import time
import grpc
from threading import Lock
from concurrent import futures
from config import ROUTER_PORT, ROUTER_IP
from queue import Queue
from threading import Thread, Lock, Event


class ServerTemplate(ABC, router_pb2_grpc.RouterServicer):
  def __init__(self, service_name, port=None, ip="localhost"):
    """
    Initialize a server with dynamic registration to the router.
    
    Args:
        service_name: Name of the service to register with the router
        port: Optional port number. If None, a port will be dynamically allocated
    """
    self.service_name = service_name
    self.port = port
    self.ip = ip
    self.addQueryQueue = Queue()
    self.runQueryQueue = Queue()
    self.requests = {}
    self.server = None
    self.address = None
    
    
    # Start the server with dynamic or specified port
    self._start_server()
    
    # Connect to the router using the address from config
    routerChannel = grpc.insecure_channel(f"{ROUTER_IP}:{ROUTER_PORT}")
    self.routerStub = router_pb2_grpc.RouterStub(routerChannel)
    
    self.addQueryThread = Thread(
      target=self._process_add_queries,
      daemon=True
    ).start()

    self.runQueryThread = Thread(
      target=self._process_run_queries,      
      daemon=True
    ).start()
    
    # Register this server with the router
    self._register_with_router()

  def _start_server(self):
    """Start the server with a dynamically allocated port or specified port"""
    self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    router_pb2_grpc.add_RouterServicer_to_server(self, self.server)
    
    if self.port is None:
      self.port = self.server.add_insecure_port("[::]:0")
    else:
      self.server.add_insecure_port(f"{self.ip}:{self.port}")
    self.address = f"{self.ip}:{self.port}"

    self.server.start()

  def _register_with_router(self):
    """Register this server with the router"""
    try:
      server_info = router_pb2.ServerInfo(
        service_name=self.service_name,
        address=self.address
      )
      self.routerStub.RegisterServer(server_info)
      # print(f"Successfully registered {self.service_name} with router at {self.address}")
    except Exception as e:
      print(f"Failed to register with router: {str(e)}")
      # You might want to retry or exit here depending on your requirements

  def _process_add_queries(self):
    while True:
      request = self.addQueryQueue.get()
      requestJson = json.loads(request.info)
      requestData = self.add_query(requestJson["data"])
      print(f"Received data in server: {requestData}")

      requestJson["data"] = requestData
      modifiedRequest = router_pb2.Request(info=json.dumps(requestJson))
      # print("finished modifying data")
      request_id = requestJson["request_id"]
      if request_id not in self.requests:
        self.requests[request_id] = {}
      self.requests[request_id][requestJson["chunk_id"]] = modifiedRequest
    # print("finished admin work on server for request", request_id)

  def RouteRequestChunks(self, request_iterator, context):
    for request in request_iterator:
      self.addQueryQueue.put(request)
      print("putting request for add query")
    return Empty()

  def _block_until_req_avail(self, request_id, requestStore, backoff=1):
    while True:
      if request_id in requestStore:
        break
      time.sleep(backoff)
  
  def _get_all_chunks(self, requestJson):
    chunk_ids = set([i for i in range(requestJson["chunk_id"] + 1)])
    self._block_until_req_avail(requestJson["request_id"], self.requests)
    while True:
      print("waiting for chunks")
      req_dict_chunk_ids = set(self.requests[requestJson["request_id"]].keys())
      if chunk_ids.issubset(req_dict_chunk_ids):
        break
      time.sleep(1)
    print("all chunks have arrived")

    all_chunks = [json.loads(chunkInfo.info)["data"] for chunkInfo in self.requests[requestJson["request_id"]].values()]
    return all_chunks

  def _process_run_queries(self):
    while True:
      print(self.runQueryQueue.qsize())
      request = self.runQueryQueue.get()
      requestJson = json.loads(request.info)
      print("processing run query for request", requestJson["request_id"])

      chunksOfData = self._get_all_chunks(requestJson)
      newData = self.run_query(chunksOfData)
      response = router_pb2.Response(info=json.dumps({
        "data": newData,
        "request_id": requestJson["request_id"],
        "service_name": requestJson["service_name"],
        "request_address": requestJson["request_address"]
      }))

      print("SENDING...")
      self.routerStub.ReceiveResponse(response)
      print("Sent response from server to router", response)

      del self.requests[requestJson["request_id"]]
      


  def RouteLastRequestChunk(self, request, context):
    self.runQueryQueue.put(request)
    print("putting request for runQuery")
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