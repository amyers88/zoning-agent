#!/usr/bin/env python3
"""
Generic URL ingestor: downloads PDFs or stores HTML text snapshots into zoning_docs/.
Use for UDO program pages, UDO application PDFs, Downtown Code PDF, etc.
"""

import os
import sys
from pathlib import Path
import mimetypes
import requests
from bs4 import BeautifulSoup

OUT_DIR = Path("zoning_docs")
OUT_DIR.mkdir(parents=True, exist_ok=True)
HEADERS = {"User-Agent": "Nashville-Zoning-AI/1.0 (+local)"}


def snapshot_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    parts = []
    for el in soup.find_all(["h1","h2","h3","p","li","a","th","td"]):
        t = el.get_text(" ", strip=True)
        if t:
            parts.append(t)
    text = "\n".join(parts)
    text += f"\n\n[Source] {url}\n"
    return text


def save_url(url: str, filename: str = None):
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    content_type = r.headers.get("Content-Type", "")
    if not filename:
        # derive from URL
        base = url.split("?")[0].rstrip("/").split("/")[-1] or "download"
        filename = base
    dest = OUT_DIR / filename

    if "pdf" in content_type.lower() or filename.lower().endswith(".pdf"):
        dest = dest if dest.suffix == ".pdf" else dest.with_suffix(".pdf")
        dest.write_bytes(r.content)
        print(f"Saved PDF: {dest}")
    else:
        # store text snapshot
        text = snapshot_html(url)
        dest = dest if dest.suffix == ".txt" else dest.with_suffix(".txt")
        dest.write_text(text, encoding="utf-8")
        print(f"Saved HTML snapshot: {dest}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_urls.py <url1> [<url2> ...]")
        sys.exit(1)
    for url in sys.argv[1:]:
        try:
            save_url(url)
        except Exception as e:
            print(f"Failed to ingest {url}: {e}")
            continue

if __name__ == "__main__":
    main()
