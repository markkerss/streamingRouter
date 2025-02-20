from generated import router_pb2_grpc, router_pb2
import json
from google.protobuf.empty_pb2 import Empty
from abc import abstractmethod, ABC 
import time
import grpc
from threading import Lock

class ServerTemplate(ABC, router_pb2_grpc.RouterServicer):
  def __init__(self):
    self.requests = {}
    self.lock = Lock()
    
    routerChannel = grpc.insecure_channel("localhost:50056")
    self.routerStub = router_pb2_grpc.RouterStub(routerChannel)

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

  @abstractmethod
  def add_query(self, chunk) -> str:
    pass

  @abstractmethod
  def run_query(self, chunks) -> str:
    pass