import grpc
from generated import middleware_pb2, middleware_pb2_grpc
from generated import summarization_pb2, summarization_pb2_grpc
from concurrent import futures
import queue
from threading import Thread 

class MiddlewareServicer(middleware_pb2_grpc.MiddlewareServiceServicer):
    def __init__(self):
        self.requests = queue.Queue()

    def RouteRequest(self, request_iterator, context):
        def receive_requests():
            for request in request_iterator:
                print(f"[Middleware] Receiving from [Client]: {request.text}")
                self.requests.put(request)
        Thread(target=receive_requests, daemon=True).start()

        channel = grpc.insecure_channel("localhost:50052")
        stub = summarization_pb2_grpc.SummarizationServiceStub(channel)
        call = stub.SummarizeText(self.GenerateRequests())

        for response in call:
            print(f"[Middleware] Received from [Server]: {response.text}")
            yield middleware_pb2.ServiceResponse(text=response.text)

    def GenerateRequests(self):
        while True:
            request = self.requests.get()
            print(f"[Middleware] Sending to [Server]: {request.text}")
            yield summarization_pb2.SummaryRequest(text=request.text)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = MiddlewareServicer()
    middleware_pb2_grpc.add_MiddlewareServiceServicer_to_server(servicer, server)
    server.add_insecure_port("[::]:50051")
    server.start()

    print("Middleware Service Running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
