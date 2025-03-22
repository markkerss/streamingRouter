from crewai import LLM
from vllm import LLM as VLLMEngine


class VLLMLLM(LLM):
  def __init__(self, model_name, **kwargs):
    self.model_name = model_name
    self.vllm_engine = VLLMEngine(model=model_name, **kwargs)
  
  def generate(self, prompt, **kwargs):
    sampling_params = kwargs.get("sampling_params", {})
    outputs = self.vllm_engine.generate(prompt, sampling_params)
    return outputs[0].outputs[0].text

  def config_dict(self):
    return {
      "model": self.model_name,
      "type": "vllm"
    }