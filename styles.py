import streamlit as st

def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .main > .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1200px;
        }

        .main {
            background-color: #f8fafc;
        }

        .big-title {
            font-size: 2.8rem;
            font-weight: 700;
            color: #1e293b;
            text-align: center;
            margin: 2rem 0 3rem 0;
            letter-spacing: -0.5px;
        }

        .card {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin: 1.5rem 0;
            transition: all 0.2s ease;
        }

        .card:hover {
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            transform: translateY(-2px);
        }

        div.stForm {
            background: white;
            padding: 2.5rem;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            max-width: 480px;
            margin: 2rem auto;
        }

        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 10px !important;
            border: 1.5px solid #cbd5e1 !important;
            padding: 0.85rem 1rem !important;
            font-size: 1rem !important;
            transition: all 0.2s ease !important;
        }

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
            outline: none !important;
        }

        .stTextInput > label,
        .stTextArea > label,
        .stSelectbox > label {
            font-weight: 600 !important;
            color: #334155 !important;
            font-size: 0.95rem !important;
            margin-bottom: 0.5rem !important;
        }

        .stButton > button {
            background-color: #3b82f6;
            color: white;
            font-weight: 600;
            font-size: 1rem;
            padding: 0.75rem 2rem;
            border-radius: 10px;
            border: none;
            width: 100%;
            height: 48px;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
        }

        .stButton > button:hover {
            background-color: #2563eb;
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(59, 130, 246, 0.3);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 1.1rem;
            font-weight: 600;
            color: #64748b;
            padding: 0.5rem 0;
        }

        .stTabs [aria-selected="true"] {
            color: #3b82f6 !important;
            border-bottom: 3px solid #3b82f6 !important;
        }

        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
            color: white !important;
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: white !important;
        }

        [data-testid="stSidebar"] .stRadio label {
            color: #f8fafc !important;
            font-weight: 500;
        }

        [data-testid="stSidebar"] .stRadio label:hover {
            color: #60a5fa !important;
        }

        [data-testid="stSidebar"] .stRadio [aria-checked="true"] label {
            color: #3b82f6 !important;
            font-weight: 700 !important;
        }

        [data-testid="stFileUploader"] {
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            padding: 2rem;
            background-color: #f8fafc;
        }

        .stAlert {
            border-radius: 10px;
            padding: 1rem 1.2rem;
        }

        .dataframe {
            border-radius: 12px !important;
            border: 1px solid #e2e8f0 !important;
        }

        ::-webkit-scrollbar {
            width: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #1e293b;
        }
        ::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 4px;
        }

        * {
            animation: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
