from generated import router_pb2_grpc
import grpc
from concurrent import futures
from serverTemplate import ServerTemplate
import requests
import json
from transformers import AutoTokenizer
import random

class ParrotServeServer(ServerTemplate):
    def __init__(self, port=None):
        super().__init__(service_name="parrotserve", port=port)
        # Default to localhost but can be configured
        self.engine_url = "http://localhost:9001"
        self.next_context_id = 1
        self.next_tid = 1
        self.pid = random.randint(0, 1000000)
        self.tokenizer = AutoTokenizer.from_pretrained("lmsys/vicuna-13b-v1.3")
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
        return chunk

    def run_query(self, chunks):
        result = []
        
        for chunk in chunks:
            chunk = json.loads(chunk)

            try:
                # Get shared prompt from the chunk
                shared_prompt = chunk["shared_prompt"]
                diverged_prompt = chunk["diverged_prompt"]
                output_len = chunk["output_len"]
                full_prompt = "1" + shared_prompt + diverged_prompt
                print(f"full_prompt: {full_prompt}\noutput_len: {output_len}\n")
                tokenized_prompt = self.tokenizer.encode(full_prompt, add_special_tokens=False)
                
                # Create a new context ID for each request
                tid = self.next_tid
                context_id = self.next_context_id
                self.next_context_id += 1
                self.next_tid += 1
                
                # First, initialize the context with a Fill operation
                fill_response = requests.post(
                    f"{self.engine_url}/fill",
                    json={
                        "pid": self.pid,
                        "tid": tid,
                        "context_id": context_id,
                        "parent_context_id": -1,
                        "end_flag": False,
                        "token_ids": tokenized_prompt 
                    },
                    timeout=60
                )
                
                if not fill_response.ok:
                    raise Exception(f"Failed to initialize context: {fill_response.text}")
                
                response = requests.post(
                    f"{self.engine_url}/generate_stream",
                    json={
                        "sampling_config": {
                            "max_gen_length": output_len,
                            "ignore_tokenizer_eos": True,
                        },
                        "pid": self.pid,
                        "tid": tid,
                        "context_id": context_id,
                        "parent_context_id": context_id,
                        "end_flag": True
                    },
                    stream=True,
                    timeout=60
                )
                
                # Process the streaming response
                if response.ok:
                    token_ids = []
                    for chunk in response.iter_content(chunk_size=4):
                        if chunk:
                            token_id = int.from_bytes(chunk, byteorder='big')
                            token_ids.append(token_id)
                    
                    # Detokenize the output tokens to get readable text
                    try:
                        generated_text = self.tokenizer.decode(token_ids, skip_special_tokens=True)
                    except Exception as e:
                        print(f"Error detokenizing: {str(e)}")
                        generated_text = f"[Generated {len(token_ids)} tokens]"
                    
                    result.append(generated_text)
                else:
                    error_msg = f"Error: {response.status_code} - {response.text}"
                    print(error_msg)
                    result.append(error_msg)
                
                try:
                    free_response = requests.post(
                        f"{self.engine_url}/free_context",
                        json={
                            "context_id": context_id,
                        },
                        timeout=10
                    )
                    if not free_response.ok:
                        print(f"Warning: Failed to free context {context_id}: {free_response.text}")
                except Exception as e:
                    print(f"Error freeing context: {str(e)}")
            
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                print(error_msg)
                result.append(error_msg)

        return result

def serve():
    server = ParrotServeServer()  # Dynamic port
    server.wait_for_termination()

if __name__ == "__main__":
    serve()