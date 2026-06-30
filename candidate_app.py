import streamlit as st
from pathlib import Path
import pandas as pd
from extract_text import extract_text
from ai_model import compute_scores
import db
import string

st.set_page_config(
    page_title="Candidate Portal - Find Your Best Job Match",
    layout="centered"
)

# Custom CSS
st.markdown("""
<style>
    .big-font {font-size: 2.5rem !important; font-weight: bold; color: #1e3d59;}
    .score-big {font-size: 4rem; font-weight: bold; color: #ff6b6b;}
    .missing-skill {background-color: #ffe6e6; padding: 0.5rem; border-radius: 8px; margin: 0.3rem 0;}
    .present-skill {background-color: #e6f9e6; padding: 0.5rem; border-radius: 8px; margin: 0.3rem 0;}
    .card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 15px; text-align: center; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">Find Your Perfect Job Match</p>', unsafe_allow_html=True)
st.markdown("### Upload your resume and see which job fits you best!")

# Upload Resume
uploaded_file = st.file_uploader("Upload Your Resume (PDF, DOCX, TXT)", type=['pdf', 'docx', 'txt'])

if uploaded_file:
    temp_path = Path("temp_resume") / uploaded_file.name
    temp_path.parent.mkdir(exist_ok=True)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    with st.spinner("Extracting text from resume..."):
        try:
            resume_text = extract_text(str(temp_path))
            if not resume_text.strip():
                st.error("Could not extract text from resume. Try a different file.")
                st.stop()
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

    st.success("Resume parsed successfully!")

    vacancies = db.list_vacancies()
    if vacancies.empty:
        st.warning("No job openings available right now.")
        st.stop()

    results = []
    progress = st.progress(0)
    for idx, vac in vacancies.iterrows():
        jd_text = vac['description'] or ""
        skills_req = [s.strip() for s in (vac['skills'] or "").split(",") if s.strip()]
        weights = (vac['embedding_weight'], vac['skills_weight'], vac['other_weight'])

        scores = compute_scores(jd_text, resume_text, skills_req, weights)
        total_pct = scores['total_score'] * 100

        missing = [
            s for s in skills_req 
            if s.lower().translate(str.maketrans('', '', string.punctuation))
               not in resume_text.lower().translate(str.maketrans('', '', string.punctuation))
        ]

        results.append({
            'vacancy_id': vac['id'],
            'title': vac['title'],
            'total_score': total_pct,
            'embedding_score': scores['embedding_score'] * 100,
            'skills_score': scores['skills_score'] * 100,
            'missing_skills': missing,
            'skills_found': len(skills_req) - len(missing),
            'skills_total': len(skills_req)
        })
        progress.progress((idx + 1) / len(vacancies))

    df = pd.DataFrame(results).sort_values("total_score", ascending=False).reset_index(drop=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Best Match Score", f"{df.iloc[0]['total_score']:.1f}%")
    col2.metric("Total Jobs Analyzed", len(df))
    strong_matches = len(df[df['total_score'] >= 60])
    col3.metric("Strong Matches (≥60%)", strong_matches)

    st.markdown("---")

    top = df.iloc[0]
    st.markdown(f"""
    <div class="card">
        <h2>Best Match: {top['title']}</h2>
        <h1 class="score-big">{top['total_score']:.1f}%</h1>
        <p>You are a strong candidate for this role!</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"See detailed breakdown for {top['title']}", expanded=True):
        col_a, col_b = st.columns(2)
        col_a.metric("Semantic Match", f"{top['embedding_score']:.1f}%")
        col_b.metric("Skills Match", f"{top['skills_score']:.1f}%")

        st.markdown("#### Skills Analysis")
        skills_req = [s.strip() for s in vacancies[vacancies['id'] == top['vacancy_id']]['skills'].values[0].split(",")]
        resume_lower = resume_text.lower().translate(str.maketrans('', '', string.punctuation))

        col_found, col_missing = st.columns(2)
        with col_found:
            st.markdown("Found in your resume")
            for skill in skills_req:
                norm = skill.lower().translate(str.maketrans('', '', string.punctuation))
                if norm in resume_lower:
                    st.markdown(f"<div class='present-skill'>+ {skill}</div>", unsafe_allow_html=True)

        with col_missing:
            st.markdown("Missing / Improve")
            if top['missing_skills']:
                for skill in top['missing_skills']:
                    st.markdown(f"<div class='missing-skill'>– {skill}</div>", unsafe_allow_html=True)
                st.info("Tip: Add these keywords to your resume or LinkedIn!")
            else:
                st.success("All required skills found!")

    st.markdown("---")
    st.markdown("### All Job Matches")
    display_df = df[['title', 'total_score', 'skills_found', 'skills_total']].copy()
    display_df['total_score'] = display_df['total_score'].apply(lambda x: f"{x:.1f}%")
    display_df['Skills Coverage'] = display_df['skills_found'].astype(str) + "/" + display_df['skills_total'].astype(str)
    display_df = display_df[['title', 'total_score', 'Skills Coverage']]
    display_df.columns = ['Job Title', 'Match %', 'Skills Found']

    def color_score(val):
        val = float(val.strip('%'))
        if val >= 70: return 'background-color: #d4edda; color: #155724'
        elif val >= 50: return 'background-color: #fff3cd; color: #856404'
        else: return 'background-color: #f8d7da; color: #721c24'

    st.dataframe(display_df.style.applymap(color_score, subset=['Match %']), use_container_width=True)

    csv = df.to_csv(index=False).encode()
    st.download_button(
        "Download Full Match Report (CSV)",
        data=csv,
        file_name=f"job_match_report_{uploaded_file.name.split('.')[0]}.csv",
        mime="text/csv"
    )

    st.markdown("---")
    st.caption("Powered by AI Resume Matching Engine | Built for better career opportunities")
