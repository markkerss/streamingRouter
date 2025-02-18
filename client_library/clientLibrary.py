from queue import Queue
from generated import router_pb2, router_pb2_grpc
import grpc
import json
import uuid
from threading import Thread, Lock
from concurrent import futures
import time

from google.protobuf.empty_pb2 import Empty

class ClientLibrary(router_pb2_grpc.RouterServicer):
  def __init__(self, service_name):
    self.service_name = service_name
    self.requests = Queue()
    self.responses = {}
    self.currChunkId = 0
    self.requestId = str(uuid.uuid4())
    self.lock = Lock()
    self.ip = "localhost:50050"
  
    self._start_server(self.ip)

    channel = grpc.insecure_channel("localhost:50051")
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
  
  def add_query(self, chunk):
    requestJson = self._create_request_json(chunk, False)
    self.requests.put(json.dumps(requestJson))
    print("Putting", chunk)
  
  def run_query(self, chunk):
    this_req_id = self.requestId
    requestJson = self._create_request_json(chunk, True)
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

  def _start_server(self, ip):
    def serve():
      server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
      router_pb2_grpc.add_RouterServicer_to_server(self, server)
      server.add_insecure_port("[::]:50050")
      server.start()

      print("Client Service Running on port 50050")
      server.wait_for_termination()
    Thread(target=serve, daemon=True).start()