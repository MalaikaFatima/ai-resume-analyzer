import streamlit as st
from pathlib import Path
import time
import string
import pandas as pd
import db
from ai_model import compute_scores
from extract_text import extract_text

def show_browse_jobs():
    """Browse Jobs Page with AI Analysis"""
    st.header("Browse Jobs")
    
    cats = db.list_categories()
    cat_filter = st.selectbox("Filter by Category", ["All"] + cats['name'].tolist() if not cats.empty else ["All"])
    
    vacs = db.list_vacancies()
    if cat_filter != "All":
        vacs = vacs[vacs['category'] == cat_filter]
    
    if vacs.empty:
        st.info("No jobs available in this category")
        return
    
    for _, vac in vacs.iterrows():
        with st.expander(f"{vac['title']} • {vac['category']}"):
            st.write(vac['description'])
            st.caption(f"Skills: {vac['skills']}")
            
            # Two-step flow: first request to Upload & Apply sets pending vacancy, then user uploads resume
            apply_key = f"apply_btn_{vac['id']}"
            if st.button("Upload Resume & Apply", key=apply_key):
                st.session_state.pending_apply_vac = int(vac['id'])
                st.session_state.pending_apply_vac_title = vac['title']
                st.rerun()

            # If this vacancy is pending application, show uploader + confirm button
            if st.session_state.get('pending_apply_vac') == int(vac['id']):
                st.info(f"Upload a resume to apply for: {vac['title']}")
                pending_uploader = st.file_uploader("Upload resume to use for this application", type=['pdf','docx','txt'], key=f"pending_upload_{vac['id']}")
                if pending_uploader and st.button("Upload & Apply", key=f"confirm_apply_{vac['id']}"):
                    cand_id = st.session_state.get('candidate_id')
                    if not cand_id:
                        st.warning("You must be logged in as a candidate to upload and apply.")
                        st.session_state.pop('pending_apply_vac', None)
                        st.session_state.pop('pending_apply_vac_title', None)
                        st.rerun()

                    # Save uploaded file
                    ts = int(time.time())
                    safe_name = f"{cand_id}_{ts}_{pending_uploader.name}"
                    path = Path("uploads") / safe_name
                    path.parent.mkdir(exist_ok=True)
                    with open(path, "wb") as f:
                        f.write(pending_uploader.getbuffer())

                    # Extract text and update candidate record
                    try:
                        text = extract_text(str(path))
                    except Exception as e:
                        st.warning(f"Saved file but failed to extract resume text: {e}")
                        text = ""

                    try:
                        db.run_query(
                            "UPDATE candidates SET filename=%s, extracted_text=%s WHERE id=%s",
                            (str(path), text, cand_id),
                            fetch=False
                        )
                    except Exception as e:
                        st.error(f"Failed to update candidate record: {e}")

                    # Now compute match & insert application (reuse existing logic)
                    resume_text = text or db.get_candidate(cand_id).get('extracted_text') or ""
                    if not resume_text.strip():
                        st.warning("Resume uploaded but no text was extracted. Application still recorded.")

                    skills_req = [s.strip() for s in vac['skills'].split(",")]

                    scores = compute_scores(
                        vac['description'],
                        resume_text,
                        skills_req,
                        (vac['embedding_weight'], vac['skills_weight'], vac['other_weight'])
                    )

                    match_pct = round(scores['total_score'] * 100, 1)
                    st.markdown("---")
                    st.markdown(f"### Your Match: {match_pct}%")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Semantic Match", f"{scores['embedding_score']*100:.1f}%")
                    with col2:
                        st.metric("Skills Match", f"{scores['skills_score']*100:.1f}%")

                    from ai_model import detect_skills
                    found_skills, missing_skills = detect_skills(skills_req, resume_text)
                    col_f, col_m = st.columns(2)
                    with col_f:
                        st.markdown("Found in Resume:")
                        if found_skills:
                            for s in found_skills:
                                st.markdown(f"<span class='skill-found'>✓ {s}</span>", unsafe_allow_html=True)
                        else:
                            st.info("No matching skills found")
                    with col_m:
                        st.markdown("Missing Skills:")
                        if missing_skills:
                            for s in missing_skills:
                                st.markdown(f"<span class='skill-missing'>✗ {s}</span>", unsafe_allow_html=True)
                        else:
                            st.success("All skills found!")

                    if missing_skills:
                        st.info("AI Recommendation: Consider adding these skills:\n- " + "\n- ".join(missing_skills[:3]))

                    # Insert application (ignore duplicates) and record which resume file was used
                    used_resume = str(path) if path else None
                    try:
                        db.run_query(
                            "INSERT IGNORE INTO applications (candidate_id, vacancy_id, resume_filename) VALUES (%s, %s, %s)",
                            (cand_id, vac['id'], used_resume),
                            fetch=False
                        )
                    except Exception:
                        # Fallback for older schemas without resume_filename column
                        db.run_query(
                            "INSERT IGNORE INTO applications (candidate_id, vacancy_id) VALUES (%s, %s)",
                            (cand_id, vac['id']),
                            fetch=False
                        )

                    # Clear pending state
                    st.session_state.pop('pending_apply_vac', None)
                    st.session_state.pop('pending_apply_vac_title', None)
                    st.success("Applied successfully")

def show_upload_resume():
    """Upload Resume Page"""
    st.header("Update Resume")
    
    uploaded = st.file_uploader("Upload new resume(s)", type=['pdf','docx','txt'], accept_multiple_files=True)
    
    if uploaded and st.button("Save Resume(s)"):
        cand_id = st.session_state.get('candidate_id')
        if not cand_id:
            # If user is logged in as candidate but has no candidate_id, create one
            if st.session_state.get('logged_in') and st.session_state.get('role') == 'candidate':
                try:
                    cid = db.add_candidate(st.session_state.username, 'not_uploaded', '')
                    if cid:
                        db.run_query("UPDATE users SET candidate_id=%s WHERE username=%s", (cid, st.session_state.username), fetch=False)
                        st.session_state.candidate_id = cid
                        cand_id = cid
                        st.info("Created candidate profile for your account.")
                    else:
                        st.error("Could not create candidate profile. Please contact support.")
                        return
                except Exception as e:
                    st.error(f"Failed to create candidate profile: {e}")
                    return
            else:
                st.warning("You must be logged in as a candidate to upload a resume.")
                return

        last_saved = None
        for file in uploaded:
            ts = int(time.time())
            safe_name = f"{cand_id}_{ts}_{file.name}"
            path = Path("uploads") / safe_name
            path.parent.mkdir(exist_ok=True)
            with open(path, "wb") as f:
                f.write(file.getbuffer())
            last_saved = path

        if not last_saved:
            st.error("No files were saved.")
            return

        # Extract text from the latest uploaded file and update candidate record to point to it
        try:
            text = extract_text(str(last_saved))
        except Exception as e:
            st.warning(f"Saved file but failed to extract resume text: {e}")
            text = ""

        result = db.run_query(
            "UPDATE candidates SET filename=%s, extracted_text=%s WHERE id=%s",
            (str(last_saved), text, cand_id), 
            fetch=False
        )

        # Verify update succeeded by re-fetching candidate
        updated = db.get_candidate(cand_id)
        if result is None or not updated:
            st.error("Failed to save resume to database. Please try again.")
            return

        st.success(f"{len(uploaded)} file(s) uploaded. Latest saved as {last_saved.name}")

def show_my_applications():
    """My Applications Page"""
    st.header("My Applications")
    
    apps = db.run_query("""
        SELECT a.id as app_id, v.title as vacancy_title, v.category, a.applied_at, a.vacancy_id
        FROM applications a
        LEFT JOIN vacancies v ON a.vacancy_id = v.id
        WHERE a.candidate_id = %s
        ORDER BY a.applied_at DESC
    """, (st.session_state.candidate_id,))
    
    if apps:
        df = pd.DataFrame(apps)
        # vacancy_title may be None if the vacancy was deleted
        df['Job Title'] = df['vacancy_title'].fillna('Deleted vacancy')
        df['Category'] = df['category'].fillna('Deleted')
        df['Applied On'] = df['applied_at']
        display_df = df[['Job Title', 'Category', 'Applied On']]
        st.dataframe(display_df, use_container_width=True)
        st.metric("Total Applications", len(apps))

        # Allow candidate to withdraw an application
        options = []
        app_map = {}
        for _, r in df.iterrows():
            label = f"{r['Job Title']} • {r['Applied On']}"
            options.append(label)
            app_map[label] = (int(r['app_id']), int(r['vacancy_id']) if r['vacancy_id'] is not None else None)

        sel = st.selectbox("Select application to withdraw", options=options, key='sel_withdraw')
        if sel:
            app_id, vac_id = app_map[sel]
            if st.button("Withdraw Application", key=f"withdraw_{app_id}"):
                st.session_state.pending_withdraw_app = int(app_id)

            if st.session_state.get('pending_withdraw_app') == int(app_id):
                st.warning("Are you sure you want to withdraw this application?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Yes, Withdraw", key=f"confirm_withdraw_{app_id}"):
                        try:
                            db.run_query("DELETE FROM applications WHERE id=%s", (app_id,), fetch=False)
                            if vac_id:
                                db.run_query("DELETE FROM scores WHERE candidate_id=%s AND vacancy_id=%s", (st.session_state.candidate_id, vac_id), fetch=False)
                            st.success("Application withdrawn successfully")
                            st.session_state.pop('pending_withdraw_app', None)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to withdraw application: {e}")
                with c2:
                    if st.button("Cancel", key=f"cancel_withdraw_{app_id}"):
                        st.session_state.pop('pending_withdraw_app', None)
                        st.info("Withdrawal cancelled")
    else:
        st.info("No applications yet. Browse jobs to apply!")


def _list_candidate_uploads(candidate_id: int):
    """Return DataFrame listing files uploaded by this candidate (based on filename prefix)."""
    p = Path("uploads")
    if not p.exists():
        return pd.DataFrame()

    rows = []
    prefix = f"{candidate_id}_"
    # Try to include any previously saved filename recorded in the candidates table
    cand = db.get_candidate(candidate_id)
    candidate_recorded_filename = None
    candidate_name_fragment = None
    if cand:
        candidate_recorded_filename = Path(cand.get('filename') or "").name
        # create a simple name fragment to heuristically match older filenames
        candidate_name_fragment = (cand.get('name') or "").lower().replace(' ', '')
    for f in p.iterdir():
        if f.is_file() and f.name.startswith(prefix):
            stat = f.stat()
            rows.append({
                "filename": f.name,
                "path": str(f),
                "uploaded_at": pd.to_datetime(stat.st_mtime, unit='s')
            })

        # Also include the candidate's recorded filename even if it wasn't saved with a prefix
        elif f.is_file() and candidate_recorded_filename and f.name == candidate_recorded_filename:
            stat = f.stat()
            rows.append({
                "filename": f.name,
                "path": str(f),
                "uploaded_at": pd.to_datetime(stat.st_mtime, unit='s')
            })

        # Heuristic: include files that contain the candidate's name fragment (helps recover older uploads)
        elif f.is_file() and candidate_name_fragment and candidate_name_fragment in f.name.lower().replace(' ', ''):
            stat = f.stat()
            rows.append({
                "filename": f.name,
                "path": str(f),
                "uploaded_at": pd.to_datetime(stat.st_mtime, unit='s')
            })

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows).sort_values("uploaded_at", ascending=False).reset_index(drop=True)
    return df


# def show_uploaded_resumes():
#     """Show table of resumes the current candidate uploaded."""
#     cand_id = st.session_state.get('candidate_id')
#     if not cand_id:
#         st.info("No candidate profile found. Upload a resume first.")
#         return

#     df = _list_candidate_uploads(cand_id)
#     st.header("Your Uploaded Resumes")
#     if df.empty:
#         st.info("No uploaded resumes found for your account.")
#         return

#     display = df[["filename", "uploaded_at"]].copy()
#     display.columns = ["Filename", "Uploaded At"]
#     st.dataframe(display, use_container_width=True)
