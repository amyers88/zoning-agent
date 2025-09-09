import os
from typing import Dict, Any
from dotenv import load_dotenv

# Ollama-based LLM + embeddings (local)
from langchain_ollama import OllamaLLM, OllamaEmbeddings

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from app.prompts import ZONING_SYS, ZONING_QA_TEMPLATE

load_dotenv()

DB_DIR = "vectorstore"
DOC_DIR = "data/zoning_pdfs"
TXT_DIR = "zoning_docs"

def build_or_load_vectordb() -> Chroma:
    # Load PDFs
    pdf_loader = DirectoryLoader(DOC_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    pdf_docs = pdf_loader.load()
    # Load local text documents (e.g., Municode extracts)
    try:
        txt_loader = DirectoryLoader(TXT_DIR, glob="**/*.txt", loader_cls=TextLoader)
        txt_docs = txt_loader.load()
    except Exception:
        txt_docs = []
    docs = pdf_docs + txt_docs
    # Chunk
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    # Embed & persist with Ollama embeddings (pull 'nomic-embed-text' in Ollama)
    emb = OllamaEmbeddings(model="nomic-embed-text")
    vs = Chroma.from_documents(
        chunks, emb, collection_name="zoning", persist_directory=DB_DIR
    )
    vs.persist()
    return vs

def get_retriever():
    vs = Chroma(
        collection_name="zoning",
        persist_directory=DB_DIR,
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
    )
    return vs.as_retriever(search_kwargs={"k": 6})

def zoning_qa(question: str) -> Dict[str, Any]:
    retriever = get_retriever()
    llm = OllamaLLM(model="llama3.1:8b", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", ZONING_SYS),
        ("human", ZONING_QA_TEMPLATE)
    ])

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )
    res = chain({"question": question})

    # Clean sources
    sources = []
    for d in res["source_documents"]:
        sources.append({
            "source": os.path.basename(str(d.metadata.get("source","unknown"))),
            "page": d.metadata.get("page")
        })
    return {"answer": res["result"], "sources": sources}
