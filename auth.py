# auth.py - Unified Authentication System
import streamlit as st
from pathlib import Path
from extract_text import extract_text
import db

def init_session_state():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.candidate_id = None

def login_page():
    """Display unified login and registration page"""
    st.markdown('<h1 class="big-title"> AI Resume Analyzer</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs([" Login", " Registeration"])
        
        # ==================== UNIFIED LOGIN TAB ====================
        with tab1:
            st.caption("Enter your credentials to continue")
            
            with st.form("unified_login", clear_on_submit=False):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", placeholder="Enter your password", type="password")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    login_btn = st.form_submit_button("Login", use_container_width=True)
               
                
                if login_btn:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        user = db.get_user(username)
                        
                        if user and user['password'] == password:
                            st.session_state.logged_in = True
                            st.session_state.role = user['role']
                            st.session_state.username = username
                            
                            if user['role'] == 'candidate':
                                st.session_state.candidate_id = user['candidate_id']
                            
                            st.success(f"Welcome {username}!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
            
            
        # ==================== REGISTRATION TAB ====================
        with tab2:
            st.markdown("### Create Candidate Account")
            st.caption("Register to start applying for jobs")
            
            with st.form("register", clear_on_submit=True):
                reg_user = st.text_input("Choose Username", placeholder="e.g., john_doe")
                reg_pass = st.text_input("Choose Password", placeholder="Minimum 6 characters", type="password")
                reg_pass_confirm = st.text_input("Confirm Password", placeholder="Re-enter password", type="password")
                reg_name = st.text_input("Full Name", placeholder="e.g., John Doe")
                reg_email = st.text_input("Email", placeholder="name@example.com")
                reg_file = st.file_uploader("Upload Resume (Optional)", type=['pdf','docx','txt'], 
                                           help="Upload your resume now or later")
                
                if st.form_submit_button(" Register", use_container_width=True):
                    # Validation
                    if not reg_user or not reg_pass or not reg_name or not reg_email:
                        st.error("Username, password, full name, and email are required")
                    elif '@' not in reg_email or '.' not in reg_email:
                        st.error("Please enter a valid email address")
                    elif len(reg_pass) < 6:
                        st.error("Password must be at least 6 characters")
                    elif reg_pass != reg_pass_confirm:
                        st.error(" Passwords do not match")
                    elif db.get_user(reg_user):
                        st.error(f"Username '{reg_user}' already exists")
                    else:
                        resume_text = ""
                        filename = "not_uploaded"
                        
                        if reg_file:
                            temp_path = Path("uploads") / reg_file.name
                            temp_path.parent.mkdir(exist_ok=True)
                            with open(temp_path, "wb") as f:
                                f.write(reg_file.getbuffer())
                            try:
                                resume_text = extract_text(str(temp_path))
                                filename = str(temp_path)
                            except Exception as e:
                                st.warning(f" Could not extract text from resume: {e}")
                        
                        try:
                            cid = db.add_candidate(reg_name, filename, resume_text)
                            db.register_user(reg_user, reg_pass, 'candidate', cid, reg_email)
                            st.success(f" Registration successful! Welcome {reg_name}!")
                            st.info("Please login with your credentials from the Login tab")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Registration failed: {e}")
            
            st.markdown("---")
            st.caption("You can upload your resume now or after registration")

def logout():
    """Logout and clear session"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()