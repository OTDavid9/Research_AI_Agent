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
def build_dataset_parallel(query: str, min_results: int = 5):

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

        with ThreadPoolExecutor(max_workers=5) as executor:
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

    return dataset


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":

    query = "Fraud Detection Banking Artificial Intelligence"

    results = build_dataset_parallel(query, min_results=2)

    import json
    print("\n\n================ FINAL OUTPUT ================\n")
    print(json.dumps(results, indent=2))
# import requests
# import time
# import pdfplumber
# from typing import List, Dict
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import threading


# # -----------------------------
# # SAFE REQUEST
# # -----------------------------
# def safe_request(url, params=None):
#     time.sleep(0.5)  # faster throttle (safe for S2 API)

#     try:
#         r = requests.get(url, params=params, timeout=30)

#         if r.status_code == 429:
#             time.sleep(3)
#             return safe_request(url, params)

#         r.raise_for_status()
#         return r

#     except Exception:
#         return None


# # -----------------------------
# # SEMANTIC SCHOLAR CLIENT
# # -----------------------------
# class SemanticScholarClient:
#     BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

#     def search(self, query: str, offset: int, limit: int = 10):
#         params = {
#             "query": query,
#             "limit": limit,
#             "offset": offset,
#             "fields": "title,authors,year,openAccessPdf"
#         }

#         r = safe_request(self.BASE_URL, params=params)
#         if not r:
#             return []

#         return r.json().get("data", [])


# # -----------------------------
# # DOWNLOAD PDF (FAST)
# # -----------------------------
# def download_pdf(task):
#     idx, url = task

#     try:
#         r = requests.get(url, timeout=25)

#         if r.status_code != 200:
#             return None

#         path = f"paper_{idx}.pdf"

#         with open(path, "wb") as f:
#             f.write(r.content)

#         return (idx, path)

#     except Exception:
#         return None


# # -----------------------------
# # EXTRACT TEXT (FAST)
# # -----------------------------
# def extract_pdf(task):
#     idx, path = task

#     try:
#         text = ""

#         with pdfplumber.open(path) as pdf:
#             for page in pdf.pages:
#                 t = page.extract_text()
#                 if t:
#                     text += t + "\n"

#         if len(text) < 200:
#             return None

#         return (idx, text)

#     except Exception:
#         return None


# # -----------------------------
# # MAIN PARALLEL PIPELINE
# # -----------------------------
# def build_dataset_parallel(query: str, min_results: int = 5):

#     client = SemanticScholarClient()
#     dataset = []
#     lock = threading.Lock()

#     offset = 0
#     attempts = 0
#     max_attempts = 20

#     print(f"🚀 Target: {min_results} papers\n")

#     while len(dataset) < min_results and attempts < max_attempts:

#         print(f"\n🔍 Batch {attempts+1} (offset {offset})")

#         papers = client.search(query, offset=offset, limit=10)

#         if not papers:
#             offset += 10
#             attempts += 1
#             continue

#         pdf_tasks = []

#         meta_map = {}

#         for i, p in enumerate(papers):
#             pdf_url = (p.get("openAccessPdf") or {}).get("url")

#             if not pdf_url:
#                 continue

#             pdf_tasks.append((i, pdf_url))
#             meta_map[i] = {
#                 "title": p.get("title"),
#                 "authors": [a["name"] for a in p.get("authors", [])],
#                 "year": p.get("year")
#             }

#         # -----------------------------
#         # PARALLEL DOWNLOAD
#         # -----------------------------
#         downloaded = []

#         with ThreadPoolExecutor(max_workers=5) as executor:
#             futures = [executor.submit(download_pdf, t) for t in pdf_tasks]

#             for f in as_completed(futures):
#                 result = f.result()
#                 if result:
#                     downloaded.append(result)

#         # -----------------------------
#         # PARALLEL EXTRACTION
#         # -----------------------------
#         extracted = []

#         with ThreadPoolExecutor(max_workers=5) as executor:
#             futures = [executor.submit(extract_pdf, d) for d in downloaded]

#             for f in as_completed(futures):
#                 result = f.result()
#                 if result:
#                     extracted.append(result)

#         # -----------------------------
#         # BUILD DATASET (thread-safe)
#         # -----------------------------
#         with lock:
#             for idx, text in extracted:
#                 meta = meta_map.get(idx)

#                 if not meta:
#                     continue

#                 dataset.append({
#                     "Title": meta["title"],
#                     "Author": ", ".join(meta["authors"]),
#                     "Year": meta["year"],
#                     "Paper_Content": text
#                 })

#                 print(f"✅ Collected ({len(dataset)}/{min_results})")

#                 if len(dataset) >= min_results:
#                     break

#         offset += 10
#         attempts += 1

#     if len(dataset) == 0:
#         raise Exception("❌ No valid papers found")

#     return dataset


# # -----------------------------
# # RUN
# # -----------------------------
# if __name__ == "__main__":

#     query = "Fraud Detection Banking Artificial Intelligence"

#     results = build_dataset_parallel(query, min_results=3)

#     import json
#     print("\n\n================ FINAL OUTPUT ================\n")
#     print(json.dumps(results, indent=2))