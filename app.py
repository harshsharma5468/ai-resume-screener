import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from dotenv import load_dotenv

load_dotenv(override=True)
sys.path.insert(0, os.path.dirname(__file__))

from model.pdf_extractor import extract_text_from_bytes
from model.skill_extractor import (
    extract_skills, extract_experience_years,
    extract_name, extract_email, extract_phone
)
from model.scorer import rank_jobs
from model.job_fetcher import fetch_jobs

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; padding: 1rem 0;
    }
    .skill-tag {
        display: inline-block; padding: 3px 10px; border-radius: 15px;
        margin: 3px; font-size: 0.8rem; font-weight: 600;
    }
    .skill-matched { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
    .skill-missing { background-color: #fce4ec; color: #c62828; border: 1px solid #ef9a9a; }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #667eea, #764ba2); }
</style>
""", unsafe_allow_html=True)


def get_fallback_jobs():
    path = os.path.join(os.path.dirname(__file__), "dataset", "job_descriptions.csv")
    return pd.read_csv(path)


def render_skills(skills, css_class):
    return " ".join(f'<span class="skill-tag {css_class}">{s}</span>' for s in skills)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/resume.png", width=80)
    st.title("AI Resume Screener")
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("""
    1. 📄 Upload your resume (PDF)
    2. 🔍 AI extracts your skills
    3. 🌐 Fetches live jobs via API
    4. 🎯 Scores & ranks matches
    5. 💡 Shows skill gaps
    """)
    st.markdown("---")
    st.markdown("### Scoring Weights")
    st.markdown("- 🎯 Skill Match: **50%**")
    st.markdown("- 🧠 Semantic Match: **35%**")
    st.markdown("- 📅 Experience: **15%**")
    st.markdown("---")
    top_n = st.slider("Top N Jobs to Show", 3, 20, 5)
    min_score = st.slider("Minimum Match Score (%)", 0, 100, 0)
    st.markdown("---")
    api_key = os.getenv("JSEARCH_API_KEY", "")
    if api_key and api_key != "your_rapidapi_key_here":
        st.success("🌐 Live Jobs: API Connected")
    else:
        st.error("❌ No API key — using local CSV")


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown('<h1 class="main-header">🤖 AI Resume Screening & Job Match System</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#666;'>Upload your resume — AI extracts skills & fetches live matching jobs</p>", unsafe_allow_html=True)
st.markdown("---")

uploaded_file = st.file_uploader("📄 Upload Your Resume (PDF)", type=["pdf"])
use_demo = st.checkbox("🎮 Use Demo Resume (no PDF needed)", value=False)

DEMO_RESUME = """
John Smith
john.smith@email.com | +1-555-0123

SUMMARY
Data Scientist with 3 years of experience in machine learning, NLP, and data analysis.

SKILLS
Python, Machine Learning, Deep Learning, NLP, TensorFlow, PyTorch, Scikit-learn,
Pandas, NumPy, SQL, Tableau, Docker, AWS, Transformers, BERT, Spacy, Statistics,
Data Visualization, REST API

EXPERIENCE
Senior Data Scientist | TechCorp | 2021 - Present (3 years of experience)
- Built NLP models for text classification achieving 94% accuracy
- Deployed ML models on AWS using Docker and Kubernetes

Data Analyst | DataCo | 2020 - 2021
- Created dashboards in Tableau for business KPIs
"""

resume_text = ""
if use_demo:
    resume_text = DEMO_RESUME
    st.success("✅ Demo resume loaded!")
elif uploaded_file:
    with st.spinner("📖 Extracting text from PDF..."):
        try:
            resume_text = extract_text_from_bytes(uploaded_file.read())
            st.success("✅ Resume parsed successfully!")
        except Exception as e:
            st.error(f"❌ Error reading PDF: {e}")

# ── Analysis ──────────────────────────────────────────────────────────────────
if resume_text:
    candidate_name  = extract_name(resume_text)
    candidate_email = extract_email(resume_text)
    candidate_phone = extract_phone(resume_text)
    resume_skills   = extract_skills(resume_text)
    resume_exp      = extract_experience_years(resume_text)

    # ── Fetch live jobs — always fresh, no cache ──────────────────────────────
    query = " ".join(resume_skills[:5]) if resume_skills else "software engineer"
    jobs_df = pd.DataFrame()

    api_key = os.getenv("JSEARCH_API_KEY", "")
    if api_key and api_key != "your_rapidapi_key_here":
        with st.spinner(f"🌐 Fetching live jobs for: **{query}**..."):
            jobs_df = fetch_jobs(query=query, num_pages=2)
        if jobs_df.empty:
            st.warning("⚠️ API returned no results — falling back to local dataset.")
            jobs_df = get_fallback_jobs()
        else:
            st.success(f"✅ Loaded **{len(jobs_df)} live jobs** from JSearch API")
    else:
        st.warning("⚠️ No API key found in .env — using local dataset.")
        jobs_df = get_fallback_jobs()

    # ── Candidate Profile ─────────────────────────────────────────────────────
    st.markdown("## 👤 Candidate Profile")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👤 Name",       candidate_name  or "N/A")
    col2.metric("📧 Email",      candidate_email or "N/A")
    col3.metric("📱 Phone",      candidate_phone or "N/A")
    col4.metric("📅 Experience", f"{resume_exp} yrs" if resume_exp else "Not specified")

    st.markdown("### 🛠️ Extracted Skills")
    if resume_skills:
        st.markdown(render_skills(resume_skills, "skill-matched"), unsafe_allow_html=True)
        st.caption(f"Total skills detected: **{len(resume_skills)}**")
    else:
        st.warning("No skills detected.")

    st.markdown("---")

    # ── Job Matching ──────────────────────────────────────────────────────────
    st.markdown("## 🎯 Job Match Results")
    with st.spinner("🔍 Scoring jobs..."):
        results_df = rank_jobs(resume_text, resume_skills, resume_exp, jobs_df)

    filtered_df = results_df[results_df["match_score"] >= min_score].head(top_n)

    if filtered_df.empty:
        st.warning("No jobs found above the minimum score threshold.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🏆 Best Match",    f"{filtered_df.iloc[0]['match_score']:.1f}%")
        c2.metric("📊 Avg Score",     f"{filtered_df['match_score'].mean():.1f}%")
        c3.metric("✅ Jobs ≥ 50%",    int((filtered_df['match_score'] >= 50).sum()))
        c4.metric("🔍 Jobs Analyzed", len(results_df))

        st.markdown("---")

        # Bar chart
        st.markdown("### 📊 Match Score Overview")
        chart_df = filtered_df.copy()
        chart_df["label"] = chart_df["job_title"] + " @ " + chart_df["company"]
        fig = px.bar(
            chart_df, x="match_score", y="label", orientation="h",
            color="match_score",
            color_continuous_scale=["#f44336", "#ff9800", "#4caf50"],
            range_color=[0, 100],
            labels={"match_score": "Match Score (%)", "label": ""},
            title="Job Match Scores",
        )
        fig.update_layout(height=400, showlegend=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

        # Radar chart
        top = filtered_df.iloc[0]
        fig_radar = go.Figure(go.Scatterpolar(
            r=[top["skill_score"], top["semantic_score"], top["experience_score"], top["match_score"]],
            theta=["Skill Match", "Semantic Match", "Experience", "Overall"],
            fill="toself", line_color="#667eea", fillcolor="rgba(102,126,234,0.3)",
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title=f"Score Breakdown — {top['job_title']} @ {top['company']}",
            height=350,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("---")

        # Job cards
        st.markdown("### 🗂️ Detailed Job Matches")
        for i, row in filtered_df.iterrows():
            rank = filtered_df.index.get_loc(i) + 1
            with st.expander(
                f"#{rank}  {row['job_title']} @ {row['company']}  —  "
                f"{'🟢' if row['match_score'] >= 70 else '🟡' if row['match_score'] >= 40 else '🔴'} "
                f"{row['match_score']:.1f}%",
                expanded=(rank == 1),
            ):
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("🎯 Overall",    f"{row['match_score']:.1f}%")
                col_b.metric("🛠️ Skills",     f"{row['skill_score']:.1f}%")
                col_c.metric("🧠 Semantic",   f"{row['semantic_score']:.1f}%")
                col_d.metric("📅 Experience", f"{row['experience_score']:.1f}%")

                st.markdown(f"📍 **Location:** {row['location']}")
                if row.get("apply_link"):
                    st.markdown(f"🔗 [Apply Now]({row['apply_link']})")

                st.markdown("**✅ Matched Skills:**")
                if row["matched_skills"]:
                    st.markdown(render_skills(row["matched_skills"], "skill-matched"), unsafe_allow_html=True)
                else:
                    st.caption("No matched skills")

                st.markdown("**❌ Missing Skills:**")
                if row["missing_skills"]:
                    st.markdown(render_skills(row["missing_skills"], "skill-missing"), unsafe_allow_html=True)
                else:
                    st.success("You have all required skills! 🎉")

                st.progress(int(row["skill_score"]),     text=f"Skill Match: {row['skill_score']:.1f}%")
                st.progress(int(row["semantic_score"]),  text=f"Semantic Match: {row['semantic_score']:.1f}%")
                st.progress(int(row["experience_score"]),text=f"Experience: {row['experience_score']:.1f}%")

        st.markdown("---")

        # Skill gap
        st.markdown("## 💡 Skill Gap Analysis")
        all_missing = {}
        for _, row in filtered_df.iterrows():
            for skill in row["missing_skills"]:
                all_missing[skill] = all_missing.get(skill, 0) + 1

        if all_missing:
            gap_df = pd.DataFrame(
                sorted(all_missing.items(), key=lambda x: -x[1]),
                columns=["Skill", "Jobs Requiring It"]
            )
            col_gap1, col_gap2 = st.columns(2)
            with col_gap1:
                fig_gap = px.bar(
                    gap_df.head(10), x="Jobs Requiring It", y="Skill", orientation="h",
                    color="Jobs Requiring It", color_continuous_scale="reds",
                    title="Skills to Learn",
                )
                fig_gap.update_layout(height=350, yaxis=dict(autorange="reversed"), showlegend=False)
                st.plotly_chart(fig_gap, use_container_width=True)
            with col_gap2:
                st.markdown("### 📚 Learning Resources")
                resources = {
                    "machine learning": "https://www.coursera.org/learn/machine-learning",
                    "deep learning":    "https://www.deeplearning.ai/",
                    "python":           "https://docs.python.org/3/tutorial/",
                    "aws":              "https://aws.amazon.com/training/",
                    "docker":           "https://docs.docker.com/get-started/",
                    "kubernetes":       "https://kubernetes.io/docs/tutorials/",
                    "sql":              "https://www.w3schools.com/sql/",
                    "tensorflow":       "https://www.tensorflow.org/tutorials",
                    "pytorch":          "https://pytorch.org/tutorials/",
                    "nlp":              "https://huggingface.co/learn/nlp-course/",
                    "tableau":          "https://www.tableau.com/learn/training",
                    "spark":            "https://spark.apache.org/docs/latest/",
                }
                for skill in gap_df["Skill"].head(8):
                    url = resources.get(skill.lower())
                    link = f"[Learn here]({url})" if url else "Search on Coursera / Udemy"
                    st.markdown(f"- 📖 **{skill.title()}** → {link}")
        else:
            st.success("🎉 You have all required skills for the top matched jobs!")

        st.markdown("---")

        # Download
        st.markdown("### 📥 Download Results")
        dl = filtered_df[["job_title", "company", "location", "match_score",
                           "skill_score", "semantic_score", "experience_score"]].copy()
        dl.columns = ["Job Title", "Company", "Location", "Match Score (%)",
                      "Skill Score (%)", "Semantic Score (%)", "Experience Score (%)"]
        st.download_button("⬇️ Download as CSV", dl.to_csv(index=False),
                           "job_match_results.csv", "text/csv")

else:
    st.markdown("""
    <div style="text-align:center; padding:3rem; background:linear-gradient(135deg,#f5f7fa,#c3cfe2); border-radius:15px;">
        <h2>👆 Upload your resume to get started</h2>
        <p style="color:#666; font-size:1.1rem;">
            AI extracts your skills → fetches live jobs from the web → scores & ranks them
        </p>
        <p>Or tick <b>Demo Resume</b> above for an instant example.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Sample Job Listings (local fallback)")
    fallback = get_fallback_jobs()[["job_title", "company", "location", "experience_years", "required_skills"]]
    fallback.columns = ["Job Title", "Company", "Location", "Exp (yrs)", "Required Skills"]
    st.dataframe(fallback, use_container_width=True, height=400)
