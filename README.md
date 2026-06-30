
# 🤖 AI Resume Analyzer
 
An intelligent resume screening and job-matching system built with Python and Streamlit. Uses **NLP and sentence embeddings** to semantically match candidate resumes against job descriptions — helping recruiters rank applicants and helping candidates find their best-fit roles.
 
---

## 📸 Screenshots
 
| Admin Dashboard | Candidate Portal |
|---|---|
| Manage vacancies, categories, upload resumes, view ranked applicants | Browse jobs, upload resume, get instant AI match score |
 
---
 
## ✨ Features
 
### 🔐 Authentication System
- Role-based login: **Admin** and **Candidate** roles
- Candidate self-registration with optional resume upload
- Session-based auth with Streamlit state management
### 🧠 AI Matching Engine (`ai_model.py`)
- **Semantic similarity** using `sentence-transformers` (`all-MiniLM-L6-v2`)
- **Skill overlap scoring** — robust NLP matching (handles punctuation, multi-word skills, substrings)
- **Weighted composite scoring**: configurable weights for embedding score, skill score, and other factors
- `detect_skills()` — identifies found vs. missing skills from resume text
### 👤 Candidate Portal
- Upload resume (PDF, DOCX, TXT)
- Browse open job vacancies by category
- Get instant **AI match score** per job with skill gap analysis
- View all applications, withdraw anytime
- Download full match report as CSV
### 🛠️ Admin Panel
- **Category Management** — create/delete job categories
- **Vacancy Management** — post jobs with description, required skills, and custom AI weights
- **Resume Upload** — bulk upload candidate resumes directly
- **Rankings** — view AI-ranked applicants per vacancy with exportable CSV
- **Dashboard** — overview of vacancies, applicants, and total applications
### 📄 Resume Parsing (`extract_text.py`)
- Supports `.pdf` (via `pdfminer.six`), `.docx` (via `python-docx`), `.txt`
- Extracts raw text for NLP processing
---
 
---
 
## 🧪 Tech Stack
 
| Layer | Technology |
|---|---|
| **Frontend / UI** | Streamlit |
| **NLP / AI** | sentence-transformers (`all-MiniLM-L6-v2`), NLTK |
| **Resume Parsing** | pdfminer.six, python-docx |
| **Database** | MySQL with connection pooling |
| **Data Processing** | Pandas, scikit-learn |
| **Language** | Python 3.10+ |
 
---
 
## ⚙️ How the AI Scoring Works
 
Each resume is scored against a job description using a **weighted composite**:
 
```
Total Score = (w1 × Embedding Score) + (w2 × Skill Score) + (w3 × Other Score)
```
 
- **Embedding Score** — cosine similarity between job description and resume using sentence embeddings (normalized 0–1)
- **Skill Score** — fraction of required skills found in resume (phrase + token matching)
- **Other Score** — placeholder for education/experience scoring (extensible)
Weights are configurable per vacancy by the admin (must sum to 1.0).
 
---

## 📦 Requirements
 
```
streamlit
sentence-transformers
pdfminer.six
python-docx
pandas
openpyxl
nltk
scikit-learn
mysql-connector-python
```
 
---
## 👩‍💻 Author
 
**Malaika Fatima**  
