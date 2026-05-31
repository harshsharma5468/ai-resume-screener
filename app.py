import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from model.pdf_extractor import extract_text_from_bytes
from model.skill_extractor import (
    extract_skills, extract_experience_years,
    extract_name, extract_email, extract_phone
)
from model.scorer import rank_jobs

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .score-high   { color: #00c853; font-weight: bold; font-size: 1.2rem; }
    .score-medium { color: #ff9800; font-weight: bold; font-size: 1.2rem; }
    .score-low    { color: #f44336; font-weight: bold; font-size: 1.2rem; }
    .skill-tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 15px;
        margin: 3px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .skill-matched { background-color: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
    .skill-missing { background-color: #fce4ec; color: #c62828; border: 1px solid #ef9a9a; }
    .job-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
    }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #667eea, #764ba2); }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_jobs():
    path = os.path.join(os.path.dirname(__file__), "dataset", "job_descriptions.csv")
    return pd.read_csv(path)


def score_color(score: float) -> str:
    if score >= 70:
        return "score-high"
    elif score >= 40:
        return "score-medium"
    return "score-low"


def render_skills(skills, css_class):
    return " ".join(
        f'<span class="skill-tag {css_class}">{s}</span>' for s in skills
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/resume.png", width=80)
    st.title("AI Resume Screener")
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("""
    1. 📄 Upload your resume (PDF)
    2. 🔍 AI extracts your skills
    3. 📊 Matches against job listings
    4. 🎯 Get your match scores
    5. 💡 See skill gaps & suggestions
    """)
    st.markdown("---")
    st.markdown("### Scoring Weights")
    st.markdown("- 🎯 Skill Match: **50%**")
    st.markdown("- 🧠 Semantic Match: **35%**")
    st.markdown("- 📅 Experience: **15%**")
    st.markdown("---")
    top_n = st.slider("Top N Jobs to Show", 3, 20, 5)
    min_score = st.slider("Minimum Match Score (%)", 0, 100, 0)


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown('<h1 class="main-header">🤖 AI Resume Screening & Job Match System</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#666;'>Upload your resume and discover your best job matches powered by NLP & ML</p>", unsafe_allow_html=True)
st.markdown("---")

jobs_df = load_jobs()

uploaded_file = st.file_uploader(
    "📄 Upload Your Resume (PDF)",
    type=["pdf"],
    help="Upload a PDF resume to get started",
)

# ── Demo mode ─────────────────────────────────────────────────────────────────
use_demo = st.checkbox("🎮 Use Demo Resume (no PDF needed)", value=False)

DEMO_RESUME = """
John Smith
john.smith@email.com | +1-555-0123

SUMMARY
Data Scientist with 3 years of experience in machine learning, NLP, and data analysis.
Passionate about building AI-powered solutions.

SKILLS
Python, Machine Learning, Deep Learning, NLP, TensorFlow, PyTorch, Scikit-learn,
Pandas, NumPy, SQL, Tableau, Docker, AWS, Transformers, BERT, Spacy, Statistics,
Data Visualization, REST API, Git

EXPERIENCE
Senior Data Scientist | TechCorp | 2021 - Present
- Built NLP models for text classification achieving 94% accuracy
- Developed recommendation systems using collaborative filtering
- Deployed ML models on AWS using Docker and Kubernetes

Data Analyst | DataCo | 2020 - 2021
- Created dashboards in Tableau for business KPIs
- Wrote complex SQL queries for data extraction

EDUCATION
M.S. Computer Science | Stanford University | 2020
B.S. Mathematics | UC Berkeley | 2018
"""

resume_text = ""
candidate_name = ""

if use_demo:
    resume_text = DEMO_RESUME
    st.success("✅ Demo resume loaded!")
elif uploaded_file:
    with st.spinner("📖 Extracting text from PDF..."):
        try:
            resume_text = extract_text_from_bytes(uploaded_file.read())
            st.success("✅ Resume uploaded and parsed successfully!")
        except Exception as e:
            st.error(f"❌ Error reading PDF: {e}")

# ── Analysis ──────────────────────────────────────────────────────────────────
if resume_text:
    candidate_name  = extract_name(resume_text)
    candidate_email = extract_email(resume_text)
    candidate_phone = extract_phone(resume_text)
    resume_skills   = extract_skills(resume_text)
    resume_exp      = extract_experience_years(resume_text)

    # ── Candidate Profile ─────────────────────────────────────────────────────
    st.markdown("## 👤 Candidate Profile")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👤 Name",        candidate_name  or "N/A")
    col2.metric("📧 Email",       candidate_email or "N/A")
    col3.metric("📱 Phone",       candidate_phone or "N/A")
    col4.metric("📅 Experience",  f"{resume_exp} yrs" if resume_exp else "Not specified")

    st.markdown("### 🛠️ Extracted Skills")
    if resume_skills:
        st.markdown(render_skills(resume_skills, "skill-matched"), unsafe_allow_html=True)
        st.caption(f"Total skills detected: **{len(resume_skills)}**")
    else:
        st.warning("No skills detected. Make sure your resume contains recognizable skill keywords.")

    st.markdown("---")

    # ── Job Matching ──────────────────────────────────────────────────────────
    st.markdown("## 🎯 Job Match Results")

    with st.spinner("🔍 Analyzing and scoring jobs..."):
        results_df = rank_jobs(resume_text, resume_skills, resume_exp, jobs_df)

    filtered_df = results_df[results_df["match_score"] >= min_score].head(top_n)

    if filtered_df.empty:
        st.warning("No jobs found above the minimum score threshold. Try lowering the filter.")
    else:
        # ── Summary metrics ───────────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🏆 Best Match",    f"{filtered_df.iloc[0]['match_score']:.1f}%")
        c2.metric("📊 Avg Score",     f"{filtered_df['match_score'].mean():.1f}%")
        c3.metric("✅ Jobs ≥ 50%",    int((filtered_df['match_score'] >= 50).sum()))
        c4.metric("🔍 Jobs Analyzed", len(results_df))

        st.markdown("---")

        # ── Score bar chart ───────────────────────────────────────────────────
        st.markdown("### 📊 Match Score Overview")
        chart_df = filtered_df[["job_title", "company", "match_score", "skill_score", "semantic_score"]].copy()
        chart_df["label"] = chart_df["job_title"] + " @ " + chart_df["company"]

        fig = px.bar(
            chart_df,
            x="match_score",
            y="label",
            orientation="h",
            color="match_score",
            color_continuous_scale=["#f44336", "#ff9800", "#4caf50"],
            range_color=[0, 100],
            labels={"match_score": "Match Score (%)", "label": ""},
            title="Job Match Scores",
        )
        fig.update_layout(height=400, showlegend=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

        # ── Radar chart for top job ───────────────────────────────────────────
        top = filtered_df.iloc[0]
        fig_radar = go.Figure(go.Scatterpolar(
            r=[top["skill_score"], top["semantic_score"], top["experience_score"], top["match_score"]],
            theta=["Skill Match", "Semantic Match", "Experience", "Overall"],
            fill="toself",
            line_color="#667eea",
            fillcolor="rgba(102,126,234,0.3)",
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title=f"Score Breakdown — {top['job_title']} @ {top['company']}",
            height=350,
        )
        st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("---")

        # ── Individual job cards ──────────────────────────────────────────────
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
                col_a.metric("🎯 Overall",   f"{row['match_score']:.1f}%")
                col_b.metric("🛠️ Skills",    f"{row['skill_score']:.1f}%")
                col_c.metric("🧠 Semantic",  f"{row['semantic_score']:.1f}%")
                col_d.metric("📅 Experience",f"{row['experience_score']:.1f}%")

                st.markdown(f"📍 **Location:** {row['location']}")

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

                # Progress bars
                st.markdown("**Score Breakdown:**")
                st.progress(int(row["skill_score"]),    text=f"Skill Match: {row['skill_score']:.1f}%")
                st.progress(int(row["semantic_score"]), text=f"Semantic Match: {row['semantic_score']:.1f}%")
                st.progress(int(row["experience_score"]),text=f"Experience: {row['experience_score']:.1f}%")

        st.markdown("---")

        # ── Skill Gap Analysis ────────────────────────────────────────────────
        st.markdown("## 💡 Skill Gap Analysis & Recommendations")

        all_missing = {}
        for _, row in filtered_df.iterrows():
            for skill in row["missing_skills"]:
                all_missing[skill] = all_missing.get(skill, 0) + 1

        if all_missing:
            gap_df = pd.DataFrame(
                sorted(all_missing.items(), key=lambda x: -x[1]),
                columns=["Skill", "Jobs Requiring It"]
            )
            col_gap1, col_gap2 = st.columns([1, 1])
            with col_gap1:
                st.markdown("### 🔥 Most In-Demand Missing Skills")
                fig_gap = px.bar(
                    gap_df.head(10),
                    x="Jobs Requiring It",
                    y="Skill",
                    orientation="h",
                    color="Jobs Requiring It",
                    color_continuous_scale="reds",
                    title="Skills to Learn for Better Matches",
                )
                fig_gap.update_layout(height=350, yaxis=dict(autorange="reversed"), showlegend=False)
                st.plotly_chart(fig_gap, use_container_width=True)

            with col_gap2:
                st.markdown("### 📚 Learning Recommendations")
                resources = {
                    "machine learning":  "https://www.coursera.org/learn/machine-learning",
                    "deep learning":     "https://www.deeplearning.ai/",
                    "python":            "https://docs.python.org/3/tutorial/",
                    "aws":               "https://aws.amazon.com/training/",
                    "docker":            "https://docs.docker.com/get-started/",
                    "kubernetes":        "https://kubernetes.io/docs/tutorials/",
                    "sql":               "https://www.w3schools.com/sql/",
                    "tensorflow":        "https://www.tensorflow.org/tutorials",
                    "pytorch":           "https://pytorch.org/tutorials/",
                    "nlp":               "https://huggingface.co/learn/nlp-course/",
                    "tableau":           "https://www.tableau.com/learn/training",
                    "spark":             "https://spark.apache.org/docs/latest/",
                }
                for skill in gap_df["Skill"].head(8):
                    url = resources.get(skill.lower())
                    if url:
                        st.markdown(f"- 📖 **{skill.title()}** → [Learn here]({url})")
                    else:
                        st.markdown(f"- 📖 **{skill.title()}** → Search on Coursera / Udemy")
        else:
            st.success("🎉 You have all the skills required for the top matched jobs!")

        st.markdown("---")

        # ── Download results ──────────────────────────────────────────────────
        st.markdown("### 📥 Download Results")
        download_df = filtered_df[["job_title", "company", "location", "match_score",
                                   "skill_score", "semantic_score", "experience_score"]].copy()
        download_df.columns = ["Job Title", "Company", "Location", "Match Score (%)",
                                "Skill Score (%)", "Semantic Score (%)", "Experience Score (%)"]
        csv = download_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download Match Results as CSV",
            data=csv,
            file_name="job_match_results.csv",
            mime="text/csv",
        )

else:
    # ── Landing placeholder ───────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 3rem; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 15px;">
        <h2>👆 Upload your resume to get started</h2>
        <p style="color:#666; font-size:1.1rem;">
            Our AI will extract your skills, match you against 20 real job listings,<br>
            and show you exactly what skills you need to land your dream job.
        </p>
        <br>
        <p>Or check the <b>Demo Resume</b> checkbox above to see a live example!</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Available Job Listings Preview")
    preview_df = jobs_df[["job_title", "company", "location", "experience_years", "required_skills"]].copy()
    preview_df.columns = ["Job Title", "Company", "Location", "Exp (yrs)", "Required Skills"]
    st.dataframe(preview_df, use_container_width=True, height=400)
