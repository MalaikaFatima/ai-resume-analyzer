# import mysql.connector
# from mysql.connector import Error, pooling
# import pandas as pd
# from typing import Optional, List, Tuple, Union

# connection_pool = None

# def init_pool():
#     global connection_pool
#     try:
#         connection_pool = pooling.MySQLConnectionPool(
#             pool_name="resume_pool",
#             pool_size=5,
#             host="localhost",
#             user="root",
#             password="",
#             database="resume_ai"
#         )
#         print("Database connection pool created")
#     except Error as e:
#         print(f"Error creating connection pool: {e}")
#         connection_pool = None

# def get_conn():
#     global connection_pool
#     if connection_pool:
#         try:
#             return connection_pool.get_connection()
#         except Error as e:
#             print(f"Pool connection failed: {e}, creating direct connection")
#     try:
#         conn = mysql.connector.connect(
#             host="localhost",
#             user="root",
#             password="",
#             database="resume_ai"
#         )
#         return conn
#     except Error as e:
#         print(f"Database connection error: {e}")
#         return None

# def run_query(query: str, params: Optional[Tuple] = None, fetch: bool = True):
#     conn = get_conn()
#     if conn is None:
#         return None
#     try:
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute(query, params)
#         if fetch:
#             result = cursor.fetchall()
#             cursor.close()
#             conn.close()
#             return result
#         else:
#             conn.commit()
#             last_id = cursor.lastrowid
#             cursor.close()
#             conn.close()
#             return last_id if last_id else True
#     except Error as e:
#         print(f"Query error: {e}")
#         print(f"Query: {query}")
#         if conn:
#             conn.close()
#         return None

# def list_vacancies() -> pd.DataFrame:
#     query = "SELECT * FROM vacancies ORDER BY created_at DESC"
#     result = run_query(query)
#     if result is None:
#         return pd.DataFrame()
#     return pd.DataFrame(result)

# def get_vacancy(vacancy_id: int) -> Optional[dict]:
#     query = "SELECT * FROM vacancies WHERE id=%s"
#     result = run_query(query, (vacancy_id,))
#     if result and len(result) > 0:
#         return result[0]
#     return None

# def add_vacancy(title: str, description: str, skills: Union[List[str], str], 
#                 embedding_weight: float, skills_weight: float, 
#                 other_weight: float, category: str = 'General') -> Optional[int]:
#     # Accept either a list of skills or a comma-separated string.
#     if isinstance(skills, (list, tuple)):
#         skills_str = ','.join(s.strip() for s in skills if s is not None)
#     else:
#         skills_str = (skills or '').strip()
#     query = """
#         INSERT INTO vacancies 
#         (title, description, skills, embedding_weight, skills_weight, other_weight, category)
#         VALUES (%s, %s, %s, %s, %s, %s, %s)
#     """
#     params = (title, description, skills_str, embedding_weight, skills_weight, other_weight, category)
#     return run_query(query, params, fetch=False)

# def delete_vacancy(vacancy_id: int) -> bool:
#     try:
#         # Remove any dependent rows first to avoid FK constraint issues
#         run_query("DELETE FROM scores WHERE vacancy_id=%s", (vacancy_id,), fetch=False)
#         run_query("DELETE FROM applications WHERE vacancy_id=%s", (vacancy_id,), fetch=False)
#         query = "DELETE FROM vacancies WHERE id=%s"
#         result = run_query(query, (vacancy_id,), fetch=False)
#         return result is not None
#     except Error as e:
#         print(f"Error deleting vacancy {vacancy_id}: {e}")
#         return False

# def list_candidates() -> pd.DataFrame:
#     query = "SELECT * FROM candidates ORDER BY uploaded_at DESC"
#     result = run_query(query)
#     if result is None:
#         return pd.DataFrame()
#     return pd.DataFrame(result)

# def get_candidate(candidate_id: int) -> Optional[dict]:
#     query = "SELECT * FROM candidates WHERE id=%s"
#     result = run_query(query, (candidate_id,))
#     if result and len(result) > 0:
#         return result[0]
#     return None

# def add_candidate(name: str, filename: str, extracted_text: str) -> Optional[int]:
#     query = """
#         INSERT INTO candidates (name, filename, extracted_text)
#         VALUES (%s, %s, %s)
#     """
#     return run_query(query, (name, filename, extracted_text), fetch=False)

# def delete_candidate(candidate_id: int) -> bool:
#     query = "DELETE FROM candidates WHERE id=%s"
#     result = run_query(query, (candidate_id,), fetch=False)
#     return result is not None

# def upsert_score(candidate_id: int, vacancy_id: int, 
#                  embedding_score: float, skills_score: float, 
#                  other_score: float, total_score: float) -> bool:
#     query = """
#         INSERT INTO scores 
#         (candidate_id, vacancy_id, embedding_score, skills_score, other_score, total_score)
#         VALUES (%s, %s, %s, %s, %s, %s)
#         ON DUPLICATE KEY UPDATE
#             embedding_score=%s,
#             skills_score=%s,
#             other_score=%s,
#             total_score=%s,
#             computed_at=CURRENT_TIMESTAMP
#     """
#     params = (
#         candidate_id, vacancy_id, 
#         embedding_score, skills_score, other_score, total_score,
#         embedding_score, skills_score, other_score, total_score
#     )
#     result = run_query(query, params, fetch=False)
#     return result is not None

# def get_scores_for_vacancy(vacancy_id: int) -> pd.DataFrame:
#     query = """
#         SELECT 
#             s.candidate_id, 
#             c.name, 
#             s.embedding_score, 
#             s.skills_score, 
#             s.other_score, 
#             s.total_score
#         FROM scores s
#         JOIN candidates c ON s.candidate_id = c.id
#         WHERE s.vacancy_id = %s
#         ORDER BY s.total_score DESC
#     """
#     result = run_query(query, (vacancy_id,))
#     if result is None:
#         return pd.DataFrame()
#     return pd.DataFrame(result)

# def get_scores_for_candidate(candidate_id: int) -> pd.DataFrame:
#     query = """
#         SELECT 
#             s.vacancy_id,
#             v.title,
#             s.embedding_score,
#             s.skills_score,
#             s.other_score,
#             s.total_score
#         FROM scores s
#         JOIN vacancies v ON s.vacancy_id = v.id
#         WHERE s.candidate_id = %s
#         ORDER BY s.total_score DESC
#     """
#     result = run_query(query, (candidate_id,))
#     if result is None:
#         return pd.DataFrame()
#     return pd.DataFrame(result)

# def get_all_scores() -> pd.DataFrame:
#     query = """
#         SELECT 
#             c.name as candidate_name,
#             v.title as vacancy_title,
#             s.embedding_score,
#             s.skills_score,
#             s.other_score,
#             s.total_score,
#             s.computed_at
#         FROM scores s
#         JOIN candidates c ON s.candidate_id = c.id
#         JOIN vacancies v ON s.vacancy_id = v.id
#         ORDER BY s.computed_at DESC
#     """
#     result = run_query(query)
#     if result is None:
#         return pd.DataFrame()
#     return pd.DataFrame(result)

# def get_stats() -> dict:
#     stats = {
#         'total_vacancies': 0,
#         'total_candidates': 0,
#         'total_scores': 0,
#         'scored_candidates': 0
#     }
#     conn = get_conn()
#     if conn is None:
#         return stats
#     try:
#         cur = conn.cursor()
#         cur.execute("SELECT COUNT(*) FROM vacancies")
#         stats['total_vacancies'] = cur.fetchone()[0]
#         cur.execute("SELECT COUNT(*) FROM candidates")
#         stats['total_candidates'] = cur.fetchone()[0]
#         cur.execute("SELECT COUNT(*) FROM scores")
#         stats['total_scores'] = cur.fetchone()[0]
#         cur.execute("SELECT COUNT(DISTINCT candidate_id) FROM scores")
#         stats['scored_candidates'] = cur.fetchone()[0]
#         cur.close()
#         conn.close()
#     except Error as e:
#         print(f"Stats error: {e}")
#     return stats

# def list_categories() -> pd.DataFrame:
#     query = "SELECT * FROM categories ORDER BY name"
#     result = run_query(query)
#     if result is None:
#         return pd.DataFrame()
#     return pd.DataFrame(result)


# def repair_vacancy_skills() -> dict:
#     """Detect and repair vacancies whose `skills` field appears to have
#     been stored with commas between characters (e.g. 'F,i,g,m,a,,, ,A,d,o,b,e').

#     Returns a dict with counts and list of updated vacancy ids.
#     """
#     import re

#     vacs = list_vacancies()
#     fixed = []
#     for _, row in vacs.iterrows():
#         vid = row['id']
#         skills = (row.get('skills') or '')
#         if not skills or ',' not in skills:
#             continue

#         parts = [p for p in skills.split(',')]
#         if len(parts) < 3:
#             continue

#         # If majority of comma-separated parts are single characters, treat as broken
#         single_count = sum(1 for p in parts if len(p.strip()) <= 1 and p.strip() != '')
#         if single_count / max(1, len(parts)) <= 0.5:
#             continue

#         # Attempt repair: remove commas, then split phrases on runs of 2+ spaces
#         no_commas = skills.replace(',', ' ')
#         # collapse multiple spaces into a delimiter
#         delim = '||SEP||'
#         cleaned = re.sub(r"\s{2,}", delim, no_commas)
#         phrases = [p.strip() for p in cleaned.split(delim) if p.strip()]
#         # As fallback, if no phrases found, fall back to splitting by single spaces and grouping
#         if not phrases:
#             words = [w for w in no_commas.split(' ') if w.strip()]
#             phrases = [' '.join(words)] if words else []

#         new_skills = ', '.join(phrases)
#         try:
#             run_query("UPDATE vacancies SET skills=%s WHERE id=%s", (new_skills, vid), fetch=False)
#             fixed.append(vid)
#         except Exception:
#             continue

#     return {"fixed_count": len(fixed), "fixed_ids": fixed}

# def add_category(name: str) -> Optional[int]:
#     query = "INSERT INTO categories (name) VALUES (%s)"
#     return run_query(query, (name,), fetch=False)

# def delete_category(category_id: int) -> bool:
#     query = "DELETE FROM categories WHERE id=%s"
#     result = run_query(query, (category_id,), fetch=False)
#     return result is not None

# def get_user(username: str) -> Optional[dict]:
#     query = "SELECT * FROM users WHERE username=%s"
#     result = run_query(query, (username,))
#     if result and len(result) > 0:
#         return result[0]
#     return None

# def register_user(username: str, password: str, role: str, candidate_id: int = None, email: str = None) -> Optional[int]:
#     """
#     Register a new user. Attempts to insert into the `email` column if provided.
#     Falls back to inserting without the email column for older schemas.
#     """
#     # Try inserting including email if passed
#     if email is not None:
#         try:
#             query = "INSERT INTO users (username, password, role, candidate_id, email) VALUES (%s, %s, %s, %s, %s)"
#             res = run_query(query, (username, password, role, candidate_id, email), fetch=False)
#             if res is not None:
#                 return res
#         except Exception:
#             # fall through to try without email
#             pass

#     # Fallback: insert without email
#     query = "INSERT INTO users (username, password, role, candidate_id) VALUES (%s, %s, %s, %s)"
#     return run_query(query, (username, password, role, candidate_id), fetch=False)

# init_pool()

import mysql.connector
from mysql.connector import Error, pooling
import pandas as pd
from typing import Optional, List, Tuple, Union

connection_pool = None

def init_pool():
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="resume_pool",
            pool_size=5,
            host="localhost",
            user="root",
            password="",
            database="resume_ai"
        )
        print("Database connection pool created")
    except Error as e:
        print(f"Error creating connection pool: {e}")
        connection_pool = None

def get_conn():
    global connection_pool
    if connection_pool:
        try:
            return connection_pool.get_connection()
        except Error as e:
            print(f"Pool connection failed: {e}, creating direct connection")
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="resume_ai"
        )
        return conn
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def run_query(query: str, params: Optional[Tuple] = None, fetch: bool = True):
    conn = get_conn()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        else:
            conn.commit()
            last_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return last_id if last_id else True
    except Error as e:
        print(f"Query error: {e}")
        print(f"Query: {query}")
        if conn:
            conn.close()
        return None

def list_vacancies() -> pd.DataFrame:
    query = "SELECT * FROM vacancies ORDER BY created_at DESC"
    result = run_query(query)
    if result is None:
        return pd.DataFrame()
    return pd.DataFrame(result)

def get_vacancy(vacancy_id: int) -> Optional[dict]:
    query = "SELECT * FROM vacancies WHERE id=%s"
    result = run_query(query, (vacancy_id,))
    if result and len(result) > 0:
        return result[0]
    return None

def add_vacancy(title: str, description: str, skills: Union[List[str], str], 
                embedding_weight: float, skills_weight: float, 
                other_weight: float, category: str = 'General') -> Optional[int]:
    if isinstance(skills, (list, tuple)):
        skills_str = ','.join(s.strip() for s in skills if s is not None)
    else:
        skills_str = (skills or '').strip()
    query = """
        INSERT INTO vacancies 
        (title, description, skills, embedding_weight, skills_weight, other_weight, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (title, description, skills_str, embedding_weight, skills_weight, other_weight, category)
    return run_query(query, params, fetch=False)

def delete_vacancy(vacancy_id: int) -> bool:
    try:
        run_query("DELETE FROM scores WHERE vacancy_id=%s", (vacancy_id,), fetch=False)
        run_query("DELETE FROM applications WHERE vacancy_id=%s", (vacancy_id,), fetch=False)
        query = "DELETE FROM vacancies WHERE id=%s"
        result = run_query(query, (vacancy_id,), fetch=False)
        return result is not None
    except Error as e:
        print(f"Error deleting vacancy {vacancy_id}: {e}")
        return False

def list_candidates() -> pd.DataFrame:
    query = "SELECT * FROM candidates ORDER BY uploaded_at DESC"
    result = run_query(query)
    if result is None:
        return pd.DataFrame()
    return pd.DataFrame(result)

def get_candidate(candidate_id: int) -> Optional[dict]:
    query = "SELECT * FROM candidates WHERE id=%s"
    result = run_query(query, (candidate_id,))
    if result and len(result) > 0:
        return result[0]
    return None

def add_candidate(name: str, filename: str, extracted_text: str) -> Optional[int]:
    query = """
        INSERT INTO candidates (name, filename, extracted_text)
        VALUES (%s, %s, %s)
    """
    return run_query(query, (name, filename, extracted_text), fetch=False)

def delete_candidate(candidate_id: int) -> bool:
    query = "DELETE FROM candidates WHERE id=%s"
    result = run_query(query, (candidate_id,), fetch=False)
    return result is not None

def upsert_score(candidate_id: int, vacancy_id: int, 
                 embedding_score: float, skills_score: float, 
                 other_score: float, total_score: float) -> bool:
    query = """
        INSERT INTO scores 
        (candidate_id, vacancy_id, embedding_score, skills_score, other_score, total_score)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            embedding_score=%s,
            skills_score=%s,
            other_score=%s,
            total_score=%s,
            computed_at=CURRENT_TIMESTAMP
    """
    params = (
        candidate_id, vacancy_id, 
        embedding_score, skills_score, other_score, total_score,
        embedding_score, skills_score, other_score, total_score
    )
    result = run_query(query, params, fetch=False)
    return result is not None

def get_scores_for_vacancy(vacancy_id: int) -> pd.DataFrame:
    query = """
        SELECT 
            s.candidate_id, 
            c.name, 
            s.embedding_score, 
            s.skills_score, 
            s.other_score, 
            s.total_score
        FROM scores s
        JOIN candidates c ON s.candidate_id = c.id
        WHERE s.vacancy_id = %s
        ORDER BY s.total_score DESC
    """
    result = run_query(query, (vacancy_id,))
    if result is None:
        return pd.DataFrame()
    return pd.DataFrame(result)

def get_scores_for_candidate(candidate_id: int) -> pd.DataFrame:
    query = """
        SELECT 
            s.vacancy_id,
            v.title,
            s.embedding_score,
            s.skills_score,
            s.other_score,
            s.total_score
        FROM scores s
        JOIN vacancies v ON s.vacancy_id = v.id
        WHERE s.candidate_id = %s
        ORDER BY s.total_score DESC
    """
    result = run_query(query, (candidate_id,))
    if result is None:
        return pd.DataFrame()
    return pd.DataFrame(result)

def get_all_scores() -> pd.DataFrame:
    query = """
        SELECT 
            c.name as candidate_name,
            v.title as vacancy_title,
            s.embedding_score,
            s.skills_score,
            s.other_score,
            s.total_score,
            s.computed_at
        FROM scores s
        JOIN candidates c ON s.candidate_id = c.id
        JOIN vacancies v ON s.vacancy_id = v.id
        ORDER BY s.computed_at DESC
    """
    result = run_query(query)
    if result is None:
        return pd.DataFrame()
    return pd.DataFrame(result)

def get_stats() -> dict:
    stats = {
        'total_vacancies': 0,
        'total_candidates': 0,
        'total_scores': 0,
        'scored_candidates': 0
    }
    conn = get_conn()
    if conn is None:
        return stats
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM vacancies")
        stats['total_vacancies'] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM candidates")
        stats['total_candidates'] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM scores")
        stats['total_scores'] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT candidate_id) FROM scores")
        stats['scored_candidates'] = cur.fetchone()[0]
        cur.close()
        conn.close()
    except Error as e:
        print(f"Stats error: {e}")
    return stats

def list_categories() -> pd.DataFrame:
    query = "SELECT * FROM categories ORDER BY name"
    result = run_query(query)
    if result is None:
        return pd.DataFrame()
    return pd.DataFrame(result)

def repair_vacancy_skills() -> dict:
    import re

    vacs = list_vacancies()
    fixed = []
    for _, row in vacs.iterrows():
        vid = row['id']
        skills = (row.get('skills') or '')
        if not skills or ',' not in skills:
            continue

        parts = [p for p in skills.split(',')]
        if len(parts) < 3:
            continue

        single_count = sum(1 for p in parts if len(p.strip()) <= 1 and p.strip() != '')
        if single_count / max(1, len(parts)) <= 0.5:
            continue

        no_commas = skills.replace(',', ' ')
        delim = '||SEP||'
        cleaned = re.sub(r"\s{2,}", delim, no_commas)
        phrases = [p.strip() for p in cleaned.split(delim) if p.strip()]
        if not phrases:
            words = [w for w in no_commas.split(' ') if w.strip()]
            phrases = [' '.join(words)] if words else []

        new_skills = ', '.join(phrases)
        try:
            run_query("UPDATE vacancies SET skills=%s WHERE id=%s", (new_skills, vid), fetch=False)
            fixed.append(vid)
        except Exception:
            continue

    return {"fixed_count": len(fixed), "fixed_ids": fixed}

def add_category(name: str) -> Optional[int]:
    query = "INSERT INTO categories (name) VALUES (%s)"
    return run_query(query, (name,), fetch=False)

def delete_category(category_id: int) -> bool:
    query = "DELETE FROM categories WHERE id=%s"
    result = run_query(query, (category_id,), fetch=False)
    return result is not None

def get_user(username: str) -> Optional[dict]:
    query = "SELECT * FROM users WHERE username=%s"
    result = run_query(query, (username,))
    if result and len(result) > 0:
        return result[0]
    return None

def register_user(username: str, password: str, role: str, candidate_id: int = None, email: str = None) -> Optional[int]:
    if email is not None:
        try:
            query = "INSERT INTO users (username, password, role, candidate_id, email) VALUES (%s, %s, %s, %s, %s)"
            res = run_query(query, (username, password, role, candidate_id, email), fetch=False)
            if res is not None:
                return res
        except Exception:
            pass

    query = "INSERT INTO users (username, password, role, candidate_id) VALUES (%s, %s, %s, %s)"
    return run_query(query, (username, password, role, candidate_id), fetch=False)

# NEW FUNCTION ADDED FOR streamlit-authenticator
def get_all_users() -> List[dict]:
    """
    Fetch all users for authentication system.
    Required for persistent login (cookies) on page refresh.
    """
    query = """
        SELECT username, password, role, candidate_id, email
        FROM users
    """
    result = run_query(query)
    
    if result is None:
        return []
    
    users = []
    for row in result:
        users.append({
            'username': row['username'],
            'password': row['password'],  # MUST be hashed (sha256)
            'role': row['role'],
            'candidate_id': row.get('candidate_id'),
            'email': row.get('email') or '',
            'name': row.get('email') or row['username']  # display name in sidebar
        })
    
    return users

# Initialize connection pool at module load
init_pool()