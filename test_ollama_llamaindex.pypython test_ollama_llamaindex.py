from llama_index.llms.ollama import Ollama

# Use the model you already have locally
llm = Ollama(model="llama3:latest", request_timeout=120.0)

resp = llm.complete("Say 'Ollama + LlamaIndex is working.' Keep it short.")
print(resp.text)
