from generated import router_pb2_grpc
import grpc
from concurrent import futures
from serverTemplate import ServerTemplate
import requests
import json
import time
import os
from threading import Thread

class ParrotServeServer(ServerTemplate):
    def __init__(self):
        super().__init__()
        # Default to localhost but can be configured
        self.engine_url = "http://localhost:9001"
        self.next_context_id = 1
        
        # Performance tracking
        self.request_times = {}
        self.total_time = 0
        self.total_requests = 0
        self.latencies = []
        
        # Test engine connection
        self._check_engine_connection()

    def _check_engine_connection(self):
        """Verify the engine is running and report its status"""
        try:
            response = requests.post(f"{self.engine_url}/ping")
            if response.ok:
                print(f"✅ Connected to ParrotServe engine at {self.engine_url}")
                print(f"Engine info: {response.json()}")
            else:
                print(f"⚠️ ParrotServe engine responded with status {response.status_code}")
        except Exception as e:
            print(f"❌ Could not connect to ParrotServe engine: {str(e)}")
            print(f"   Make sure you started the engine with: python -m parrot.engine.http_server --config_path engine.json --without_os")

    def add_query(self, chunk):
        # Start timing the request
        request_id = hash(chunk) % 10000000
        self.request_times[request_id] = time.time()
        return chunk
    
    def run_query(self, chunks):
        result = []
        for chunk in chunks:
            request_id = hash(chunk) % 10000000
            start_time = self.request_times.get(request_id, time.time())
            
            try:
                # Create a context ID for this request
                context_id = self.next_context_id
                self.next_context_id += 1
                
                # Use the generate endpoint of ParrotServe engine
                print(f"Sending prompt to engine: '{chunk[:50]}...' (len={len(chunk)})")
                
                response = requests.post(
                    f"{self.engine_url}/generate",
                    json={
                        "prompt": "1" + chunk["shared_prompt"] + "{{input}}{{output}}",
                        "sampling_config": {
                            "max_gen_length": chunk["output_len"],
                            "ignore_tokenizer_eos": True,
                        },
                        "pid": 0,  # Fixed value for standalone mode
                        "tid": 0,  # Fixed value for standalone mode
                        "context_id": context_id,
                        "parent_context_id": -1,
                        "end_flag": True  # Ensure context is properly closed
                    },
                    timeout=60  # Reasonable timeout for benchmarking
                )
                
                if response.ok:
                    response_data = response.json()
                    # Different engine types might return different response formats
                    if "generated_text" in response_data:
                        generated_text = response_data["generated_text"]
                    elif "generated_ids" in response_data and response_data["generated_ids"]:
                        # For engines that return token IDs, we'll format them
                        token_ids = response_data["generated_ids"]
                        generated_text = f"[Generated {len(token_ids)} tokens]"
                    else:
                        generated_text = str(response_data)
                        
                    result.append(generated_text)
                    
                    # Free the context when done
                    try:
                        requests.post(
                            f"{self.engine_url}/free_context",
                            json={"context_id": context_id}
                        )
                    except Exception as e:
                        print(f"Error freeing context {context_id}: {str(e)}")
                else:
                    error_msg = f"Error: {response.status_code} - {response.text}"
                    print(error_msg)
                    result.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                print(error_msg)
                result.append(error_msg)
            
            # Calculate and record request statistics
            end_time = time.time()
            latency = end_time - start_time
            self.latencies.append(latency)
            self.total_time += latency
            self.total_requests += 1
            
            # Print statistics periodically
            if self.total_requests % 10 == 0:
                avg_latency = self.total_time / self.total_requests
                print(f"Request #{self.total_requests} completed in {latency:.2f}s (avg: {avg_latency:.2f}s)")
        
        return result

def serve():
    portNum = "50065"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    router_pb2_grpc.add_RouterServicer_to_server(ParrotServeServer(), server)
    server.add_insecure_port(f"[::]:{portNum}")
    server.start()
    print(f"ParrotServe Benchmark Service Running on port {portNum}")
    print(f"Connected directly to engine without OS layer")
    server.wait_for_termination()

if __name__ == "__main__":
    serve() 