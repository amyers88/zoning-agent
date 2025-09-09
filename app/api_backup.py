import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
from app.zoning_rag import build_or_load_vectordb, zoning_qa, get_retriever
from app.extractors import extract_facts
from app.tools import budget_compare, geocode_address, get_zoning_district, get_static_map_url, get_overlays

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

class DeveloperAnalysisRequest(BaseModel):
    address: str
    proposed_use: Optional[str] = None
    include_variance_analysis: bool = False

@app.post("/zoning/developer-analysis")
def developer_analysis(req: DeveloperAnalysisRequest):
    """
    Comprehensive zoning analysis for commercial real estate developers.
    Provides all information needed to evaluate a property for development.
    """
    try:
        # Get coordinates and zoning district
        coordinates = geocode_address(req.address)
        if not coordinates:
            raise HTTPException(status_code=400, detail="Could not geocode address")
        
        zoning_district = get_zoning_district(coordinates)
        if not zoning_district:
            raise HTTPException(status_code=400, detail="Could not determine zoning district")
        
        # Build comprehensive query
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
        
        # Get comprehensive analysis
        retriever = get_retriever()
        docs = retriever.get_relevant_documents(query)
        snippets = [d.page_content[:1500] for d in docs[:6]]
        facts = extract_facts(snippets)
        
        # Generate detailed analysis using the enhanced prompt
        from app.prompts import DEVELOPER_SNAPSHOT_TEMPLATE
        from langchain_ollama import OllamaLLM
        
        llm = OllamaLLM(model="llama3.1:8b", temperature=0)
        context = "\n\n".join(snippets)
        
        analysis_prompt = DEVELOPER_SNAPSHOT_TEMPLATE.format(
            address=req.address,
            zoning_context=context
        )
        
        detailed_analysis = llm.invoke(analysis_prompt)
        
        # Prepare sources
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
            "analysis_timestamp": "2025-01-27"  # You might want to use actual timestamp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

class UseSpecificRequest(BaseModel):
    address: str
    use_type: str
    zoning_district: Optional[str] = None

@app.post("/zoning/use-analysis")
def use_specific_analysis(req: UseSpecificRequest):
    """
    Analyze zoning requirements for a specific use type at an address.
    """
    try:
        # Get zoning district if not provided
        if not req.zoning_district:
            coordinates = geocode_address(req.address)
            if coordinates:
                req.zoning_district = get_zoning_district(coordinates)
        
        if not req.zoning_district:
            raise HTTPException(status_code=400, detail="Could not determine zoning district")
        
        # Build use-specific query
        from app.prompts import USE_SPECIFIC_ANALYSIS
        from langchain_ollama import OllamaLLM
        
        retriever = get_retriever()
        docs = retriever.get_relevant_documents(
            f"{req.use_type} development requirements {req.zoning_district} zoning district"
        )
        snippets = [d.page_content[:1500] for d in docs[:4]]
        
        llm = OllamaLLM(model="llama3.1:8b", temperature=0)
        context = "\n\n".join(snippets)
        
        analysis_prompt = USE_SPECIFIC_ANALYSIS.format(
            address=req.address,
            use_type=req.use_type,
            zoning_district=req.zoning_district
        )
        
        analysis = llm.invoke(analysis_prompt)
        
        sources = []
        for d in docs[:4]:
            sources.append({
                "source": os.path.basename(str(d.metadata.get("source", "unknown"))),
                "page": d.metadata.get("page")
            })
        
        return {
            "address": req.address,
            "use_type": req.use_type,
            "zoning_district": req.zoning_district,
            "analysis": analysis,
            "sources": sources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Use analysis failed: {str(e)}")

class VarianceRequest(BaseModel):
    address: str
    zoning_district: str
    proposed_use: str
    variance_types: List[str]  # e.g., ["height", "setback", "parking"]

@app.post("/zoning/variance-analysis")
def variance_analysis(req: VarianceRequest):
    """
    Analyze potential for zoning variances at a property.
    """
    try:
        from app.prompts import VARIANCE_ANALYSIS
        from langchain_ollama import OllamaLLM
        
        retriever = get_retriever()
        docs = retriever.get_relevant_documents(
            f"zoning variance process {req.zoning_district} {req.proposed_use}"
        )
        snippets = [d.page_content[:1500] for d in docs[:4]]
        
        llm = OllamaLLM(model="llama3.1:8b", temperature=0)
        context = "\n\n".join(snippets)
        
        analysis_prompt = VARIANCE_ANALYSIS.format(
            address=req.address,
            zoning_district=req.zoning_district,
            proposed_use=req.proposed_use
        )
        
        analysis = llm.invoke(analysis_prompt)
        
        sources = []
        for d in docs[:4]:
            sources.append({
                "source": os.path.basename(str(d.metadata.get("source", "unknown"))),
                "page": d.metadata.get("page")
            })
        
        return {
            "address": req.address,
            "zoning_district": req.zoning_district,
            "proposed_use": req.proposed_use,
            "variance_types": req.variance_types,
            "analysis": analysis,
            "sources": sources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Variance analysis failed: {str(e)}")

class MapRequest(BaseModel):
    address: str
    zoom: int = 15
    width: int = 600
    height: int = 400

@app.post("/map/static")
def static_map(req: MapRequest):
    try:
        coords = geocode_address(req.address)
        if not coords:
            raise HTTPException(status_code=400, detail="Could not geocode address")
        url = get_static_map_url(coords, zoom=req.zoom, width=req.width, height=req.height)
        return {"address": req.address, "coordinates": coords, "map_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Map generation failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
def ui_home():
    return HTMLResponse(content=open("simple_ui.html").read())
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Nashville Zoning AI</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #0b1320; color: #e8eef9; }
      .container { max-width: 960px; margin: 0 auto; padding: 24px; }
      .card { background: #111a2e; border: 1px solid #233253; border-radius: 12px; padding: 20px; box-shadow: 0 10px 24px rgba(0,0,0,0.35); }
      h1 { font-size: 22px; margin: 0 0 16px; }
      label { display: block; font-size: 14px; margin-bottom: 6px; color: #a8b3cf; }
      input, select { width: 100%; padding: 12px 14px; border-radius: 8px; border: 1px solid #2a3a60; background: #0f1627; color: #e8eef9; }
      .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
      button { background: #3b82f6; color: white; border: none; padding: 12px 16px; border-radius: 8px; cursor: pointer; font-weight: 600; }
      button:disabled { opacity: .6; cursor: not-allowed; }
      .mt { margin-top: 12px; }
      .mt-lg { margin-top: 20px; }
      .tag { display: inline-block; background: #1b2744; border: 1px solid #2a3a60; color: #b8c3dc; border-radius: 100px; padding: 2px 10px; font-size: 12px; margin-right: 6px; }
      .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
      .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; white-space: pre-wrap; }
      .muted { color: #9aa7c7; font-size: 13px; }
      .sources li { margin-bottom: 6px; }
      .footer { text-align: center; color: #7f8db2; font-size: 12px; margin-top: 20px; }
    </style>
  </head>
  <body>
    <div class=\"container\">
      <div class=\"card\">
        <h1>🏙️ Nashville Zoning AI</h1>
        <label for=\"address\">Address</label>
        <input id=\"address\" placeholder=\"e.g., 100 Broadway, Nashville, TN\" />
        <div class=\"row mt\">
          <div>
            <label for=\"use\">Proposed use (optional)</label>
            <input id=\"use\" placeholder=\"e.g., mixed-use retail and office\" />
          </div>
          <div>
            <label for=\"variance\">Include variance analysis</label>
            <select id=\"variance\"><option value=\"false\">No</option><option value=\"true\">Yes</option></select>
          </div>
        </div>
        <button id=\"go\" class=\"mt-lg\">Analyze</button>
        <div id=\"status\" class=\"mt muted\"></div>
      </div>

      <div id=\"results\" class=\"grid mt-lg\" style=\"display:none;\">
        <div class=\"card\">
          <h1>📋 Developer Analysis</h1>
          <div id=\"summary\" class=\"mono\"></div>
          <div class=\"mt\">
            <div class=\"tag\" id=\"district\"></div>
            <div class=\"tag\" id=\"coords\"></div>
          </div>
          <div class=\"mt\">Facts (parsed):
            <div id=\"facts\" class=\"mono mt\"></div>
          </div>
          <div class=\"mt\">Sources:
            <ul id=\"sources\" class=\"sources\"></ul>
          </div>
        </div>
        <div class=\"card\">
          <h1>🗺️ Map</h1>
          <img id=\"mapimg\" alt=\"map\" style=\"width:100%\; border-radius: 8px; border:1px solid #233253;\" />
        </div>
      </div>

      <div class=\"footer\">Runs locally on Ollama + Chroma. Nashville-specific.</div>
    </div>
    <script>
      const $ = (id) => document.getElementById(id);
      const go = $("go");
      const statusEl = $("status");
      const results = $("results");
      const district = $("district");
      const coords = $("coords");
      const summary = $("summary");
      const facts = $("facts");
      const sources = $("sources");
      const mapimg = $("mapimg");

      async function analyze() {
        const address = $("address").value.trim();
        const proposed = $("use").value.trim();
        const variance = $("variance").value === 'true';
        if (!address) { statusEl.textContent = 'Enter an address.'; return; }
        go.disabled = true; statusEl.textContent = 'Analyzing…'; results.style.display = 'none';
        try {
          const payload = { address, include_variance_analysis: variance };
          if (proposed) payload.proposed_use = proposed;
          const resp = await fetch('/zoning/developer-analysis', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
          });
          if (!resp.ok) throw new Error(await resp.text());
          const data = await resp.json();

          // Fill UI
          district.textContent = `Zoning: ${data.zoning_district || 'Unknown'}`;
          coords.textContent = data.coordinates ? `Lat,Lng: ${data.coordinates[0].toFixed(5)}, ${data.coordinates[1].toFixed(5)}` : 'No coordinates';
          summary.textContent = data.detailed_analysis || '(No analysis)';
          facts.textContent = JSON.stringify(data.facts, null, 2);
          sources.innerHTML = '';
          (data.sources || []).forEach(s => {
            const li = document.createElement('li');
            li.textContent = `${s.source}${s.page !== undefined ? ", p."+s.page : ''}`;
            sources.appendChild(li);
          });
          // Map
          if (data.coordinates) {
            const m = await fetch('/map/static', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ address })});
            const mj = await m.json();
            mapimg.src = mj.map_url;
          }
          results.style.display = 'grid';
          statusEl.textContent = '';
        } catch (e) {
          statusEl.textContent = 'Error: ' + e.message;
        } finally {
          go.disabled = false;
        }
      }

      go.addEventListener('click', analyze);
      document.addEventListener('keydown', (e) => { if (e.key === 'Enter') analyze(); });
    </script>
  </body>
 </html>
    """
    return HTMLResponse(content=html)

class EnvelopeCalcRequest(BaseModel):
    address: str
    lot_width_ft: float = Field(..., gt=0)
    lot_depth_ft: float = Field(..., gt=0)
    proposed_uses: Optional[List[str]] = None

@app.post("/zoning/envelope-calc")
def zoning_envelope_calc(req: EnvelopeCalcRequest):
    """
    Compute a conservative building envelope from zoning facts and lot dimensions.
    Returns setbacks, buildable footprint, coverage/FAR caps, and height caps.
    """
    try:
        lot_area = req.lot_width_ft * req.lot_depth_ft
        retriever = get_retriever()
        # Retrieve facts relevant to dimensional standards
        docs = retriever.get_relevant_documents(
            f"{req.address}: zoning district, height, setbacks, lot coverage, FAR, parking"
        )
        snippets = [d.page_content[:1200] for d in docs[:5]]
        facts = extract_facts(snippets)

        def num(value):
            try:
                if value is None:
                    return None
                if isinstance(value, (int, float)):
                    return float(value)
                # strip non-numeric except dot
                import re
                m = re.findall(r"[0-9]+(?:\.[0-9]+)?", str(value))
                return float(m[0]) if m else None
            except Exception:
                return None

        # Pull dimensional values
        front = num(facts.get("front_setback_ft")) or 0.0
        side = num(facts.get("side_setback_ft")) or 0.0
        rear = num(facts.get("rear_setback_ft")) or 0.0
        max_height_ft = num(facts.get("max_height_ft"))
        max_stories = num(facts.get("max_stories"))
        lot_coverage_max = num(facts.get("lot_coverage_max"))
        if lot_coverage_max and lot_coverage_max > 1.5:
            # assume percentages provided like 60 -> 0.60
            lot_coverage_max = lot_coverage_max / 100.0
        far = num(facts.get("floor_area_ratio"))

        buildable_width = max(req.lot_width_ft - 2 * side, 0)
        buildable_depth = max(req.lot_depth_ft - (front + rear), 0)
        geometric_footprint = max(buildable_width * buildable_depth, 0)
        coverage_cap = lot_area * lot_coverage_max if lot_coverage_max else None
        max_footprint = min(geometric_footprint, coverage_cap) if coverage_cap else geometric_footprint
        max_floor_area_by_far = (far * lot_area) if far else None

        # crude story estimate if height is known (12 ft per story typical)
        est_max_stories_from_height = int(max_height_ft // 12) if max_height_ft else None

        sources = []
        for d in docs[:5]:
            sources.append({
                "source": os.path.basename(str(d.metadata.get("source", "unknown"))),
                "page": d.metadata.get("page")
            })

        return {
            "address": req.address,
            "lot": {
                "width_ft": req.lot_width_ft,
                "depth_ft": req.lot_depth_ft,
                "area_sqft": lot_area
            },
            "setbacks_ft": {"front": front, "side": side, "rear": rear},
            "buildable_area_sqft": {
                "geometric_footprint": geometric_footprint,
                "coverage_cap": coverage_cap,
                "max_footprint": max_footprint
            },
            "intensity_caps": {
                "floor_area_ratio": far,
                "max_floor_area_by_far": max_floor_area_by_far,
                "lot_coverage_max": lot_coverage_max
            },
            "height_caps": {
                "max_height_ft": max_height_ft,
                "max_stories": max_stories,
                "est_max_stories_from_height": est_max_stories_from_height
            },
            "facts": facts,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Envelope calc failed: {str(e)}")

class GoNoGoRequest(BaseModel):
    address: str
    proposed_use: str
    lot_width_ft: Optional[float] = None
    lot_depth_ft: Optional[float] = None

@app.post("/zoning/go-no-go")
def go_no_go(req: GoNoGoRequest):
    """
    Quick feasibility screen with a Go / Caution / No-Go rating and rationale.
    """
    try:
        retriever = get_retriever()
        docs = retriever.get_relevant_documents(
            f"{req.address}: permitted uses, conditional uses, prohibited uses, setbacks, parking"
        )
        snippets = [d.page_content[:1200] for d in docs[:5]]
        facts = extract_facts(snippets)

        uses_prohibited = [u.lower() for u in (facts.get("prohibited_uses") or [])]
        uses_by_right = [u.lower() for u in (facts.get("permitted_uses") or [])]
        uses_conditional = [u.lower() for u in (facts.get("conditional_uses") or [])]

        pu = req.proposed_use.lower()
        rating = "Caution"
        reasons: List[str] = []

        if any(pu in u for u in uses_prohibited):
            rating = "No-Go"
            reasons.append("Proposed use appears prohibited in district")
        elif any(pu in u for u in uses_by_right):
            rating = "Go"
            reasons.append("Proposed use appears permitted by right")
        elif any(pu in u for u in uses_conditional):
            rating = "Caution"
            reasons.append("Proposed use likely requires special/conditional approval")
        else:
            reasons.append("Use permission unclear from code snippets")

        # simple dimensional sanity check if lot dims provided
        front = facts.get("front_setback_ft")
        side = facts.get("side_setback_ft")
        rear = facts.get("rear_setback_ft")
        def n(x):
            try:
                return float(x)
            except Exception:
                return None
        if req.lot_width_ft and req.lot_depth_ft and (n(side) is not None) and (n(front) is not None) and (n(rear) is not None):
            bw = req.lot_width_ft - 2 * n(side)
            bd = req.lot_depth_ft - (n(front) + n(rear))
            if bw <= 0 or bd <= 0:
                rating = "No-Go"
                reasons.append("Setbacks consume lot; no buildable footprint")

        sources = []
        for d in docs[:5]:
            sources.append({
                "source": os.path.basename(str(d.metadata.get("source", "unknown"))),
                "page": d.metadata.get("page")
            })

        return {
            "address": req.address,
            "proposed_use": req.proposed_use,
            "rating": rating,
            "reasons": reasons,
            "facts": facts,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Go/No-Go failed: {str(e)}")

class OverlaySummaryRequest(BaseModel):
    address: str

@app.post("/zoning/overlays")
def overlay_summaries(req: OverlaySummaryRequest):
    """
    Summarize common Nashville overlays and likely implications. GIS overlay lookup
    requires integration; this returns a best-effort summary with citations.
    """
    try:
        # Determine overlays from GIS
        coords = geocode_address(req.address)
        overlays = get_overlays(coords) if coords else []

        # Create a compact summary using model with overlays context
        retriever = get_retriever()
        docs = retriever.get_relevant_documents(
            "Nashville overlay districts Urban Design Overlay Historic Overlay floodplain TOD Neighborhood Conservation standards"
        )
        snippets = [d.page_content[:1000] for d in docs[:4]]
        from langchain_ollama import OllamaLLM
        llm = OllamaLLM(model="llama3.1:8b", temperature=0)
        overlay_names = []
        for attrs in overlays:
            # Try common name/code fields
            name = attrs.get("DIST_NAME") or attrs.get("OVERLAY") or attrs.get("NAME") or attrs.get("CODE")
            if name:
                overlay_names.append(str(name))
        prompt = (
            "Summarize the implications of these Nashville overlay districts for development: "
            + ", ".join(overlay_names or ["(none detected)"]) + ". "
            "Focus on approvals, design standards, and common conditions. Keep concise with citations when present.\n\n"
            "Context:\n" + "\n\n".join(snippets)
        )
        summary = llm.invoke(prompt)

        sources = []
        for d in docs[:4]:
            sources.append({
                "source": os.path.basename(str(d.metadata.get("source", "unknown"))),
                "page": d.metadata.get("page")
            })
        return {"address": req.address, "detected_overlays": overlays, "summary": summary, "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Overlay summary failed: {str(e)}")

