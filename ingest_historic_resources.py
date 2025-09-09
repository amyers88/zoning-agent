#!/usr/bin/env python3
"""
Download key Historic Zoning (MHZC) resources into zoning_docs/ for local RAG ingestion.
Resources:
- MHZC Rules of Order and Procedure (2025-03)
- Germantown Historic Preservation Zoning Overlay Design Guidelines (2024)
- MHZC Handbook (revised 2022)
- Districts & Design Guidelines landing page (HTML snapshot text)
"""

import os
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup

OUT_DIR = Path("zoning_docs")
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESOURCES = [
    {
        "url": "https://www.nashville.gov/sites/default/files/2025-03/MHZC-Rules-of-Order-and-Procedure-2025-03.pdf?ct=1742926155",
        "filename": "mhzc_rules_of_order_2025_03.pdf"
    },
    {
        "url": "https://www.nashville.gov/sites/default/files/2025-06/MHZC-HPZO-Germantown_Design_Guidelines_2024_final.pdf?ct=1749490143",
        "filename": "mhzc_germantown_design_guidelines_2024.pdf"
    },
    {
        "url": "https://www.nashville.gov/sites/default/files/2022-05/Handbook_revised_2022.pdf?",
        "filename": "mhzc_handbook_2022.pdf"
    },
]

LANDING_PAGE = {
    "url": "https://www.nashville.gov/departments/planning/historic-zoning-information/districts-and-design-guidelines",
    "filename": "mhzc_districts_and_design_guidelines.txt"
}

HEADERS = {"User-Agent": "Nashville-Zoning-AI/1.0 (+local)"}


def download_binary(url: str, dest: Path):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    dest.write_bytes(r.content)


def fetch_text_snapshot(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    parts = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li", "a"]):
        t = el.get_text(" ", strip=True)
        if t:
            parts.append(t)
    text = "\n".join(parts)
    text += f"\n\n[Source] {url}\n"
    return text


def main():
    try:
        for res in RESOURCES:
            dest = OUT_DIR / res["filename"]
            print(f"Downloading {res['url']} -> {dest}")
            download_binary(res["url"], dest)
        # Landing page snapshot
        text = fetch_text_snapshot(LANDING_PAGE["url"])
        (OUT_DIR / LANDING_PAGE["filename"]).write_text(text, encoding="utf-8")
        print("Done. Files stored under zoning_docs/.")
        print("Rebuild the index if needed (delete vectorstore/ then start the server).")
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
