import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple

try:
    from sentence_transformers import SentenceTransformer
    _SBERT_AVAILABLE = True
except ImportError:
    _SBERT_AVAILABLE = False

_sbert_model = None
_tfidf_vectorizer = None


def _get_sbert():
    global _sbert_model
    if _sbert_model is None and _SBERT_AVAILABLE:
        _sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _sbert_model


def compute_skill_match(resume_skills: List[str], job_skills: List[str]) -> Tuple[float, List[str], List[str]]:
    if not job_skills:
        return 0.0, [], []
    resume_set = set(s.lower() for s in resume_skills)
    job_set = set(s.lower() for s in job_skills)
    matched = sorted(resume_set & job_set)
    missing = sorted(job_set - resume_set)
    score = len(matched) / len(job_set) * 100
    return round(score, 2), matched, missing


def compute_semantic_similarity(resume_text: str, job_text: str) -> float:
    model = _get_sbert()
    if model:
        embeddings = model.encode([resume_text, job_text])
        sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return round(float(sim) * 100, 2)
    # Fallback: TF-IDF cosine similarity
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        tfidf = vectorizer.fit_transform([resume_text, job_text])
        sim = cosine_similarity(tfidf[0], tfidf[1])[0][0]
        return round(float(sim) * 100, 2)
    except Exception:
        return 0.0


def compute_experience_score(resume_exp: int, required_exp: int) -> float:
    if required_exp == 0:
        return 100.0
    ratio = min(resume_exp / required_exp, 1.5)
    score = min(ratio * 100, 100)
    return round(score, 2)


def compute_final_score(skill_score: float, semantic_score: float, exp_score: float) -> float:
    return round(0.50 * skill_score + 0.35 * semantic_score + 0.15 * exp_score, 2)


def rank_jobs(
    resume_text: str,
    resume_skills: List[str],
    resume_exp: int,
    jobs_df: pd.DataFrame,
) -> pd.DataFrame:
    results = []
    for _, row in jobs_df.iterrows():
        job_skills = [s.strip() for s in str(row["required_skills"]).split(",")]
        skill_score, matched, missing = compute_skill_match(resume_skills, job_skills)
        semantic_score = compute_semantic_similarity(resume_text, str(row["description"]))
        exp_score = compute_experience_score(resume_exp, int(row["experience_years"]))
        final_score = compute_final_score(skill_score, semantic_score, exp_score)
        results.append({
            "job_id": row["job_id"],
            "job_title": row["job_title"],
            "company": row["company"],
            "location": row["location"],
            "required_skills": job_skills,
            "matched_skills": matched,
            "missing_skills": missing,
            "skill_score": skill_score,
            "semantic_score": semantic_score,
            "experience_score": exp_score,
            "match_score": final_score,
        })
    result_df = pd.DataFrame(results)
    return result_df.sort_values("match_score", ascending=False).reset_index(drop=True)
