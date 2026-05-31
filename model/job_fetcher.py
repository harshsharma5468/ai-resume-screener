import os
import requests
import pandas as pd


def fetch_jobs(query: str = "software engineer", num_pages: int = 1) -> pd.DataFrame:
    """Fetch live jobs from JSearch API. Returns DataFrame matching CSV schema."""
    api_key = os.getenv("JSEARCH_API_KEY", "")
    if not api_key or api_key == "your_rapidapi_key_here":
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
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except Exception:
            break

        for job in data:
            desc = job.get("job_description", "")
            rows.append({
                "job_title": job.get("job_title", ""),
                "company": job.get("employer_name", ""),
                "description": desc,
                "required_skills": "",   # scorer extracts from description
                "experience_years": 0,
                "location": job.get("job_city", "") or job.get("job_country", ""),
                "apply_link": job.get("job_apply_link", ""),
            })

    return pd.DataFrame(rows) if rows else pd.DataFrame()
