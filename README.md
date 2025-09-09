# Nashville Zoning AI Assistant

A comprehensive AI-powered zoning analysis tool specifically designed for commercial real estate developers in Nashville, Tennessee. This assistant provides detailed zoning information, development requirements, and regulatory guidance to help developers make informed decisions about property investments and development projects.

## 🏢 Features

### Core Capabilities
- **Address-Based Zoning Analysis**: Input any Nashville address to get comprehensive zoning information
- **Developer-Focused Reports**: Detailed analysis covering all aspects developers need to know
- **Use-Specific Analysis**: Get requirements for specific development types (retail, office, residential, etc.)
- **Variance Analysis**: Evaluate potential for zoning variances and alternative approaches
- **Cost Implications**: Understand fees, requirements, and timeline impacts

### What Developers Get
- **Zoning District Information**: Primary district, overlays, and district descriptions
- **Permitted Uses**: What can be built by right vs. what requires special approval
- **Development Standards**: Height limits, setbacks, lot coverage, parking requirements
- **Process Guidance**: Required permits, approval timeline, public hearing requirements
- **Risk Assessment**: Potential challenges and development obstacles
- **Opportunity Analysis**: Variance potential, rezoning options, incentive programs

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama installed locally with `llama3.1:8b` and `nomic-embed-text` models
- Nashville Zoning Code 2025 PDF in the `data/zoning_pdfs/` directory
- 100% local stack: no paid APIs, no OpenAI/Anthropic, no external vector DB

### Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd zoning-agent

# Install dependencies
pip install -r requirements.txt

# Start Ollama (if not already running)
ollama serve

# Pull required models (all local)
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### Running the API
```bash
# Start the FastAPI server
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
```

## 📋 API Endpoints

### 1. Comprehensive Developer Analysis
**POST** `/zoning/developer-analysis`

Get a complete zoning analysis for any Nashville property.

```json
{
  "address": "123 Broadway, Nashville, TN",
  "proposed_use": "mixed-use retail and office",
  "include_variance_analysis": true
}
```

**Response includes:**
- Zoning district and coordinates
- Comprehensive development analysis
- Structured facts extraction
- Source citations
- Development opportunities and risks

### 2. Use-Specific Analysis
**POST** `/zoning/use-analysis`

Analyze requirements for a specific use type.

```json
{
  "address": "456 Music Row, Nashville, TN",
  "use_type": "restaurant with outdoor seating"
}
```

### 3. Variance Analysis
**POST** `/zoning/variance-analysis`

Evaluate potential for zoning variances.

```json
{
  "address": "789 Hillsboro Pike, Nashville, TN",
  "zoning_district": "CS",
  "proposed_use": "multi-family residential",
  "variance_types": ["height", "parking", "setback"]
}
```

### 4. Quick Zoning Snapshot
**POST** `/zoning/snapshot`

Get a quick overview of key zoning facts.

```json
{
  "address": "321 Demonbreun St, Nashville, TN",
  "focus": ["height", "setbacks", "parking"]
}
```

## 🗺️ Nashville Zoning Districts

The system recognizes all Nashville zoning districts:

- **RS**: Residential Single Family
- **RM**: Residential Multi-Family  
- **OR**: Office Residential
- **CS**: Commercial Services
- **CL**: Commercial Limited
- **MUL**: Mixed Use Limited
- **MUN**: Mixed Use Neighborhood
- **MUG**: Mixed Use General
- **MUI**: Mixed Use Intensive
- **IR**: Industrial Restricted
- **IG**: Industrial General

## 🛠️ Technical Architecture (Local-Only)

- **RAG System**: ChromaDB (on-disk) with Ollama embeddings (no cloud)
- **LLM**: Ollama (Llama 3.1 8B) fully local inference
- **Document Processing**: Local PDF parsing/chunking
- **Geocoding**: OpenStreetMap Nominatim (free public endpoint) or self-hostable
- **Zoning Lookup**: Metro Nashville ArcGIS Base Zoning layer (MapServer). Set `MNPD_BASE_ZONING_URL` to override.
  - Example: `https://maps.nashville.gov/arcgis/rest/services/Zoning_Landuse/BaseZoning/MapServer`
  - We query the point with `/0/query?geometry=<lon,lat>&geometryType=esriGeometryPoint&inSR=4326...`
- **Overlay Lookup**: Metro Nashville ArcGIS Overlays dataset (Hub/MapServer/FeatureServer). Set `MNPD_OVERLAYS_URL`.
  - Hub dataset: [Zoning Overlay Districts – ArcGIS Hub](https://datanashvillegov-nashville.hub.arcgis.com/datasets/Nashville::zoning-overlay-districts/explore?location=36.155249%2C-86.839651%2C10.15)
  - Configure to the underlying service layer URL, e.g., `.../MapServer/0` or `.../FeatureServer/0`.
- **API**: FastAPI (runs locally)

## 📁 Project Structure

```
zoning-agent/
├── app/
│   ├── api.py              # FastAPI endpoints
│   ├── zoning_rag.py       # RAG system implementation
│   ├── prompts.py          # Developer-focused prompts
│   ├── extractors.py       # Structured fact extraction
│   └── tools.py            # Geocoding and utilities
├── data/
│   └── zoning_pdfs/        # Nashville Zoning Code PDFs
├── vectorstore/            # ChromaDB storage
└── requirements.txt        # Python dependencies
 
### Optional data ingestion helpers
- `fetch_municode_overlays.py` – Municode Title 17.36 overlay text to `zoning_docs/`
- `ingest_historic_resources.py` – MHZC rules, guidelines, and handbook to `zoning_docs/`
- `ingest_urls.py` – generic downloader for UDO program pages, UDO apps, DTC PDF, etc.
```

## 🔧 Configuration

The system is local-only and uses Ollama models. To use different local models, update names in:
- `app/zoning_rag.py` (for embeddings and LLM)
- `app/extractors.py` (for fact extraction)

## 📊 Example Usage

### For a Downtown Nashville Property
```python
import requests

response = requests.post("http://localhost:8000/zoning/developer-analysis", json={
    "address": "100 Broadway, Nashville, TN",
    "proposed_use": "hotel and retail",
    "include_variance_analysis": True
})

analysis = response.json()
print(analysis["detailed_analysis"])
```

### Real Zoning Lookup via ArcGIS
```python
from app.tools import geocode_address, get_zoning_district

coords = geocode_address("100 Broadway, Nashville, TN")
print(coords)
print(get_zoning_district(coords))
```

### For a Suburban Development
```python
response = requests.post("http://localhost:8000/zoning/use-analysis", json={
    "address": "5000 Harding Pike, Nashville, TN", 
    "use_type": "single-family residential subdivision"
})
```

## 🎯 Use Cases

### Commercial Real Estate Developers
- **Site Evaluation**: Quickly assess development potential
- **Due Diligence**: Understand regulatory requirements before acquisition
- **Feasibility Studies**: Evaluate project viability based on zoning constraints
- **Permit Planning**: Understand approval process and timeline

### Real Estate Investors
- **Investment Analysis**: Factor zoning into property valuations
- **Risk Assessment**: Identify potential regulatory obstacles
- **Market Research**: Understand development trends by district

### Architects & Planners
- **Design Constraints**: Understand dimensional and design requirements
- **Code Compliance**: Ensure designs meet zoning standards
- **Variance Planning**: Identify areas where variances might be needed

## 🚧 Current Limitations

- **Zoning Lookup**: Currently uses mock zoning district determination (needs integration with Nashville GIS)
- **Real-time Updates**: Zoning code changes require manual PDF updates
- **Geographic Scope**: Limited to Nashville, TN area

## 🔮 Future Enhancements

- [ ] Integration with Nashville GIS API for real zoning lookups
- [ ] Interactive zoning map visualization
- [ ] Historical zoning change tracking
- [ ] Integration with permit application systems
- [ ] Cost estimation for development fees and requirements
- [ ] Neighborhood compatibility analysis
- [ ] Market trend analysis by zoning district
 - [ ] Deep integration of MHZC guidelines per overlay with auto citation

## 📞 Support

For questions about Nashville zoning regulations, consult the official [Nashville Zoning Code](https://www.nashville.gov/departments/planning/zoning) or contact the Metro Planning Department.

## 📄 License

This project is for educational and development purposes. Always verify zoning information with official sources before making development decisions.

### Official references
- Metro Nashville Base Zoning (ArcGIS MapServer): `MNPD_BASE_ZONING_URL`
- Metro Nashville Zoning Overlay Districts (ArcGIS Hub/MapServer): `MNPD_OVERLAYS_URL` — see [Zoning Overlay Districts – ArcGIS Hub](https://datanashvillegov-nashville.hub.arcgis.com/datasets/Nashville::zoning-overlay-districts/explore?location=36.155249%2C-86.839651%2C10.15)
- Overlay districts legal basis (Municode Title 17.36): [Municode – Title 17.36](https://library.municode.com/tn/metro_government_of_nashville_and_davidson_county/codes/code_of_ordinances?nodeId=CD_TIT17ZO_CH17.36OVDI_ARTIOVDIES)
- Historic Zoning Commission: Rules of Order (Mar 2025): [MHZC Rules PDF](https://www.nashville.gov/sites/default/files/2025-03/MHZC-Rules-of-Order-and-Procedure-2025-03.pdf?ct=1742926155)
- Historic Zoning: Germantown Guidelines (2024): [Germantown Guidelines PDF](https://www.nashville.gov/sites/default/files/2025-06/MHZC-HPZO-Germantown_Design_Guidelines_2024_final.pdf?ct=1749490143)
- Historic Zoning: Handbook (2022): [MHZC Handbook PDF](https://www.nashville.gov/sites/default/files/2022-05/Handbook_revised_2022.pdf?)
- Historic Zoning: Districts & Design Guidelines landing: [MHZC Districts & Design Guidelines](https://www.nashville.gov/departments/planning/historic-zoning-information/districts-and-design-guidelines)
 
#### Civil / Site Compliance
- Stormwater Management Manual (2021, Vols. 1–5): Nashville.gov (Regulations, Procedures, Theory, BMPs, LID; includes waiver/variance links). Ingest via `ingest_urls.py`.
- Tree / Landscape “Tree Ordinance” – Title 17.24 Landscaping, Buffering & Tree (plan compliance): Municode / eLaws. Ingest via `ingest_urls.py`.
- Title 17.28 amendments (2024) – Tree replacement & preservation updates: filetransfer.nashville.gov (use current codified Title 17 for enforceable language). Ingest via `ingest_urls.py`.

Example ingestion commands (replace with the exact URLs you use):
```bash
# Stormwater Manuals (Vols 1–5)
python ingest_urls.py "<Stormwater Manual Vol 1 PDF URL>" \
                     "<Stormwater Manual Vol 2 PDF URL>" \
                     "<Stormwater Manual Vol 3 PDF URL>" \
                     "<Stormwater Manual Vol 4 PDF URL>" \
                     "<Stormwater Manual Vol 5 PDF URL>"

# Tree Ordinance and related updates
python ingest_urls.py "<Municode/eLaws Title 17.24 URL>" \
                     "<Title 17.28 2024 Amendment PDF URL>"

# Rebuild index (optional: delete vectorstore/) then restart API
```
 - Urban Design Overlays (program/info): Nashville Planning – UDO page (add via `ingest_urls.py`)
 - UDO Applications & Fees: filetransfer.nashville.gov link (add via `ingest_urls.py`)
 - Downtown Code (DTC – latest PDF): Nashville.gov DTC download (add via `ingest_urls.py`)
