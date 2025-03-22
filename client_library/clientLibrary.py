from queue import Queue
from generated import router_pb2, router_pb2_grpc
import grpc
import json
import uuid
from threading import Thread, Lock, Event
from concurrent import futures
import time
from config import get_router_address

from google.protobuf.empty_pb2 import Empty

class ClientLibrary(router_pb2_grpc.RouterServicer):
  def __init__(self, service_name):
    self.service_name = service_name
    self.requests = Queue()
    self.responses = {}
    self.currChunkId = 0
    self.requestId = str(uuid.uuid4())
    self.lock = Lock()
    self.ip = None

    self._port_assigned = Event()
    self._start_server()
    self._port_assigned.wait()

    # Connect to the router using the address from config
    router_address = get_router_address()
    channel = grpc.insecure_channel(f"localhost:{router_address}")
    self.stub = router_pb2_grpc.RouterStub(channel)
  
    def send_to_middleware():
      self.stub.RouteRequestChunks(self._generate_query())
    Thread(target=send_to_middleware, daemon=True).start()
  
  def _generate_query(self):
    while True:
      with self.lock:
        request = self.requests.get()
        yield router_pb2.Request(info=request)
    
  def _create_request_json(self, chunk, is_final):
    currRequest = {
      "data": chunk, 
      "chunk_id": self.currChunkId, 
      "request_id": self.requestId, 
      "service_name": self.service_name, 
      "is_final_chunk": is_final,
      "request_ip": self.ip
    }
    if is_final:
      self.currChunkId = 0
      self.requestId = str(uuid.uuid4())
    else:
      self.currChunkId += 1
    return currRequest
  
  def add_query(self, chunk, is_final=False):
    requestJson = self._create_request_json(chunk, is_final)
    self.requests.put(json.dumps(requestJson))
    # print("Client putting", chunk)
    return requestJson
  
  def run_query(self, chunk):
    this_req_id = self.requestId
    requestJson = self.add_query(chunk, True)
    self.stub.RouteLastRequestChunk(router_pb2.Request(info=json.dumps(requestJson)))
    while True:
      if this_req_id in self.responses:
        break
      time.sleep(1)
    response = self.responses[this_req_id]
    del self.responses[this_req_id]
    return response
  
  def RouteRequestChunks(self, request_iterator, context):
    context.abort(grpc.StatusCode.UNIMPLEMENTED, "RouteRequestChunks is not implemented.")
  
  def RouteLastRequestChunk(self, request, context):
    context.abort(grpc.StatusCode.UNIMPLEMENTED, "RouteLastRequestChunk is not implemented.")
  
  def ReceiveResponse(self, response, context):
    responseJson = json.loads(response.info)
    self.responses[responseJson["request_id"]] = responseJson["data"]
    return Empty()

  def _start_server(self):
    def serve():
      server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
      router_pb2_grpc.add_RouterServicer_to_server(self, server)
      port = server.add_insecure_port("[::]:0")
      self.ip = f"localhost:{port}"
      self._port_assigned.set()
      server.start()

      print("Client Service Running on port", self.ip)
      server.wait_for_termination()
    Thread(target=serve, daemon=True).start()