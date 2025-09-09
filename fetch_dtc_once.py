# fetch_dtc_once.py
# Download and read Nashville's Downtown Code PDF using PyMuPDF only

import hashlib, pathlib, sys
import requests
import json


# Official Downtown Code PDF (June 2025)
DTC_PDF_URL = "https://www.nashville.gov/sites/default/files/2025-06/Downtown-Code-250520.pdf?ct=1749150062"

CACHE_DIR = pathlib.Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cache_path(url: str) -> pathlib.Path:
    h = hashlib.sha256(url.encode()).hexdigest()[:32]
    return CACHE_DIR / f"{h}.pdf"

def fetch(url: str) -> bytes:
    p = cache_path(url)
    if p.exists():
        return p.read_bytes()
    s = requests.Session()
    s.headers.update({"User-Agent": "ZoningAgent/0.1"})
    r = s.get(url, timeout=45)
    r.raise_for_status()
    p.write_bytes(r.content)
    return r.content

def extract_pdf_text_pymupdf(raw: bytes) -> str:
    import fitz  # PyMuPDF
    text_parts = []
    with fitz.open(stream=raw, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())  # extract page text
    return "\n".join(text_parts)

def sectionize(text: str) -> dict:
    buckets = {"height": [], "uses": [], "parking": []}
    for line in text.splitlines():
        low = line.lower()
        if "height" in low or "stories" in low or "maximum height" in low:
            buckets["height"].append(line.strip())
        if "permitted use" in low or "use table" in low or "uses" in low:
            buckets["uses"].append(line.strip())
        if "parking" in low or "stall" in low:
            buckets["parking"].append(line.strip())
    return {k: v[:20] for k, v in buckets.items() if v}

def main():
    print("Downloading Downtown Code PDF…")
    raw = fetch(DTC_PDF_URL)
    print(f"Fetched {len(raw)} bytes. Extracting text with PyMuPDF…")
    text = extract_pdf_text_pymupdf(raw)
    if not text.strip():
        print("Could not extract text. The PDF may be image-based (needs OCR).")
        sys.exit(1)
    print(f"Extracted {len(text)} characters.\n")

    buckets = sectionize(text)
    if not buckets:
        print("No obvious lines for height/uses/parking found. We can adjust keywords next.")
        sys.exit(0)
    payload = {
        "address": "100 Broadway, Nashville, TN",
        "district": "DTC",
        "sections": buckets,
        "sources": [
            {"name": "Downtown Code (official PDF)", "url": DTC_PDF_URL, "type": "pdf"}
        ]
    }
    (CACHE_DIR / "last_fetch.json").write_text(json.dumps(payload, indent=2))
    print(f"Saved JSON to {CACHE_DIR / 'last_fetch.json'}")

    print("=== SAMPLE LINES FROM THE PDF ===")
    for k, lines in buckets.items():
        print(f"\n[{k.upper()}]")
        for L in lines:
            print(" •", L)

if __name__ == "__main__":
    main()
