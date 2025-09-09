#!/usr/bin/env python3
"""
Fetch overlay districts content (Title 17.36) from Municode and save to zoning_docs/.
This helps the local RAG answer overlay legal-basis questions with citations.
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

MUNICODE_URL = (
    "https://library.municode.com/tn/metro_government_of_nashville_and_davidson_county/"
    "codes/code_of_ordinances?nodeId=CD_TIT17ZO_CH17.36OVDI_ARTIOVDIES"
)
OUTPUT_DIR = Path("zoning_docs")
OUTPUT_FILE = OUTPUT_DIR / "overlays_title_17_36.txt"

HEADERS = {
    "User-Agent": "Nashville-Zoning-AI/1.0 (+local)"
}

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Municode renders content dynamically; when static HTML is limited, we still
    # capture visible text in the page to seed the RAG. If needed, this can be
    # replaced with a manual saved export.
    text_parts = []
    for el in soup.find_all(["h1","h2","h3","p","li"]):
        t = el.get_text(strip=True)
        if t:
            text_parts.append(t)
    text = "\n".join(text_parts)
    # Add source tag
    src = f"\n\n[Source: Municode Title 17.36] {MUNICODE_URL}\n"
    return text + src

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        html = fetch_html(MUNICODE_URL)
        text = extract_text(html)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Failed to fetch Municode overlays: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
