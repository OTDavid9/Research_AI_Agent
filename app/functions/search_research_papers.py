from venv import logger

import requests
import time
import io
import pdfplumber
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


# -----------------------------
# SAFE REQUEST
# -----------------------------
def safe_request(url, params=None):
    time.sleep(0.5)

    try:
        r = requests.get(url, params=params, timeout=30)

        if r.status_code == 429:
            time.sleep(3)
            return safe_request(url, params)

        r.raise_for_status()
        return r

    except Exception:
        return None


# -----------------------------
# SEMANTIC SCHOLAR CLIENT
# -----------------------------
class SemanticScholarClient:
    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def search(self, query: str, offset: int, limit: int = 10):
        params = {
            "query": query,
            "limit": limit,
            "offset": offset,
            "fields": "title,authors,year,openAccessPdf"
        }

        r = safe_request(self.BASE_URL, params=params)
        if not r:
            return []

        return r.json().get("data", [])


# -----------------------------
# IN-MEMORY PDF EXTRACTION (NO FILES)
# -----------------------------
def extract_pdf_from_url(url: str) -> str:
    try:
        r = requests.get(url, timeout=30)

        if r.status_code != 200:
            return ""

        file_stream = io.BytesIO(r.content)

        text = ""

        with pdfplumber.open(file_stream) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        return text.strip()

    except Exception:
        return ""


# -----------------------------
# MAIN PIPELINE (PARALLEL + MEMORY ONLY)
# -----------------------------
def search_research_papers(query: str, min_results: int = 3)-> List[Dict[str, str]]:

    client = SemanticScholarClient()
    dataset = []
    lock = threading.Lock()

    offset = 0
    attempts = 0
    max_attempts = 20

    print(f"🚀 Target: {min_results} valid papers\n")

    while len(dataset) < min_results and attempts < max_attempts:

        print(f"\n🔍 Batch {attempts+1} (offset {offset})")

        papers = client.search(query, offset=offset, limit=10)

        if not papers:
            offset += 10
            attempts += 1
            continue

        tasks = []
        meta_map = {}

        for i, p in enumerate(papers):
            pdf_url = (p.get("openAccessPdf") or {}).get("url")

            if not pdf_url:
                continue

            tasks.append((i, pdf_url))
            meta_map[i] = {
                "title": p.get("title"),
                "authors": [a["name"] for a in p.get("authors", [])],
                "year": p.get("year")
            }

        # -----------------------------
        # PARALLEL PDF EXTRACTION (IN MEMORY)
        # -----------------------------
        results = []

        def worker(task):
            idx, url = task
            text = extract_pdf_from_url(url)

            if len(text) < 200:
                return None

            return (idx, text)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(worker, t) for t in tasks]

            for f in as_completed(futures):
                r = f.result()
                if r:
                    results.append(r)

        # -----------------------------
        # BUILD DATASET
        # -----------------------------
        with lock:
            for idx, text in results:
                meta = meta_map.get(idx)

                if not meta:
                    continue

                dataset.append({
                    "Title": meta["title"],
                    "Author": ", ".join(meta["authors"]),
                    "Year": meta["year"],
                    "Paper_Content": text
                })

                print(f"✅ Collected ({len(dataset)}/{min_results})")

                if len(dataset) >= min_results:
                    break

        offset += 10
        attempts += 1

    if len(dataset) == 0:
        raise Exception("❌ No valid papers retrieved")
    
    logger.info(f"🎉 Successfully retrieved {dataset} papers for query: '{query}'")

    print(f"\n🎉 Completed: Retrieved {dataset} papers for query: '{query}'")

    return dataset


