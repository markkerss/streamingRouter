import grpc
from generated import middleware_pb2, middleware_pb2_grpc
from generated import summarization_pb2, summarization_pb2_grpc
from concurrent import futures

class MiddlewareServicer(middleware_pb2_grpc.MiddlewareServiceServicer):
    def __init__(self):
        self.services = {
            "summarization": summarization_pb2_grpc.SummarizationServiceStub(
                grpc.insecure_channel("localhost:50052")  # Connects to Summarization Service
            )
        }

    def RouteRequest(self, request_iterator, context):
        """Routes only bidirectional streaming requests to backend services."""
        for request in request_iterator:
            print(f"Middleware Routing to Service: {request.service_name}")

            if request.service_name not in self.services:
                yield middleware_pb2.ServiceResponse(output_text="Service not found.")
                continue

            if request.service_name == "summarization":
                summary_request = (summarization_pb2.SummaryRequest(text=request.text) for request in request_iterator)
                for response in self.services["summarization"].SummarizeText(summary_request):
                    yield middleware_pb2.ServiceResponse(output_text=response.summary)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    middleware_pb2_grpc.add_MiddlewareServiceServicer_to_server(MiddlewareServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Middleware Service Running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
