from generated import router_pb2_grpc
import grpc
from concurrent import futures
from serverTemplate import ServerTemplate
from transformers import pipeline

class TranslationServer(ServerTemplate):
  def __init__(self):
    super().__init__()
    self.pipe = pipeline("translation", model="facebook/nllb-200-distilled-600M", src_lang="ita_Latn", tgt_lang="eng_Latn")

  def add_query(self, chunk):
    return chunk
  
  def run_query(self, chunks):
    results = []
    for chunk in chunks:
      results.append(self.pipe(chunk)[0]['translation_text'])
      print(results)
    return results

def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  router_pb2_grpc.add_RouterServicer_to_server(TranslationServer(), server)
  server.add_insecure_port("[::]:50054")
  server.start()
  print("Simple Service Running on port 50054")
  server.wait_for_termination()

if __name__ == "__main__":
  serve()