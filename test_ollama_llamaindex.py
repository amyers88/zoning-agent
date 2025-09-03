import warnings, urllib3
warnings.filterwarnings("ignore", category=urllib3.exceptions.NotOpenSSLWarning)

from llama_index.llms.ollama import Ollama

# Use the model you already have locally; explicit base_url + long timeout
llm = Ollama(
    model="llama3:latest",
    base_url="http://127.0.0.1:11434",
    request_timeout=600.0,
    temperature=0.1
)

resp = llm.complete("Say 'Ollama + LlamaIndex is working.' Keep it short.")
print(resp.text)

