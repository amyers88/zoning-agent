from typing import Dict, Any, List, Optional
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, Field

class ZoningFacts(BaseModel):
    # Basic District Info
    zoning_district: str = Field(..., description="Primary zoning district code")
    district_name: Optional[str] = Field(None, description="Full name of zoning district")
    overlay_districts: Optional[List[str]] = Field(None, description="Any overlay districts")
    
    # Dimensional Standards
    max_height_ft: Optional[float] = Field(None, description="Maximum building height in feet")
    max_stories: Optional[int] = Field(None, description="Maximum number of stories")
    front_setback_ft: Optional[float] = Field(None, description="Front yard setback requirement")
    side_setback_ft: Optional[float] = Field(None, description="Side yard setback requirement")
    rear_setback_ft: Optional[float] = Field(None, description="Rear yard setback requirement")
    lot_coverage_max: Optional[float] = Field(None, description="Maximum lot coverage percentage")
    floor_area_ratio: Optional[float] = Field(None, description="Maximum floor area ratio (FAR)")
    
    # Parking Requirements
    parking_ratio: Optional[str] = Field(None, description="Parking spaces required per unit/use")
    parking_location: Optional[str] = Field(None, description="Where parking can be located")
    
    # Use Information
    permitted_uses: Optional[List[str]] = Field(None, description="Uses permitted by right")
    conditional_uses: Optional[List[str]] = Field(None, description="Uses requiring special permits")
    prohibited_uses: Optional[List[str]] = Field(None, description="Uses not allowed")
    
    # Special Requirements
    design_standards: Optional[List[str]] = Field(None, description="Architectural or design requirements")
    landscaping_requirements: Optional[str] = Field(None, description="Landscaping and green space requirements")
    signage_restrictions: Optional[str] = Field(None, description="Signage limitations")
    
    # Development Process
    required_permits: Optional[List[str]] = Field(None, description="Permits required for development")
    approval_timeline: Optional[str] = Field(None, description="Typical approval timeline")
    public_hearing_required: Optional[bool] = Field(None, description="Whether public hearing is required")
    
    # Cost Factors
    development_fees: Optional[str] = Field(None, description="Estimated development fees")
    infrastructure_requirements: Optional[List[str]] = Field(None, description="Required off-site improvements")
    
    # Opportunities & Risks
    variance_potential: Optional[str] = Field(None, description="Potential for zoning variances")
    rezoning_options: Optional[List[str]] = Field(None, description="Alternative zoning districts to consider")
    development_challenges: Optional[List[str]] = Field(None, description="Potential development obstacles")

def extract_facts(context_snippets: List[str]) -> Dict[str, Any]:
    """
    Given top retrieved text snippets, ask the local model to output a JSON object
    that matches the ZoningFacts schema. If it can’t, return raw text.
    """
    llm = OllamaLLM(model="llama3.1:8b", temperature=0)
    schema = ZoningFacts.model_json_schema()
    newline_join = '\n\n'.join(context_snippets)
    prompt = f"""Extract zoning fields as JSON matching this JSON Schema:
{schema}

Text:
{newline_join}

Return ONLY valid JSON."""
    out = llm.invoke(prompt)
    import json
    try:
        return json.loads(out)
    except Exception:
        return {"raw": out}

