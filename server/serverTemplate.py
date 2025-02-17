from generated import router_pb2_grpc
import json
from google.protobuf.empty_pb2 import Empty
from abc import abstractmethod, ABC 

class ServerTemplate(ABC, router_pb2_grpc.RouterServicer):
  def RouteRequest(self, request_iterator, context):
    for request in request_iterator:
      self.add_query(request)
    return Empty()
  
  def ReceiveResponse(self, request, context):
    job_id = json.loads(request.info)["job_id"]
    return self.run_query(job_id)

  @abstractmethod
  def add_query(self, request):
    pass

  @abstractmethod
  def run_query(self, jobId):
    pass