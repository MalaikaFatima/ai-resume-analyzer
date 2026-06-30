# main.py - Main Application Entry Point

import streamlit as st
from auth import init_session_state, login_page, logout
from styles import load_css
import admin_pages
import candidate_pages

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Resume Analyzer Pro",
    page_icon="📄",
    layout="wide"
)

# ---------------------------------------------------------
# LOAD GLOBAL STYLES
# ---------------------------------------------------------
load_css()

# ---------------------------------------------------------
# INITIALIZE SESSION STATE
# ---------------------------------------------------------
init_session_state()

# ---------------------------------------------------------
# AUTHENTICATION CHECK
# ---------------------------------------------------------
if not st.session_state.logged_in:
    login_page()
    st.stop()

# ---------------------------------------------------------
# SIDEBAR MENU
# ---------------------------------------------------------
with st.sidebar:
    st.title(f"User: {st.session_state.username}")
    st.caption(f"Role: {st.session_state.role.upper()}")
    st.markdown("---")

    # Menu Options based on Role
    if st.session_state.role == "admin":
        page = st.radio(
            "Menu",
            ["Categories", "Vacancies", "Upload Resumes", "Rankings", "Dashboard"],
            label_visibility="collapsed"  # clean look
        )
    else:
        page = st.radio(
            "Menu",
            ["Browse Jobs", "My Applications"],
            label_visibility="collapsed"
        )

    st.markdown("---")
    # Logout Button (always stays at the bottom)
    if st.button("Logout", use_container_width=True, type="primary"):
        logout()

# ---------------------------------------------------------
# PAGE ROUTING BASED ON ROLE
# ---------------------------------------------------------
if st.session_state.role == "admin":
    if page == "Categories":
        admin_pages.show_categories()
    elif page == "Vacancies":
        admin_pages.show_vacancies()
    elif page == "Upload Resumes":
        admin_pages.show_upload_resumes()
    elif page == "Rankings":
        admin_pages.show_rankings()
    elif page == "Dashboard":
        admin_pages.show_dashboard()

else:  # Candidate Side Pages
    if page == "Browse Jobs":
        candidate_pages.show_browse_jobs()
   
    elif page == "My Applications":
        candidate_pages.show_my_applications()
