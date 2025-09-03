import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from app.zoning_rag import build_or_load_vectordb, zoning_qa, get_retriever
from app.extractors import extract_facts
from app.tools import budget_compare

load_dotenv()
app = FastAPI(title="Zoning & Draw Copilot")

class ZoningQuery(BaseModel):
    address: str
    question: str

@app.on_event("startup")
def on_startup():
    # Build index only if missing
    if not os.path.exists("vectorstore/chroma.sqlite3"):
        build_or_load_vectordb()

@app.post("/zoning/qa")
def zoning_qa_endpoint(payload: ZoningQuery):
    res = zoning_qa(f"{payload.address}: {payload.question}")
    return res

class DrawFiles(BaseModel):
    budget_path: str
    draw_path: str

@app.post("/draw/variance")
def draw_variance(files: DrawFiles):
    return {"result": budget_compare({"budget": files.budget_path, "draw": files.draw_path})}

class SnapshotRequest(BaseModel):
    address: str
    focus: List[str] = ["height","setbacks","parking"]

@app.post("/zoning/snapshot")
def zoning_snapshot(req: SnapshotRequest):
    # retrieve top chunks and extract facts
    retriever = get_retriever()
    docs = retriever.get_relevant_documents(f"{req.address}: zoning district, height, setbacks, parking")
    snippets = [d.page_content[:1200] for d in docs[:4]]
    facts = extract_facts(snippets)
    # simple md summary
    md = ["# Zoning Snapshot", f"**Address:** {req.address}", "## Key Facts:"]
    for k,v in facts.items():
        md.append(f"- **{k}**: {v}")
    md.append("\n## Sources:")
    for d in docs[:4]:
        md.append(f"- {os.path.basename(d.metadata.get('source','?'))}, p.{d.metadata.get('page')}")
    return {"facts": facts, "markdown": "\n".join(md)}

