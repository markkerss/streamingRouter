from serverTemplate import ServerTemplate
from transformers import pipeline

class TranslationServer(ServerTemplate):
  def __init__(self, port=None):
    super().__init__(service_name="translation", port=port)
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
  server = TranslationServer()  # Dynamic port
  server.wait_for_termination()

if __name__ == "__main__":
  serve()