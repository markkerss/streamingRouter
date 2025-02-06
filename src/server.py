import grpc
from concurrent import futures
from vllm import LLM, SamplingParams
from generated import summarization_pb2, summarization_pb2_grpc
from threading import Thread
from queue import Queue

class SummarizationServicer(summarization_pb2_grpc.SummarizationServiceServicer):
    def __init__(self):
        self.llm = LLM(model="meta-llama/Llama-3.1-8B", gpu_memory_utilization=0.4, max_model_len=40960)
        self.summary = ""
    
    def SummarizeText(self, request_iterator, context):
        requests = Queue()

        def receive_requests():
            for request in request_iterator:
                requests.put(request)
        Thread(target=receive_requests, daemon=True).start() 

        while True:
            request = requests.get()
            print(f"[Server] receiving: {request.text}\n")
            prompt = f"Summarize the following text concisely in 20 words or less: {request.text} {', making it flow with the previous summary:' + self.summary if self.summary else ''}"
            sampling_params = SamplingParams(temperature=0.7, max_tokens=20)
            outputs = self.llm.generate(prompt, sampling_params)

            new_summary = outputs[0].outputs[0].text.strip()
            self.summary += new_summary
            print(f"[Server] sending: {new_summary}\n")
            yield summarization_pb2.SummaryResponse(text=new_summary)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    summarization_pb2_grpc.add_SummarizationServiceServicer_to_server(SummarizationServicer(), server)
    server.add_insecure_port("[::]:50052")
    server.start()
    print("Summarization Service Running on port 50052")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
