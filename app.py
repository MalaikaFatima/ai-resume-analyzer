# # app.py - Enhanced Version with Better UI and Error Handling
# import streamlit as st
# from pathlib import Path
# import pandas as pd
# from extract_text import extract_text
# from ai_model import compute_scores
# import db
# import traceback

# # Configuration
# UPLOADS = Path("uploads")
# UPLOADS.mkdir(exist_ok=True, parents=True)

# # Page config
# st.set_page_config(
#     page_title="AI HR Resume Analyzer",
#     page_icon="📄",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS for better UI
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         font-weight: bold;
#         color: #1f77b4;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
#     .sub-header {
#         font-size: 1.5rem;
#         color: #2c3e50;
#         margin-top: 1rem;
#         margin-bottom: 1rem;
#     }
#     .stButton>button {
#         width: 100%;
#         background-color: #1f77b4;
#         color: white;
#         border-radius: 5px;
#         padding: 0.5rem 1rem;
#     }
#     .stButton>button:hover {
#         background-color: #145a8a;
#     }
#     .metric-card {
#         background-color: #f0f2f6;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin: 0.5rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Title
# st.markdown('<p class="main-header">🎯 AI Resume Analyzer — HR Module</p>', unsafe_allow_html=True)

# # Sidebar menu
# menu = st.sidebar.selectbox(
#     "📋 Navigation Menu",
#     ["🏢 Vacancy Management", "📤 Upload Resumes", "🏆 Rank Candidates", "📊 Dashboard"]
# )

# # ==================== VACANCY MANAGEMENT ====================
# if menu == "🏢 Vacancy Management":
#     st.markdown('<p class="sub-header">Manage Job Vacancies</p>', unsafe_allow_html=True)
    
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         with st.form("vacancy_form", clear_on_submit=True):
#             st.subheader("➕ Add New Vacancy")
#             title = st.text_input("Job Title *", placeholder="e.g., Senior Software Engineer")
#             description = st.text_area(
#                 "Job Description / JD *",
#                 placeholder="Enter detailed job description here...",
#                 height=150
#             )
#             skills_raw = st.text_input(
#                 "Required Skills (comma separated) *",
#                 placeholder="e.g., Python, Machine Learning, SQL"
#             )
            
#             st.markdown("**Scoring Weights (must sum to 1.0)**")
#             col_w1, col_w2, col_w3 = st.columns(3)
#             with col_w1:
#                 we = st.number_input("Semantic Match", min_value=0.0, max_value=1.0, value=0.4, step=0.05)
#             with col_w2:
#                 ws = st.number_input("Skills Match", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
#             with col_w3:
#                 wo = st.number_input("Other Criteria", min_value=0.0, max_value=1.0, value=0.3, step=0.05)
            
#             submitted = st.form_submit_button("✅ Add Vacancy")
            
#             if submitted:
#                 # Validation
#                 if not title.strip():
#                     st.error("❌ Job Title is required!")
#                 elif not description.strip():
#                     st.error("❌ Job Description is required!")
#                 elif not skills_raw.strip():
#                     st.error("❌ Required Skills are required!")
#                 elif abs((we + ws + wo) - 1.0) > 0.01:
#                     st.error(f"❌ Weights must sum to 1.0 (current: {we + ws + wo:.2f})")
#                 else:
#                     skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
#                     try:
#                         db.add_vacancy(title, description, skills, we, ws, wo)
#                         st.success(f"✅ Vacancy '{title}' added successfully!")
#                         st.rerun()
#                     except Exception as e:
#                         st.error(f"❌ Database error: {str(e)}")
    
#     with col2:
#         st.info("💡 **Tips:**\n\n"
#                 "- Be specific in job descriptions\n"
#                 "- List skills clearly\n"
#                 "- Adjust weights based on priority\n"
#                 "- Semantic: Overall JD match\n"
#                 "- Skills: Exact skill matches\n"
#                 "- Other: Future expansion")
    
#     st.markdown("---")
#     st.markdown('<p class="sub-header">📋 Existing Vacancies</p>', unsafe_allow_html=True)
    
#     vac_df = db.list_vacancies()
#     if not vac_df.empty:
#         # Display with better formatting
#         display_df = vac_df[['id', 'title', 'skills', 'embedding_weight', 'skills_weight', 'other_weight', 'created_at']]
#         display_df.columns = ['ID', 'Job Title', 'Skills', 'Semantic Wt', 'Skills Wt', 'Other Wt', 'Created']
#         st.dataframe(display_df, use_container_width=True)
        
#         # Delete functionality
#         col_del1, col_del2 = st.columns([3, 1])
#         with col_del1:
#             del_id = st.selectbox("Select Vacancy to Delete", options=[0] + vac_df['id'].tolist(), format_func=lambda x: "Select..." if x == 0 else f"ID {x} - {vac_df[vac_df['id']==x]['title'].values[0]}")
#         with col_del2:
#             st.write("")
#             st.write("")
#             if st.button("🗑️ Delete", use_container_width=True):
#                 if del_id > 0:
#                     try:
#                         conn = db.get_conn()
#                         cur = conn.cursor()
#                         cur.execute("DELETE FROM vacancies WHERE id=%s", (del_id,))
#                         conn.commit()
#                         conn.close()
#                         st.success(f"✅ Deleted vacancy ID {del_id}")
#                         st.rerun()
#                     except Exception as e:
#                         st.error(f"❌ Error: {str(e)}")
#                 else:
#                     st.warning("⚠️ Please select a vacancy to delete")
#     else:
#         st.info("📭 No vacancies yet. Add one using the form above.")

# # ==================== UPLOAD RESUMES ====================
# elif menu == "📤 Upload Resumes":
#     st.markdown('<p class="sub-header">Upload Candidate Resumes</p>', unsafe_allow_html=True)
    
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         uploaded_files = st.file_uploader(
#             "📁 Select Resume Files",
#             accept_multiple_files=True,
#             type=['pdf', 'docx', 'txt'],
#             help="Upload one or multiple resume files (PDF, DOCX, or TXT)"
#         )
#         name_input = st.text_input(
#             "Candidate Name (optional)",
#             placeholder="Leave empty to use filename",
#             help="If uploading multiple files, filename will be used as name"
#         )
        
#         if st.button("💾 Save Uploads", use_container_width=True):
#             if not uploaded_files:
#                 st.warning("⚠️ Please upload at least one file.")
#             else:
#                 progress_bar = st.progress(0)
#                 status_text = st.empty()
                
#                 for idx, f in enumerate(uploaded_files):
#                     status_text.text(f"Processing {idx+1}/{len(uploaded_files)}: {f.name}")
                    
#                     save_path = UPLOADS / f.name
#                     with open(save_path, "wb") as out:
#                         out.write(f.getbuffer())
                    
#                     try:
#                         text = extract_text(str(save_path))
#                         if not text.strip():
#                             st.warning(f"⚠️ No text extracted from {f.name}")
#                             text = ""
#                     except Exception as e:
#                         st.error(f"❌ Failed to extract text from {f.name}: {str(e)}")
#                         text = ""
                    
#                     candidate_name = name_input.strip() if name_input.strip() else f.name.rsplit(".", 1)[0]
                    
#                     try:
#                         cid = db.add_candidate(candidate_name, str(save_path), text)
#                         st.success(f"✅ Saved: {candidate_name} (ID: {cid})")
#                     except Exception as e:
#                         st.error(f"❌ Database error for {candidate_name}: {str(e)}")
                    
#                     progress_bar.progress((idx + 1) / len(uploaded_files))
                
#                 status_text.text("✅ All files processed!")
#                 st.balloons()
#                 st.rerun()
    
#     with col2:
#         st.info("📌 **Supported Formats:**\n\n"
#                 "- PDF (.pdf)\n"
#                 "- Word (.docx)\n"
#                 "- Text (.txt)\n\n"
#                 "**Tips:**\n"
#                 "- Ensure files are readable\n"
#                 "- Avoid scanned PDFs\n"
#                 "- Use clear formatting")
    
#     st.markdown("---")
#     st.markdown('<p class="sub-header">📊 Uploaded Candidates</p>', unsafe_allow_html=True)
    
#     cand_df = db.list_candidates()
#     if not cand_df.empty:
#         display_df = cand_df[['id', 'name', 'filename', 'uploaded_at']]
#         display_df.columns = ['ID', 'Name', 'Filename', 'Upload Date']
#         st.dataframe(display_df, use_container_width=True)
        
#         st.metric("Total Candidates", len(cand_df))
#     else:
#         st.info("📭 No candidates uploaded yet.")

# # ==================== RANK CANDIDATES ====================
# elif menu == "🏆 Rank Candidates":
#     st.markdown('<p class="sub-header">Rank Candidates for Vacancy</p>', unsafe_allow_html=True)
    
#     vac_df = db.list_vacancies()
#     if vac_df.empty:
#         st.warning("⚠️ No vacancies found. Please create a vacancy first.")
#     else:
#         vac_options = {row['id']: row for _, row in vac_df.iterrows()}
#         vac_id = st.selectbox(
#             "Select Vacancy",
#             options=list(vac_options.keys()),
#             format_func=lambda x: f"🎯 {vac_options[x]['title']}"
#         )
        
#         vacancy = vac_options[vac_id]
        
#         col1, col2 = st.columns([2, 1])
        
#         with col1:
#             st.markdown(f"### 📄 {vacancy['title']}")
#             st.text_area("Job Description", value=vacancy['description'] or "", height=120, disabled=True)
        
#         with col2:
#             skills_req = [s.strip() for s in (vacancy['skills'] or "").split(",") if s.strip()]
#             st.markdown("**Required Skills:**")
#             for skill in skills_req:
#                 st.markdown(f"- ✅ {skill}")
#             if not skills_req:
#                 st.info("No skills specified")
        
#         st.markdown("---")
        
#         cand_df = db.list_candidates()
#         if cand_df.empty:
#             st.info("📭 No candidates uploaded yet.")
#         else:
#             col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
            
#             with col_btn1:
#                 if st.button("🔄 Compute Scores and Rank All Candidates", use_container_width=True):
#                     progress_bar = st.progress(0)
#                     status_text = st.empty()
                    
#                     for idx, (_, c) in enumerate(cand_df.iterrows()):
#                         status_text.text(f"Scoring {idx+1}/{len(cand_df)}: {c['name']}")
                        
#                         resume_text = c['extracted_text'] or ""
#                         jd_text = vacancy['description'] or ""
                        
#                         if not jd_text.strip():
#                             st.error("❌ Job description is empty! Cannot compute scores.")
#                             break
                        
#                         weights = (
#                             vacancy['embedding_weight'],
#                             vacancy['skills_weight'],
#                             vacancy['other_weight']
#                         )
                        
#                         try:
#                             res = compute_scores(jd_text, resume_text, skills_req, weights)
#                             db.upsert_score(
#                                 c['id'], vac_id,
#                                 res['embedding_score'],
#                                 res['skills_score'],
#                                 res['other_score'],
#                                 res['total_score']
#                             )
#                         except Exception as e:
#                             st.error(f"❌ Error scoring {c['name']}: {str(e)}")
#                             st.code(traceback.format_exc())
                        
#                         progress_bar.progress((idx + 1) / len(cand_df))
                    
#                     status_text.text("✅ All scores computed!")
#                     st.success("✅ Scoring complete!")
#                     st.rerun()
            
#             scores_df = db.get_scores_for_vacancy(vac_id)
            
#             if scores_df.empty:
#                 st.info("ℹ️ No scores yet. Click 'Compute Scores' button to generate rankings.")
#             else:
#                 st.markdown('<p class="sub-header">🏆 Ranked Candidates</p>', unsafe_allow_html=True)
                
#                 # Display with better formatting
#                 display_scores = scores_df.copy()
#                 display_scores['embedding_score'] = display_scores['embedding_score'].apply(lambda x: f"{x:.2%}")
#                 display_scores['skills_score'] = display_scores['skills_score'].apply(lambda x: f"{x:.2%}")
#                 display_scores['other_score'] = display_scores['other_score'].apply(lambda x: f"{x:.2%}")
#                 display_scores['total_score'] = display_scores['total_score'].apply(lambda x: f"{x:.2%}")
#                 display_scores.columns = ['Candidate ID', 'Name', 'Semantic Match', 'Skills Match', 'Other', 'Total Score']
                
#                 st.dataframe(display_scores, use_container_width=True)
                
#                 # Export options
#                 col_exp1, col_exp2 = st.columns(2)
#                 with col_exp1:
#                     csv = scores_df.to_csv(index=False)
#                     st.download_button(
#                         "📥 Download CSV",
#                         data=csv,
#                         file_name=f"ranked_vacancy_{vac_id}_{vacancy['title']}.csv",
#                         mime="text/csv",
#                         use_container_width=True
#                     )
                
#                 # Top candidate highlight
#                 st.markdown("---")
#                 top = scores_df.iloc[0]
#                 col_top1, col_top2, col_top3 = st.columns(3)
#                 with col_top1:
#                     st.metric("🥇 Top Candidate", top['name'])
#                 with col_top2:
#                     st.metric("Total Score", f"{top['total_score']:.2%}")
#                 with col_top3:
#                     st.metric("Skills Match", f"{top['skills_score']:.2%}")

# # ==================== DASHBOARD ====================
# elif menu == "📊 Dashboard":
#     st.markdown('<p class="sub-header">System Overview</p>', unsafe_allow_html=True)
    
#     vac_df = db.list_vacancies()
#     cand_df = db.list_candidates()
    
#     col1, col2, col3 = st.columns(3)
    
#     with col1:
#         st.markdown('<div class="metric-card">', unsafe_allow_html=True)
#         st.metric("🏢 Total Vacancies", len(vac_df))
#         st.markdown('</div>', unsafe_allow_html=True)
    
#     with col2:
#         st.markdown('<div class="metric-card">', unsafe_allow_html=True)
#         st.metric("👥 Total Candidates", len(cand_df))
#         st.markdown('</div>', unsafe_allow_html=True)
    
#     with col3:
#         st.markdown('<div class="metric-card">', unsafe_allow_html=True)
#         # Count scored candidates
#         conn = db.get_conn()
#         if conn:
#             cur = conn.cursor()
#             cur.execute("SELECT COUNT(DISTINCT candidate_id) FROM scores")
#             scored = cur.fetchone()[0]
#             conn.close()
#             st.metric("✅ Scored Candidates", scored)
#         st.markdown('</div>', unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     if not vac_df.empty:
#         st.markdown("### Recent Vacancies")
#         recent_vac = vac_df.sort_values('created_at', ascending=False).head(5)
#         for _, row in recent_vac.iterrows():
#             st.markdown(f"**{row['title']}** - Created: {row['created_at']}")
    
#     if not cand_df.empty:
#         st.markdown("### Recent Candidates")
#         recent_cand = cand_df.sort_values('uploaded_at', ascending=False).head(5)
#         for _, row in recent_cand.iterrows():
#             st.markdown(f"**{row['name']}** - Uploaded: {row['uploaded_at']}")

# main_app.py - Unified AI Resume Analyzer Platform
# main_app.py - FINAL 100% WORKING VERSION