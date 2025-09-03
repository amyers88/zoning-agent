from typing import Dict, Any, List, Optional
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, Field

class ZoningFacts(BaseModel):
    zoning_district: str = Field(..., description="Primary zoning district code")
    max_height_ft: Optional[float] = None
    front_setback_ft: Optional[float] = None
    side_setback_ft: Optional[float] = None
    rear_setback_ft: Optional[float] = None
    parking_ratio: Optional[str] = None

def extract_facts(context_snippets: List[str]) -> Dict[str, Any]:
    """
    Given top retrieved text snippets, ask the local model to output a JSON object
    that matches the ZoningFacts schema. If it can’t, return raw text.
    """
    llm = OllamaLLM(model="llama3.1:8b", temperature=0)
    schema = ZoningFacts.model_json_schema()
    prompt = f"""Extract zoning fields as JSON matching this JSON Schema:
{schema}

Text:
{'\n\n'.join(context_snippets)}

Return ONLY valid JSON."""
    out = llm.invoke(prompt)
    import json
    try:
        return json.loads(out)
    except Exception:
        return {"raw": out}

