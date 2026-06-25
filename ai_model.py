# ai_model.py
import re
import string
import nltk
from sentence_transformers import SentenceTransformer, util

# Ensure punkt tokenizer is present
try:
    nltk.data.find('tokenizers/punkt')
except:
    nltk.download('punkt')

# Load a small, fast sentence embedding model
MODEL = SentenceTransformer('all-MiniLM-L6-v2')


def normalize_text(text: str) -> str:
    """
    Lowercase, remove extra spaces and line breaks
    """
    text = text.lower()
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def embed_text(text: str):
    """
    Return tensor embedding of text
    """
    return MODEL.encode(text, convert_to_tensor=True)


def semantic_similarity(a: str, b: str) -> float:
    """
    Returns cosine similarity in range [-1, 1]
    """
    emb_a = embed_text(a)
    emb_b = embed_text(b)
    score = util.cos_sim(emb_a, emb_b).item()
    return float(score)


def skill_overlap_score(skills_required: list, resume_text: str) -> float:
    """
    Robust skill overlap score:
    - case-insensitive
    - ignores punctuation
    - substring match
    Returns fraction of required skills found in resume
    """
    import re

    if not skills_required:
        return 0.0

    # Lowercase resume and create a cleaned version where punctuation becomes spaces
    rt = resume_text.lower()
    rt_clean = re.sub(r"[^\w\+]+", " ", rt)
    resume_tokens = set(t for t in rt_clean.split() if t)

    found = 0
    for s in skills_required:
        if not s:
            continue
        s_norm = s.lower()
        # Normalize skill phrase similarly (punctuation -> space)
        s_clean = re.sub(r"[^\w\+]+", " ", s_norm).strip()
        if not s_clean:
            continue

        # First try exact phrase match on cleaned resume (word boundaries)
        phrase = r"\b" + re.escape(s_clean) + r"\b"
        if re.search(phrase, rt_clean):
            found += 1
            continue

        # Otherwise, split skill into tokens and see if any token appears in resume tokens
        tokens = [t for t in s_clean.split() if t]
        # Require all tokens of the skill to appear (full-word match)
        if tokens and all(tok in resume_tokens for tok in tokens):
            found += 1
            continue

    return found / len(skills_required)


def detect_skills(skills_required: list, resume_text: str):
    """Return (found_skills, missing_skills) lists using the same logic
    as skill_overlap_score so UI and scoring are consistent.
    """
    import re

    if not skills_required:
        return [], []

    rt = resume_text.lower()
    rt_clean = re.sub(r"[^\w\+]+", " ", rt)
    resume_tokens = set(t for t in rt_clean.split() if t)

    found = []
    missing = []
    for s in skills_required:
        if not s:
            continue
        s_norm = s.lower()
        s_clean = re.sub(r"[^\w\+]+", " ", s_norm).strip()
        if not s_clean:
            continue

        phrase = r"\b" + re.escape(s_clean) + r"\b"
        if re.search(phrase, rt_clean):
            found.append(s)
            continue

        tokens = [t for t in s_clean.split() if t]
        # Require all tokens of the skill to appear (full-word match)
        if tokens and all(tok in resume_tokens for tok in tokens):
            found.append(s)
            continue

        missing.append(s)

    return found, missing


def compute_scores(jd_text: str, resume_text: str, skills_required: list,
                   weights=(0.4, 0.3, 0.3)):
    """
    Compute embedding, skills, and other scores.
    Returns dict with individual scores and decimal-safe weighted total_score.

    weights: tuple of (embedding_weight, skills_weight, other_weight)
    - Set weights=(0.0, 1.0, 0.0) for skill-score-only ranking
    """
    # Embedding similarity normalized to 0..1
    emb_raw = semantic_similarity(jd_text, resume_text)  # -1..1
    emb_score = (emb_raw + 1) / 2.0

    # Skills overlap score (robust)
    skills_score = skill_overlap_score(skills_required, resume_text)

    # Placeholder for other score (education/experience)
    other_score = 0.0

    # Ensure decimal-safe float multiplication
    w_emb, w_sk, w_other = map(float, weights)
    emb_score = float(emb_score)
    skills_score = float(skills_score)
    other_score = float(other_score)

    total = w_emb * emb_score + w_sk * skills_score + w_other * other_score

    return {
        "embedding_raw": emb_raw,
        "embedding_score": emb_score,
        "skills_score": skills_score,
        "other_score": other_score,
        "total_score": total
    }
