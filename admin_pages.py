import streamlit as st
from pathlib import Path
import pandas as pd
import db
from ai_model import compute_scores
from extract_text import extract_text
import time

# ---------------------------------------------------------
# 1. CATEGORY MANAGEMENT
# ---------------------------------------------------------
def show_categories():
    st.header("Manage Categories")
    st.session_state.setdefault("cat_added", False)
    st.session_state.setdefault("cat_deleted", False)

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.session_state.cat_added:
            st.success("Category added successfully!")
            st.session_state.cat_added = False
        if st.session_state.cat_deleted:
            st.success("Category deleted successfully!")
            st.session_state.cat_deleted = False

        with st.form("add_category_form", clear_on_submit=True):
            new_cat = st.text_input("Category Name", placeholder="e.g., Data Science, Marketing")
            if st.form_submit_button("Add Category", use_container_width=True, type="primary"):
                if not new_cat.strip():
                    st.error("Please enter a category name")
                else:
                    existing = db.list_categories()
                    if not existing.empty and new_cat.strip().lower() in existing["name"].str.lower().values:
                        st.error(f"Category '{new_cat.strip()}' already exists!")
                    else:
                        db.add_category(new_cat.strip())
                        st.session_state.cat_added = True
                        st.rerun()

    with col2:
        st.info("**Tips:**\n\n• Use clear names\n• Avoid duplicates\n• Categories organize jobs")

    st.markdown("---")

    

    st.subheader("Current Categories")
    cats = db.list_categories()
    if cats.empty:
        st.info("No categories yet")
        return

    st.dataframe(cats[["id", "name", "created_at"]], use_container_width=True, hide_index=True)
    st.markdown("---")

    col_del1, col_del2 = st.columns([3, 1])
    with col_del1:
        del_cat = st.selectbox(
            "Select category to delete",
            options=[0] + cats["id"].tolist(),
            format_func=lambda x: "-- Select --" if x == 0 else cats[cats["id"] == x]["name"].iloc[0],
            key="del_cat_select"
        )
    with col_del2:
        st.write(""); st.write("")
        if st.button("Delete Category", type="secondary", use_container_width=True):
            if del_cat != 0:
                if db.delete_category(del_cat):
                    st.session_state.cat_deleted = True
                    st.rerun()
                else:
                    st.error("Cannot delete: Vacancies exist in this category")
            else:
                st.warning("Please select a category")


# ---------------------------------------------------------
# 2. VACANCY MANAGEMENT
# ---------------------------------------------------------
def show_vacancies():
    st.header("Vacancy Management")

    with st.expander("Add New Vacancy", expanded=True):
        with st.form("add_vacancy", clear_on_submit=True):
            title = st.text_input("Job Title *")
            desc = st.text_area("Job Description *", height=150)
            skills = st.text_input("Required Skills * (comma separated)")
            cats = db.list_categories()
            cat = st.selectbox("Category *", cats["name"].tolist() if not cats.empty else ["General"])

            c1, c2, c3 = st.columns(3)
            with c1: w1 = st.slider("Description Weight", 0.0, 1.0, 0.5, 0.05)
            with c2: w2 = st.slider("Skills Weight", 0.0, 1.0, 0.3, 0.05)
            with c3: w3 = st.slider("Other Weight", 0.0, 1.0, 0.2, 0.05)

            if st.form_submit_button("Add Vacancy", type="primary", use_container_width=True):
                if not title or not desc or not skills:
                    st.error("All fields required")
                elif abs(w1 + w2 + w3 - 1.0) > 0.01:
                    st.error(f"Weights must sum to 1.0 (current: {w1+w2+w3:.2f})")
                else:
                    # Split skills strictly on commas (admin should provide comma-separated list)
                    skills_list = [s.strip() for s in skills.split(",") if s.strip()]
                    if not skills_list:
                        st.error("Please enter at least one skill (comma separated)")
                    else:
                        db.add_vacancy(title, desc, skills_list, w1, w2, w3, cat)
                        st.success("Vacancy added!")
                        st.rerun()

    st.markdown("---")
    st.subheader("Current Vacancies")
    vacs = db.list_vacancies()
    if vacs.empty:
        st.info("No vacancies yet")
        return
  

    st.dataframe(vacs[["title", "category", "created_at"]], use_container_width=True, hide_index=True)
    st.markdown("---")

    col1, col2 = st.columns([3, 1])
    with col1:
        del_vac = st.selectbox(
            "Select vacancy to delete",
            options=[0] + vacs["id"].tolist(),
            format_func=lambda x: "-- Select --" if x == 0 else vacs[vacs["id"] == x]["title"].iloc[0],
            key="del_vac_select"
        )
    with col2:
        st.write(""); st.write("")
        if st.button("Delete Vacancy", type="secondary", use_container_width=True, key="del_vac_btn"):
            if del_vac != 0:

                st.session_state.pending_delete_vac = int(del_vac)
            else:
                st.warning("Please select a vacancy")

        if st.session_state.get('pending_delete_vac'):
            pending_id = st.session_state.pending_delete_vac
            if pending_id == del_vac:
                title = vacs[vacs["id"] == pending_id]["title"].iloc[0]
                st.warning(f"Are you sure you want to delete **{title}**?")
                coly, coln = st.columns([1,1])
                with coly:
                    if st.button("Yes", type="primary", key="confirm_del_vac"):
                        try:
                            res = db.delete_vacancy(pending_id)
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
                            res = None

                        if not res:
                            apps = db.run_query("SELECT COUNT(*) as cnt FROM applications WHERE vacancy_id=%s", (pending_id,))
                            cnt = apps[0]['cnt'] if apps else 0
                            if cnt > 0:
                                st.error("Cannot delete vacancy: there are applications for this vacancy. Remove applications first.")
                            else:
                                st.error("Failed to delete vacancy. Check server logs.")
                        else:
                            st.success("Vacancy deleted!")
                            st.session_state.pop('pending_delete_vac', None)
                            st.rerun()
                with coln:
                    if st.button("Cancel", type="secondary", key="cancel_del_vac"):
                        del st.session_state['pending_delete_vac']
                        st.info("Deletion cancelled")


# ---------------------------------------------------------
# 3. RESUME UPLOAD
# ---------------------------------------------------------
def show_upload_resumes():
    st.header("Upload Candidate Resumes")

    uploaded = st.file_uploader("Upload PDF/DOCX files", type=["pdf", "docx"], accept_multiple_files=True)
    name_input = st.text_input("Candidate Name (optional – uses filename if empty)")

    if st.button("Save All Resumes", type="primary", use_container_width=True):
        if not uploaded:
            st.warning("Please upload at least one file")
        else:
            with st.spinner("Processing resumes..."):
                saved = []
                for file in uploaded:
                    save_path = Path("uploads") / file.name
                    save_path.parent.mkdir(exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(file.getbuffer())
                    text = extract_text(str(save_path))
                    cname = name_input.strip() if name_input.strip() else file.name.rsplit(".", 1)[0]
                    db.add_candidate(cname, str(save_path), text)
                    saved.append(file.name)

            if saved:
                st.success(f"{len(saved)} resume(s) uploaded and processed: {', '.join(saved)}")
            st.rerun()

    st.markdown("---")
    st.subheader("Uploaded Resumes")

    admin_rows = db.run_query(
        "SELECT c.* FROM candidates c LEFT JOIN users u ON u.candidate_id = c.id WHERE u.id IS NULL ORDER BY c.uploaded_at DESC"
    )
    cand_rows = db.run_query(
        "SELECT u.id as user_id, u.username, u.candidate_id, c.name FROM users u JOIN candidates c ON u.candidate_id = c.id ORDER BY c.uploaded_at DESC"
    )

    admin_df = pd.DataFrame(admin_rows) if admin_rows else pd.DataFrame()

    cand_files = []
    if cand_rows:
        try:
            import candidate_pages as cand_mod
        except Exception:
            cand_mod = None

        for u in cand_rows:
            cid = u.get('candidate_id')
            name = u.get('name') or u.get('username')
            files_df = None
            if cand_mod:
                try:
                    files_df = cand_mod._list_candidate_uploads(cid)
                except Exception:
                    files_df = None

            if files_df is None or files_df.empty:
                rec = db.get_candidate(cid)
                if rec and rec.get('filename'):
                    cand_files.append({
                        'candidate_id': cid,
                        'name': name,
                        'filename': Path(rec.get('filename')).name,
                        'path': rec.get('filename'),
                        'uploaded_at': rec.get('uploaded_at')
                    })
                continue

            for _, fr in files_df.iterrows():
                vac_titles = []
                try:
                    apps = db.run_query(
                        "SELECT v.title FROM applications a JOIN vacancies v ON a.vacancy_id = v.id "
                        "WHERE a.candidate_id = %s AND (a.resume_filename = %s OR a.resume_filename = %s)",
                        (cid, fr['path'], fr['filename'])
                    )
                    if apps:
                        vac_titles = [r['title'] for r in apps if r.get('title')]
                except Exception:
                    vac_titles = []

               
                if not vac_titles:
                    try:
                        rec = db.get_candidate(cid)
                        rec_fn = rec.get('filename') if rec else None
                        if rec_fn and (rec_fn == fr['path'] or Path(rec_fn).name == fr['filename']):
                            apps2 = db.run_query(
                                "SELECT v.title FROM applications a JOIN vacancies v ON a.vacancy_id = v.id WHERE a.candidate_id = %s",
                                (cid,)
                            )
                            if apps2:
                                vac_titles = [r['title'] for r in apps2 if r.get('title')]
                    except Exception:
                        vac_titles = vac_titles or []

                cand_files.append({
                    'candidate_id': cid,
                    'name': name,
                    'filename': fr['filename'],
                    'path': fr['path'],
                    'uploaded_at': fr['uploaded_at'],
                    'vacancies': ', '.join(vac_titles) if vac_titles else ''
                })

    cand_df = pd.DataFrame(cand_files) if cand_files else pd.DataFrame()

    col_admin, col_cand = st.columns(2)
    with col_admin:
        st.subheader("Admin Uploads")
        if admin_df.empty:
            st.info("No admin uploads yet")
        else:
            st.dataframe(admin_df[["name", "filename", "uploaded_at"]], use_container_width=True, hide_index=True)

    with col_cand:
        st.subheader("Candidate Uploads")
        if cand_df.empty:
            st.info("No candidate uploads yet")
        else:
            display_cand = cand_df[["name", "filename", "vacancies"]].copy()
            display_cand.columns = ["Name", "Filename", "Vacancies Applied"]
            st.dataframe(display_cand, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Only allow deletion of admin-uploaded resumes (not candidate-linked records)
    admin_df = admin_df if isinstance(admin_df, pd.DataFrame) else pd.DataFrame()
    if admin_df.empty:
        st.info("No admin-uploaded resumes available for deletion")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        del_cand = st.selectbox(
            "Select admin-uploaded resume to delete",
            options=[0] + admin_df["id"].tolist(),
            format_func=lambda x: "-- Select --" if x == 0 else admin_df[admin_df["id"] == x]["name"].iloc[0],
            key="del_resume_select"
        )
    with col2:
        st.write(""); st.write("")
        if st.button("Delete Resume", type="secondary", use_container_width=True, key="del_resume_btn"):
            if del_cand != 0:
                st.session_state.pending_delete_cand = int(del_cand)
            else:
                st.warning("Please select a resume")

        if st.session_state.get('pending_delete_cand'):
            pending_id = st.session_state.pending_delete_cand
            if pending_id == del_cand:
                cand_rec = db.get_candidate(pending_id)
                name = cand_rec.get('name') if cand_rec else 'Unknown'
                st.warning(f"Delete resume of **{name}**?")
                coly, coln = st.columns([1,1])
                with coly:
                    if st.button("Yes", type="primary", key="confirm_del_resume"):
                        try:
                            res = db.delete_candidate(pending_id)
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
                            res = None

                        if not res:
                            apps = db.run_query("SELECT COUNT(*) as cnt FROM applications WHERE candidate_id=%s", (pending_id,))
                            cnt = apps[0]['cnt'] if apps else 0
                            if cnt > 0:
                                st.error("Cannot delete candidate: there are applications for this candidate. Remove applications first.")
                            else:
                                st.error("Failed to delete resume record. Check server logs.")
                        else:
                            try:
                                fn = cand_rec.get('filename') if cand_rec else None
                                if fn:
                                    p = Path(fn)
                                    if p.exists():
                                        p.unlink()
                            except Exception:
                                pass
                            st.success("Resume deleted!")
                            st.session_state.pop('pending_delete_cand', None)
                            st.rerun()
                with coln:
                    if st.button("Cancel", type="secondary", key="cancel_del_resume"):
                        del st.session_state['pending_delete_cand']
                        st.info("Deletion cancelled")


# ---------------------------------------------------------
# 4. RANKINGS
# ---------------------------------------------------------
def show_rankings():
    st.header("Candidate Rankings")
    
    cats = db.list_categories()
    if cats.empty:
        st.warning("No categories found. Please add categories first.")
        return

    selected_category = st.selectbox("Filter by Category", options=["All Categories"] + cats["name"].tolist())

    if selected_category == "All Categories":
        vacs = db.list_vacancies()
    else:
        vacs = db.list_vacancies()[db.list_vacancies()["category"] == selected_category]

    if vacs.empty:
        st.info(f"No vacancies in '{selected_category}'")
        return

    vacancy_options = vacs["title"] + " (" + vacs["category"] + ")"
    vacancy_map = dict(zip(vacancy_options, vacs["id"]))

    # Allow ranking across all vacancies in the selected category
    if selected_category != "All Categories":
        all_label = f"All Vacancies in {selected_category}"
        options_list = [all_label] + list(vacancy_map.keys())
        vacancy_map = {all_label: None, **vacancy_map}
    else:
        options_list = list(vacancy_map.keys())

    selected_display = st.selectbox("Select Vacancy", options=options_list)
    vacancy_id = vacancy_map[selected_display]

    st.markdown("---")

    with st.spinner("Computing latest AI rankings..."):
        # If a specific vacancy is selected, behave as before (compute & upsert)
        if vacancy_id is not None:
            vac = db.get_vacancy(vacancy_id)

            # Only consider candidates who applied to this vacancy
            apps = db.run_query(
                "SELECT c.* FROM applications a JOIN candidates c ON a.candidate_id = c.id WHERE a.vacancy_id = %s",
                (vacancy_id,)
            )
            if not apps:
                st.info("No applicants for this vacancy yet")
                return
            candidates = pd.DataFrame(apps)

            skills_list = [s.strip() for s in vac["skills"].split(",")] if vac["skills"] else []

            for _, row in candidates.iterrows():
                scores = compute_scores(
                    vac["description"],
                    row["extracted_text"] or "",
                    skills_list,
                    (vac["embedding_weight"], vac["skills_weight"], vac["other_weight"])
                )
                db.upsert_score(
                    row["id"], vacancy_id,
                    scores["embedding_score"], scores["skills_score"],
                    scores["other_score"], scores["total_score"]
                )

        else:
            # Category-level ranking: consider applicants to ANY vacancy in this category.
            vac_ids = vacs["id"].tolist()
            if not vac_ids:
                st.info("No vacancies in this category")
                return

            placeholders = ",".join(["%s"] * len(vac_ids))
            apps = db.run_query(
                f"SELECT c.*, a.vacancy_id FROM applications a JOIN candidates c ON a.candidate_id = c.id WHERE a.vacancy_id IN ({placeholders})",
                tuple(vac_ids)
            )
            if not apps:
                st.info("No applicants for this category yet")
                return

            apps_df = pd.DataFrame(apps)

            best = {}
            for _, arow in apps_df.iterrows():
                cand_id = arow["id"]
                vac_applied_id = arow["vacancy_id"]
                vac_rec = db.get_vacancy(vac_applied_id)
                skills_list = [s.strip() for s in vac_rec["skills"].split(",")] if vac_rec["skills"] else []
                scores = compute_scores(
                    vac_rec["description"],
                    arow["extracted_text"] or "",
                    skills_list,
                    (vac_rec["embedding_weight"], vac_rec["skills_weight"], vac_rec["other_weight"])
                )
                total = scores["total_score"]
                if cand_id not in best or total > best[cand_id]["total_score"]:
                    best[cand_id] = {
                        "id": cand_id,
                        "name": arow.get("name"),
                        "embedding_score": scores["embedding_score"],
                        "skills_score": scores["skills_score"],
                        "other_score": scores["other_score"],
                        "total_score": total,
                        "vacancy_id": vac_applied_id
                    }

            # Convert best dict to DataFrame for display
            df = pd.DataFrame(list(best.values()))
            if df.empty:
                st.info("No rankings available yet")
                return

            df = df.sort_values("total_score", ascending=False).reset_index(drop=True)
            df["rank"] = df.index + 1
            df["total_score_%"] = (df["total_score"] * 100).round(1).astype(str) + "%"
            df["skills_score_%"] = (df["skills_score"] * 100).round(1).astype(str) + "%"

            st.subheader(f"Rankings (best match per candidate) for {selected_category}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Applicants", len(df))
            c2.metric("Best Match", df.iloc[0]["total_score_%"])
            c3.metric("Average Match", f"{df['total_score'].mean()*100:.1f}%")

            st.markdown("---")

            display_df = df[["rank", "name", "total_score_%", "skills_score_%"]].copy()
            display_df.columns = ["Rank", "Candidate", "Overall Match (%)", "Skills Match (%)"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False).encode()
            st.download_button(
                "Download Rankings CSV",
                data=csv,
                file_name=f"ranking_{selected_category.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            return

    df = db.get_scores_for_vacancy(vacancy_id)
    if df.empty:
        st.info("No rankings available yet")
        return

    df = df.sort_values("total_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    df["total_score_%"] = (df["total_score"] * 100).round(1).astype(str) + "%"
    df["skills_score_%"] = (df["skills_score"] * 100).round(1).astype(str) + "%"

    st.subheader(f"Rankings: {selected_display.split(' (')[0]}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Applicants", len(df))
    c2.metric("Best Match", df.iloc[0]["total_score_%"])
    c3.metric("Average Match", f"{df['total_score'].mean()*100:.1f}%")

    st.markdown("---")

    display_df = df[["rank", "name", "total_score_%", "skills_score_%"]].copy()
    display_df.columns = ["Rank", "Candidate", "Overall Match (%)", "Skills Match (%)"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode()
    st.download_button(
        "Download Rankings CSV",
        data=csv,
        file_name=f"ranking_{selected_display.replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True
    )

    # --------------------
    # Admin-uploaded resumes: custom rankings panel (shown below candidate rankings)
    # --------------------
    st.markdown("---")
    st.subheader("Admin-uploaded Resumes — Custom Rankings")

    admin_rows = db.run_query(
        "SELECT c.* FROM candidates c LEFT JOIN users u ON u.candidate_id = c.id WHERE u.id IS NULL ORDER BY c.uploaded_at DESC"
    )
    admin_df = pd.DataFrame(admin_rows) if admin_rows else pd.DataFrame()
    if admin_df.empty:
        st.info("No admin-uploaded resumes available for custom ranking")
    else:
        admin_options = []
        admin_map = {}
        for _, r in admin_df.iterrows():
            label = f"{r.get('name')} ({r.get('id')})"
            admin_options.append(label)
            admin_map[label] = int(r.get('id'))

        selected_admin_labels = st.multiselect("Select admin-uploaded resumes to evaluate", options=admin_options)

        admin_category = st.selectbox("Select Category for Admin Resume Evaluation", options=["All Categories"] + cats["name"].tolist())
        if admin_category == "All Categories":
            admin_vacs = db.list_vacancies()
        else:
            admin_vacs = db.list_vacancies()[db.list_vacancies()["category"] == admin_category]

        if admin_vacs.empty:
            st.info("No vacancies for selected category")
        else:
            admin_vac_options = admin_vacs["title"] + " (" + admin_vacs["category"] + ")"
            admin_vac_map = dict(zip(admin_vac_options, admin_vacs["id"]))
            admin_selected_display = st.selectbox("Select Vacancy for Admin Resume Evaluation", options=list(admin_vac_map.keys()))
            admin_vacancy_id = admin_vac_map[admin_selected_display]

            if st.button("Compute Selected Admin Resume Rankings", type="primary", use_container_width=True, key="compute_admin_rankings_bottom"):
                if not selected_admin_labels:
                    st.warning("Please select at least one admin-uploaded resume to evaluate")
                else:
                    rows = []
                    vac_rec = db.get_vacancy(admin_vacancy_id)
                    skills_list = [s.strip() for s in vac_rec["skills"].split(",")] if vac_rec["skills"] else []
                    for lbl in selected_admin_labels:
                        cid = admin_map.get(lbl)
                        rec = db.get_candidate(cid)
                        if not rec:
                            continue
                        scores = compute_scores(
                            vac_rec["description"],
                            rec.get("extracted_text") or "",
                            skills_list,
                            (vac_rec["embedding_weight"], vac_rec["skills_weight"], vac_rec["other_weight"]) 
                        )
                        rows.append({
                            "id": rec.get("id"),
                            "name": rec.get("name"),
                            "embedding_score": scores["embedding_score"],
                            "skills_score": scores["skills_score"],
                            "other_score": scores["other_score"],
                            "total_score": scores["total_score"]
                        })

                    out_df = pd.DataFrame(rows)
                    if out_df.empty:
                        st.info("No scores computed for selected resumes")
                    else:
                        out_df = out_df.sort_values("total_score", ascending=False).reset_index(drop=True)
                        out_df["rank"] = out_df.index + 1
                        out_df["total_score_%"] = (out_df["total_score"] * 100).round(1).astype(str) + "%"
                        out_df["skills_score_%"] = (out_df["skills_score"] * 100).round(1).astype(str) + "%"

                        st.markdown("---")
                        st.subheader(f"Admin Selected Resumes — Rankings for {vac_rec['title']}")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Selected Resumes", len(out_df))
                        c2.metric("Best Match", out_df.iloc[0]["total_score_%"]) if len(out_df) > 0 else None
                        c3.metric("Average Match", f"{out_df['total_score'].mean()*100:.1f}%" if len(out_df) > 0 else "0%")

                        display_df = out_df[["rank", "name", "total_score_%", "skills_score_%"]].copy()
                        display_df.columns = ["Rank", "Candidate", "Overall Match (%)", "Skills Match (%)"]
                        st.dataframe(display_df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# 5. DASHBOARD
# ---------------------------------------------------------
def show_dashboard():
    st.header("Admin Dashboard")
    v = len(db.list_vacancies())
    c_row = db.run_query("SELECT COUNT(DISTINCT candidate_id) as cnt FROM applications")
    c = c_row[0]["cnt"] if c_row else 0
    a = db.run_query("SELECT COUNT(*) as cnt FROM applications")
    apps = a[0]["cnt"] if a else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Vacancies", v)
    col2.metric("Unique Applicants", c)
    col3.metric("Applications", apps)

    st.markdown("---")

    st.subheader("Applicants by Vacancy")
    vacs = db.list_vacancies()
    if vacs.empty:
        st.info("No vacancies available")
    else:
        vac_opts = vacs["title"] + " (" + vacs["category"] + ")"
        vac_map = dict(zip(vac_opts, vacs["id"]))
        sel_vac_display = st.selectbox("Select Vacancy to view applicants", options=["-- Select --"] + list(vac_map.keys()))
        if sel_vac_display and sel_vac_display != "-- Select --":
            sel_vac_id = vac_map[sel_vac_display]
            apps_rows = db.run_query(
                "SELECT a.id as app_id, c.id as candidate_id, c.name, COALESCE(a.resume_filename, c.filename) as filename, a.applied_at, u.email as email "
                "FROM applications a "
                "JOIN candidates c ON a.candidate_id = c.id "
                "LEFT JOIN users u ON u.candidate_id = c.id "
                "WHERE a.vacancy_id = %s ORDER BY a.applied_at DESC",
                (sel_vac_id,)
            )
            if not apps_rows:
                st.info("No applicants for this vacancy yet")
            else:
                apps_df = pd.DataFrame(apps_rows)
                st.markdown(f"**Total applicants:** {len(apps_df)}")
                display = apps_df[["candidate_id", "name", "email", "filename", "applied_at"]].copy()
                display.columns = ["Candidate ID", "Name", "Email", "Resume", "Applied At"]
                st.dataframe(display, use_container_width=True)
                csv = apps_df.to_csv(index=False).encode()
                st.download_button("Download Applicants CSV", data=csv, file_name=f"applicants_{sel_vac_id}.csv", mime="text/csv")

    st.success("Welcome back, Admin! Everything is under control.")
