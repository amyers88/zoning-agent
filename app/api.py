import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from app.zoning_rag import build_or_load_vectordb, zoning_qa, get_retriever
from app.extractors import extract_facts
from app.tools import budget_compare, geocode_address, get_zoning_district, get_static_map_url, get_overlays

load_dotenv()
app = FastAPI(title="Nashville Zoning AI")

class ZoningQuery(BaseModel):
    address: str
    question: str

@app.on_event("startup")
def on_startup():
    if not os.path.exists("vectorstore/chroma.sqlite3"):
        build_or_load_vectordb()

@app.post("/zoning/qa")
def zoning_qa_endpoint(payload: ZoningQuery):
    return zoning_qa(f"{payload.address}: {payload.question}")

class DeveloperAnalysisRequest(BaseModel):
    address: str
    proposed_use: Optional[str] = None
    include_variance_analysis: bool = False

@app.post("/zoning/developer-analysis")
def developer_analysis(req: DeveloperAnalysisRequest):
    try:
        coordinates = geocode_address(req.address)
        if not coordinates:
            raise HTTPException(status_code=400, detail="Could not geocode address")
        
        zoning_district = get_zoning_district(coordinates)
        if not zoning_district:
            raise HTTPException(status_code=400, detail="Could not determine zoning district")
        
        query_parts = [
            f"Address: {req.address}",
            f"Zoning District: {zoning_district}",
            "Comprehensive developer analysis including:",
            "- Permitted uses and development standards",
            "- Height, setback, and parking requirements", 
            "- Development process and timeline",
            "- Cost implications and fees",
            "- Development opportunities and risks"
        ]
        
        if req.proposed_use:
            query_parts.append(f"Proposed Use: {req.proposed_use}")
            query_parts.append("- Specific requirements for this use type")
            query_parts.append("- Approval process and timeline")
        
        if req.include_variance_analysis:
            query_parts.append("- Variance potential and process")
            query_parts.append("- Alternative development approaches")
        
        query = " ".join(query_parts)
        
        retriever = get_retriever()
        docs = retriever.get_relevant_documents(query)
        snippets = [d.page_content[:1500] for d in docs[:6]]
        facts = extract_facts(snippets)
        
        from app.prompts import DEVELOPER_SNAPSHOT_TEMPLATE
        from langchain_ollama import OllamaLLM
        
        llm = OllamaLLM(model="llama3.1:8b", temperature=0)
        context = "\n\n".join(snippets)
        
        analysis_prompt = DEVELOPER_SNAPSHOT_TEMPLATE.format(
            address=req.address,
            zoning_context=context
        )
        
        detailed_analysis = llm.invoke(analysis_prompt)
        
        sources = []
        for d in docs[:6]:
            sources.append({
                "source": os.path.basename(str(d.metadata.get("source", "unknown"))),
                "page": d.metadata.get("page"),
                "content_preview": d.page_content[:200] + "..."
            })
        
        return {
            "address": req.address,
            "coordinates": coordinates,
            "zoning_district": zoning_district,
            "facts": facts,
            "detailed_analysis": detailed_analysis,
            "sources": sources,
            "analysis_timestamp": "2025-01-27"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
def ui_home():
    return HTMLResponse(content=open("simple_ui.html").read())

@app.get("/health")
def health():
    return {"status": "ok", "message": "Nashville Zoning AI is running"}
