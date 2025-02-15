from queue import Queue
from generated import router_pb2, router_pb2_grpc
import grpc
import json
import uuid
from threading import Thread


class ClientLibrary():
  def __init__(self, name):
    self.name = name
    self.q = Queue()
    self.job_id = str(uuid.uuid4())

    channel = grpc.insecure_channel("localhost:50051")
    self.stub = router_pb2_grpc.RouterStub(channel)
  
    def send_to_middleware():
      self.stub.RouteRequest(self._generate_query())
    Thread(target=send_to_middleware, daemon=True).start()
  
  def _generate_query(self):
    while True:
      chunk = self.q.get()
      request = {"data": chunk, "job_id": self.job_id, "service_name": self.name}
      print("sending", chunk, "to middleware")
      yield router_pb2.Request(info=json.dumps(request))

  def add_query(self, chunk):
    self.q.put(chunk)
    print("Putting", chunk)
  
  def run_query(self):
    request = json.dumps({"job_id": self.job_id, "service_name": self.name})
    request = router_pb2.JobInfo(info=request)
    response = self.stub.ReceiveResponse(request)
    jsonResponse = json.loads(response.info)
    return jsonResponse
    