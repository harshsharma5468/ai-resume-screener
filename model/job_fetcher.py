import os
import requests
import pandas as pd
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from model.skill_extractor import extract_skills, extract_experience_years


def fetch_jobs(query: str = "software engineer", num_pages: int = 1) -> pd.DataFrame:
    """Fetch live jobs from JSearch API. Returns DataFrame matching CSV schema."""
    load_dotenv(override=True)
    api_key = os.getenv("JSEARCH_API_KEY", "").strip()
    if not api_key or api_key == "your_rapidapi_key_here":
        print("[job_fetcher] No API key found.")
        return pd.DataFrame()

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    rows = []
    for page in range(1, num_pages + 1):
        params = {"query": query, "page": str(page), "num_pages": "1"}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if not data:
                print(f"[job_fetcher] API returned empty data. Response: {resp.json()}")
                break
        except Exception as e:
            print(f"[job_fetcher] API error: {e}")
            break

        for i, job in enumerate(data):
            desc = job.get("job_description", "")
            skills = extract_skills(desc)
            exp = extract_experience_years(desc)
            rows.append({
                "job_id": job.get("job_id", f"live_{page}_{i}"),
                "job_title": job.get("job_title", ""),
                "company": job.get("employer_name", ""),
                "description": desc,
                "required_skills": ", ".join(skills),
                "experience_years": exp,
                "location": job.get("job_city", "") or job.get("job_country", ""),
                "apply_link": job.get("job_apply_link", ""),
            })

    return pd.DataFrame(rows) if rows else pd.DataFrame()
