# --- suppress the LibreSSL warning globally for this script ---
import warnings, urllib3
warnings.filterwarnings("ignore", category=urllib3.exceptions.NotOpenSSLWarning)

# --- LlamaIndex + Ollama setup ---
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex

# Point LlamaIndex at your local Ollama server; give a long timeout for first call
Settings.llm = Ollama(
    model="llama3:latest",
    base_url="http://127.0.0.1:11434",
    request_timeout=600.0,
    temperature=0.1,
)

# 🔑 Force embeddings to be local (avoids OpenAI API key problem)
Settings.embed_model = OllamaEmbedding(model_name="llama3:latest")

# --- Load your local zoning documents ---
# Put TXT or PDF files in the 'zoning_docs' folder on your Desktop/zoning-agent
documents = SimpleDirectoryReader(
    "zoning_docs",
    recursive=True,
    required_exts=[".txt"],
    filename_as_id=True,
).load_data()

# --- Build a vector index and ask a starter question ---
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine(similarity_top_k=3)

prompt = "Summarize the key zoning rules in exactly 3 short bullet points."
response = query_engine.query(prompt)

print("\n=== ANSWER ===")
print(str(response))
print("\n(Top-3 similar chunks were searched.)")
