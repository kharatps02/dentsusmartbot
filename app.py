"""
Dentsu Smart Buddy — v5.1 (Production)
=========================================
Features:
  1. Smart keyword-based routing (no LLM hallucination) — works per doc type
  2. Professional onboarding page — "Dentsu Smart Buddy"
  3. URL/blog link → WebLoader → Q&A
  4. CSV/Excel → pandas analysis + chart generation
  5. Multi-document interaction (image + doc + csv simultaneously)
  6. Compatible with langchain==1.2.17, langchain-core==1.3.3,
     langchain-classic==1.0.5, langchain-community==0.4.1,
     langchain-openai==1.1.10 on Python 3.11
"""

import streamlit as st
import os
import re
import hashlib
import sqlite3
import uuid
import json
import base64
import html as html_lib
import io
from datetime import datetime
from warnings import filterwarnings

filterwarnings("ignore")

st.set_page_config(
    page_title="Dentsu Smart Buddy",
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --primary: #0033A0;
    --primary-dim: rgba(0,51,160,0.10);
    --primary-border: rgba(0,51,160,0.18);
    --primary-glow: rgba(0,51,160,0.25);
    --accent: #00C4B3;
    --accent-dim: rgba(0,196,179,0.10);
    --bg-root: #0A0D12;
    --bg-surface: #10141B;
    --bg-card: #161B25;
    --bg-elevated: #1D2330;
    --text-100: #F0F2F5;
    --text-200: #C4CAD4;
    --text-300: #8B95A5;
    --text-400: #5E6878;
    --border: rgba(255,255,255,0.06);
    --border-focus: rgba(0,51,160,0.45);
    --blue: #6B8AFF;
    --blue-dim: rgba(107,138,255,0.10);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.4);
    --shadow-xl: 0 20px 60px rgba(0,0,0,0.5);
}

html, body, .stApp {
    background: var(--bg-root) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-100) !important;
}
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

section[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] .stMarkdown span {
    color: var(--text-200) !important; font-family: 'Inter', sans-serif !important; font-size: 0.85rem !important;
}

.brand-box {
    padding: 1.5rem 1rem 1.2rem 1rem; text-align: center;
    border-bottom: 1px solid var(--border); margin-bottom: 1rem;
}
.brand-box .logo {
    font-size: 1.15rem; font-weight: 700; color: var(--primary);
    letter-spacing: 0.08em;
    display: flex; align-items: center; justify-content: center; gap: 0.45rem;
}
.brand-box .sub {
    font-size: 0.62rem; color: var(--text-400);
    letter-spacing: 0.15em; text-transform: uppercase; margin-top: 4px;
}

.user-pill {
    display: flex; align-items: center; gap: 0.6rem;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 0.55rem 0.75rem; margin: 0.6rem 0;
}
.user-pill .av {
    width: 30px; height: 30px; border-radius: 50%;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.75rem; color: #fff; flex-shrink: 0;
}
.user-pill .nm { font-weight: 600; font-size: 0.82rem; color: var(--text-100); }
.user-pill .rl { font-size: 0.68rem; color: var(--text-400); }

.sd { border: none; border-top: 1px solid var(--border); margin: 0.9rem 0; }

/* ── Professional Login ── */
.login-brand {
    text-align: center; margin-bottom: 2rem;
}
.login-brand .lb-icon {
    width: 64px; height: 64px; border-radius: 20px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 1.8rem; margin-bottom: 1rem; box-shadow: 0 8px 24px rgba(0,51,160,0.3);
}
.login-brand h1 {
    font-size: 1.55rem; font-weight: 700; color: var(--text-100);
    letter-spacing: 0.04em; margin: 0 0 0.15rem 0;
}
.login-brand h1 span { color: var(--accent); }
.login-brand .lb-tag {
    font-size: 0.68rem; color: var(--text-400); letter-spacing: 0.2em;
    text-transform: uppercase; margin-top: 0.2rem;
}
.login-brand .lb-desc {
    font-size: 0.82rem; color: var(--text-300); margin-top: 0.8rem;
    line-height: 1.55; max-width: 340px; margin-left: auto; margin-right: auto;
}
.login-features {
    display: flex; justify-content: center; gap: 1.2rem; margin-top: 1.2rem; flex-wrap: wrap;
}
.login-feat {
    display: flex; align-items: center; gap: 0.35rem;
    font-size: 0.7rem; color: var(--text-300);
    background: var(--bg-elevated); border: 1px solid var(--border);
    border-radius: 20px; padding: 0.3rem 0.7rem;
}
.login-feat .lf-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }

/* Chat */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important; padding: 0.8rem 1rem !important;
    margin-bottom: 0.5rem !important; color: var(--text-100) !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(0,51,160,0.10), rgba(0,51,160,0.04)) !important;
    border: 1px solid var(--primary-border) !important;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] td, [data-testid="stChatMessage"] span {
    color: var(--text-100) !important; font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatMessage"] h1, [data-testid="stChatMessage"] h2, [data-testid="stChatMessage"] h3 {
    color: var(--text-100) !important; font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
}
[data-testid="stChatMessage"] code {
    background: rgba(255,255,255,0.06) !important; color: #e0c285 !important;
    font-family: 'JetBrains Mono', monospace !important; padding: 0.15em 0.4em !important; border-radius: 4px !important;
}
[data-testid="stChatMessage"] pre {
    background: #0D1117 !important; border: 1px solid var(--border) !important; border-radius: var(--radius-sm) !important;
}
[data-testid="stChatMessage"] a { color: var(--blue) !important; }
[data-testid="stChatMessage"] blockquote {
    border-left: 3px solid var(--primary) !important; background: var(--primary-dim) !important;
    padding: 0.3em 0.9em !important; border-radius: 0 var(--radius-sm) var(--radius-sm) 0 !important;
}
[data-testid="stChatMessage"] table th { background: var(--bg-elevated) !important; border-bottom: 2px solid var(--primary-border) !important; }
[data-testid="stChatMessage"] table td { border-bottom: 1px solid var(--border) !important; }

.src-box { margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid rgba(255,255,255,0.06); }
.src-label { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #5E6878; margin-bottom: 0.35rem; }
.src-chips { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.src-chip {
    display: inline-flex; align-items: center; gap: 0.25rem;
    background: #1E2430; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px; padding: 0.2rem 0.6rem;
    font-size: 0.68rem; color: #8B95A5; text-decoration: none !important; transition: all 0.15s;
}
.src-chip:hover { border-color: rgba(0,51,160,0.3); color: #0033A0; background: rgba(0,51,160,0.08); }
.src-chip .sd2 { width: 5px; height: 5px; border-radius: 50%; background: #6B8AFF; flex-shrink: 0; }

.tbadge {
    display: inline-block; margin-top: 0.3rem;
    background: rgba(0,51,160,0.08); border: 1px solid rgba(0,51,160,0.18);
    border-radius: 20px; padding: 0.12rem 0.55rem;
    font-size: 0.62rem; font-weight: 500; color: #0033A0; font-family: 'JetBrains Mono', monospace;
}

.welcome-area { text-align: center; padding: 10vh 2rem 4rem 2rem; }
.welcome-area .w-icon {
    width: 64px; height: 64px; border-radius: 20px;
    background: linear-gradient(135deg, var(--primary), var(--accent));
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 1.6rem; margin-bottom: 1.2rem; box-shadow: 0 8px 24px rgba(0,51,160,0.25);
}
.welcome-area h2 { font-size: 1.4rem; font-weight: 600; color: var(--text-100); margin-bottom: 0.5rem; }
.welcome-area p { font-size: 0.88rem; color: var(--text-400); max-width: 480px; margin: 0 auto; line-height: 1.6; }

.doc-item {
    display: flex; align-items: center; gap: 0.4rem;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 6px; padding: 0.35rem 0.6rem; margin: 0.25rem 0;
    font-size: 0.75rem; color: var(--text-200);
}
.doc-item .di { color: var(--primary); flex-shrink: 0; }

.stTextInput > div > div > input {
    background: var(--bg-elevated) !important; border: 1px solid var(--border) !important;
    color: var(--text-100) !important; border-radius: var(--radius-sm) !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus { border-color: var(--border-focus) !important; box-shadow: 0 0 0 3px var(--primary-dim) !important; }
.stButton > button {
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    border-radius: var(--radius-sm) !important; transition: all 0.2s !important; font-size: 0.84rem !important;
}
form .stButton > button { background: linear-gradient(135deg, var(--primary), #0044CC) !important; color: #fff !important; border: none !important; }
form .stButton > button:hover { box-shadow: 0 4px 16px var(--primary-glow) !important; transform: translateY(-1px) !important; }
section[data-testid="stSidebar"] .stButton > button {
    background: var(--bg-card) !important; color: var(--text-200) !important; border: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--bg-elevated) !important; border-color: var(--primary-border) !important; color: var(--text-100) !important;
}
.stFileUploader > div { background: var(--bg-card) !important; border: 1px dashed rgba(255,255,255,0.1) !important; border-radius: var(--radius-sm) !important; }
.stChatInput > div { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: var(--radius-md) !important; }
.stChatInput textarea { color: var(--text-100) !important; font-family: 'Inter', sans-serif !important; }
.stSpinner > div > div { border-top-color: var(--accent) !important; }
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: var(--text-300) !important;
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    font-size: 0.82rem !important; padding: 0.6rem 1.2rem !important;
    border-bottom: 2px solid transparent !important; white-space: nowrap !important;
}
.stTabs [aria-selected="true"] { color: var(--primary) !important; border-bottom-color: var(--primary) !important; }
.stAlert { border-radius: var(--radius-sm) !important; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--bg-elevated); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════

DB_PATH = "research_assistant.db"

def init_database():
    conn = sqlite3.connect(DB_PATH); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, display_name TEXT,
        role TEXT DEFAULT 'user', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS conversations (
        conversation_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
        title TEXT DEFAULT 'New Chat',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        message_id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
        role TEXT NOT NULL, content TEXT NOT NULL,
        sources TEXT, tool_calls TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS documents (
        doc_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
        filename TEXT NOT NULL, file_type TEXT, content_preview TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit(); conn.close()

def _hash(pw): return hashlib.sha256(f"dentsu_salt_2025_{pw}".encode()).hexdigest()

def register_user(username, password):
    uid = str(uuid.uuid4()); display = username.strip().title()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT INTO users VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)",
                     (uid, username.lower().strip(), _hash(password), display, "user"))
        conn.commit(); conn.close()
        return {"user_id": uid, "username": username.lower().strip(), "display_name": display, "role": "user"}
    except sqlite3.IntegrityError:
        conn.close(); return None

def authenticate(username, password):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT user_id,username,display_name,role FROM users WHERE username=? AND password_hash=?",
                       (username.lower().strip(), _hash(password))).fetchone()
    conn.close()
    return {"user_id": row[0], "username": row[1], "display_name": row[2], "role": row[3]} if row else None

def seed_defaults():
    conn = sqlite3.connect(DB_PATH)
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)",
                     (str(uuid.uuid4()), "admin", _hash("admin123"), "Admin", "admin"))
    conn.commit(); conn.close()

def create_conversation(uid, title="New Chat"):
    cid = str(uuid.uuid4()); conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO conversations VALUES (?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)", (cid, uid, title))
    conn.commit(); conn.close(); return cid

def get_conversations(uid):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT conversation_id,title,created_at,updated_at FROM conversations WHERE user_id=? ORDER BY updated_at DESC", (uid,)).fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "created_at": r[2], "updated_at": r[3]} for r in rows]

def delete_conversation(cid):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM messages WHERE conversation_id=?", (cid,))
    conn.execute("DELETE FROM conversations WHERE conversation_id=?", (cid,))
    conn.commit(); conn.close()

def save_message(cid, role, content, sources=None, tool_calls=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP)",
                 (str(uuid.uuid4()), cid, role, content, json.dumps(sources) if sources else None, tool_calls))
    conn.execute("UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE conversation_id=?", (cid,))
    conn.commit(); conn.close()

def get_messages(cid):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT role,content,sources,tool_calls,timestamp FROM messages WHERE conversation_id=? ORDER BY timestamp ASC", (cid,)).fetchall()
    conn.close()
    out = []
    for r in rows:
        s = None
        if r[2]:
            try: s = json.loads(r[2])
            except: pass
        out.append({"role": r[0], "content": r[1], "sources": s, "tool_calls": r[3], "timestamp": r[4]})
    return out

def save_doc_record(uid, fname, ftype, preview):
    conn = sqlite3.connect(DB_PATH)
    existing = conn.execute("SELECT doc_id FROM documents WHERE user_id=? AND filename=?", (uid, fname)).fetchone()
    if existing: conn.close(); return
    conn.execute("INSERT INTO documents VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)",
                 (str(uuid.uuid4()), uid, fname, ftype, preview[:500]))
    conn.commit(); conn.close()

def get_user_docs(uid):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT doc_id,filename,file_type,uploaded_at FROM documents WHERE user_id=? ORDER BY uploaded_at DESC", (uid,)).fetchall()
    conn.close()
    return [{"id": r[0], "filename": r[1], "type": r[2], "uploaded_at": r[3]} for r in rows]

def delete_document(doc_id, uid):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT filename FROM documents WHERE doc_id=? AND user_id=?", (doc_id, uid)).fetchone()
    fname = row[0] if row else None
    conn.execute("DELETE FROM documents WHERE doc_id=? AND user_id=?", (doc_id, uid))
    conn.commit(); conn.close()
    return fname


# ═══════════════════════════════════════════════
# FILE PROCESSING
# ═══════════════════════════════════════════════

def extract_pdf(f):
    try:
        import pymupdf; f.seek(0)
        doc = pymupdf.open(stream=f.read(), filetype="pdf")
        txt = "\n".join(p.get_text() for p in doc); doc.close()
        return txt if txt.strip() else "[No extractable text in PDF]"
    except Exception as e: return f"[PDF error: {e}]"

def extract_docx(f):
    try:
        from docx import Document; f.seek(0)
        return "\n".join(p.text for p in Document(io.BytesIO(f.read())).paragraphs if p.text.strip())
    except Exception as e: return f"[DOCX error: {e}]"

def extract_txt(f):
    try:
        f.seek(0); d = f.read()
        try: return d.decode("utf-8")
        except: return d.decode("latin-1")
    except Exception as e: return f"[TXT error: {e}]"

def extract_image(f):
    try:
        f.seek(0); data = f.read()
        if not data: return "[Image error: empty file]"
        b64 = base64.b64encode(data).decode("utf-8")
        ext = f.name.rsplit(".", 1)[-1].lower()
        mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
        return f"__IMAGE_B64__{json.dumps({'mime': mime_map.get(ext, 'image/png'), 'b64': b64})}"
    except Exception as e: return f"[Image error: {e}]"

def extract_csv_excel(f):
    """Read CSV/Excel into pandas, store as JSON-safe marker."""
    try:
        import pandas as pd
        f.seek(0); name = f.name.lower()
        if name.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(f.read()))
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(f.read()))
        else:
            return "[Unsupported tabular format]"

        # Store everything as a single JSON blob — no pipe delimiter issues
        payload = {
            "shape": f"{df.shape[0]} rows × {df.shape[1]} columns",
            "columns": {col: str(df[col].dtype) for col in df.columns},
            "preview_md": df.head(20).to_markdown(index=False),
            "data_json": df.to_json(orient="records", date_format="iso")
        }
        return f"__DATAFRAME__{json.dumps(payload)}"
    except Exception as e:
        return f"[CSV/Excel error: {e}]"

def is_image_data(text):
    return text and text.startswith("__IMAGE_B64__")

def is_dataframe_data(text):
    return text and text.startswith("__DATAFRAME__")

def parse_image_data(text):
    """Extract mime and b64 from image marker."""
    try:
        payload = json.loads(text[len("__IMAGE_B64__"):])
        return payload["mime"], payload["b64"]
    except: return None, None

def parse_dataframe(text):
    """Reconstruct pandas DataFrame from marker."""
    try:
        import pandas as pd
        payload = json.loads(text[len("__DATAFRAME__"):])
        df = pd.DataFrame(json.loads(payload["data_json"]))
        return df, payload
    except:
        return None, None

def process_upload(f):
    n = f.name.lower()
    if n.endswith(".pdf"):  return extract_pdf(f)
    if n.endswith(".docx"): return extract_docx(f)
    if n.endswith(".txt"):  return extract_txt(f)
    if n.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")): return extract_image(f)
    if n.endswith((".csv", ".xlsx", ".xls")): return extract_csv_excel(f)
    return f"[Unsupported: {f.name}]"


# ═══════════════════════════════════════════════
# URL / BLOG LINK PROCESSING
# ═══════════════════════════════════════════════

def detect_url(text):
    match = re.search(r'https?://[^\s<>"\']+', text)
    return match.group(0) if match else None

def load_url_content(url):
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]): tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        content = "\n".join(lines)
        return content[:15000] if content else "[No content extracted from URL]"
    except Exception as e: return f"[URL load error: {e}]"

def store_url_as_doc(url, content):
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    doc_name = f"🔗 {domain}"
    st.session_state.setdefault("doc_texts", {})[doc_name] = content
    if doc_name not in st.session_state.get("processed_files", []):
        st.session_state.setdefault("processed_files", []).append(doc_name)
    st.session_state.setdefault("url_docs", {})[url] = doc_name
    return doc_name


# ═══════════════════════════════════════════════
# LLM HELPER
# ═══════════════════════════════════════════════

def get_llm(max_tokens=2000):
    from langchain_openai import AzureChatOpenAI
    return AzureChatOpenAI(
        azure_deployment="gpt-4o", api_version="2024-12-01-preview",
        azure_endpoint=st.session_state.get("azure_endpoint", ""),
        api_key=st.session_state.get("azure_api_key", ""),
        temperature=0, max_tokens=max_tokens
    )


# ═══════════════════════════════════════════════
# SMART ROUTING — keyword-based, no LLM hallucination
# ═══════════════════════════════════════════════

def classify_doc_types():
    """Classify all uploaded docs into categories."""
    image_entries = {}
    text_entries = {}
    df_entries = {}
    for fn, txt in st.session_state.get("doc_texts", {}).items():
        if is_image_data(txt):
            image_entries[fn] = txt
        elif is_dataframe_data(txt):
            df_entries[fn] = txt
        else:
            text_entries[fn] = txt
    return image_entries, text_entries, df_entries

def build_doc_topic_keywords():
    """Extract actual keywords from document content for matching."""
    keywords = set()
    for fn, txt in st.session_state.get("doc_texts", {}).items():
        if is_image_data(txt):
            keywords.update(["image", "picture", "photo", "diagram", "screenshot", fn.lower()])
        elif is_dataframe_data(txt):
            _, payload = parse_dataframe(txt)
            if payload:
                for col in payload.get("columns", {}).keys():
                    keywords.update(col.lower().split("_"))
                    keywords.update(col.lower().split(" "))
            keywords.update(["data", "csv", "excel", "table", "column", "row", fn.lower()])
        else:
            # Extract top words from text documents
            words = re.findall(r'\b[a-zA-Z]{3,}\b', txt[:3000].lower())
            # Get most frequent meaningful words
            from collections import Counter
            common = Counter(words).most_common(50)
            stop = {"the","and","for","are","but","not","you","all","can","had","her","was","one",
                    "our","out","has","have","been","from","this","that","with","they","will","each",
                    "which","their","said","what","its","about","than","into","them","some","could",
                    "other","more","very","when","come","make","like","over","such","also","most"}
            for w, _ in common:
                if w not in stop: keywords.add(w)
            keywords.add(fn.lower().replace(".pdf","").replace(".docx","").replace(".txt",""))
    return keywords

def is_query_about_docs(query):
    """Keyword overlap check — fast, no hallucination."""
    doc_keywords = build_doc_topic_keywords()
    if not doc_keywords:
        return False

    query_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))

    # Direct reference to document or file
    direct_refs = {"document", "file", "uploaded", "pdf", "report", "article", "csv",
                   "excel", "spreadsheet", "image", "picture", "photo", "data", "table",
                   "chart", "plot", "graph", "column", "analyze", "summarize", "summary",
                   "extract", "describe", "explain", "what", "list", "content"}
    if query_words & direct_refs:
        return True

    # Check overlap with actual doc content keywords
    overlap = query_words & doc_keywords
    # If at least 2 content words match, or 1 match + short query
    if len(overlap) >= 2:
        return True
    if len(overlap) >= 1 and len(query_words) <= 5:
        return True

    return False


# ═══════════════════════════════════════════════
# EXECUTION PATHS
# ═══════════════════════════════════════════════

def run_combined_query(prompt, image_entries, text_entries, df_entries, user, cid):
    """
    Handle queries across ALL doc types simultaneously.
    Images + text + dataframes all contribute context.
    Returns (answer, sources, tool_info, chart_fig_or_None)
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    # Determine if this is primarily a data analysis/chart request
    is_data_query = bool(df_entries) and any(kw in prompt.lower() for kw in [
        "chart", "plot", "graph", "visuali", "bar", "pie", "line", "histogram",
        "scatter", "trend", "distribution", "average", "mean", "sum", "count",
        "total", "max", "min", "group", "compare", "top", "bottom", "sort",
        "filter", "percentage", "ratio", "growth", "correlation"
    ])

    # If data analysis needed, run the pandas engine
    if is_data_query:
        answer, fig = run_dataframe_analysis(prompt, df_entries)
        # Also add text context if user references both
        if text_entries and any(w in prompt.lower() for w in ["document", "report", "pdf", "text", "article"]):
            text_answer, _, _ = run_doc_qa(prompt, text_entries, user, cid)
            answer = f"{answer}\n\n---\n\n**From your documents:**\n{text_answer}"
        return answer, [], "Data Analysis", fig

    # Build multimodal content for the LLM
    content_parts = [{"type": "text", "text": prompt}]
    has_images = bool(image_entries)
    today_str = datetime.now().strftime("%B %d, %Y")

    # Add text document context
    doc_ctx_parts = []
    if text_entries:
        for fn, txt in text_entries.items():
            doc_ctx_parts.append(f"[Document: {fn}]\n{txt[:4000]}")

    # Add DataFrame previews as text context
    if df_entries:
        for fn, raw in df_entries.items():
            _, payload = parse_dataframe(raw)
            if payload:
                doc_ctx_parts.append(f"[Data: {fn} ({payload['shape']})]\n{payload['preview_md'][:2000]}")

    if doc_ctx_parts:
        full_ctx = "\n\n---\n\n".join(doc_ctx_parts)
        content_parts[0]["text"] += f"\n\n[Uploaded document context:]\n{full_ctx}"

    # Add images
    if has_images:
        for fn, img_data in image_entries.items():
            mime, b64 = parse_image_data(img_data)
            if mime and b64:
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "high"}
                })

    # Use vision-capable model if images present
    try:
        llm = get_llm(max_tokens=2000)
        sys_content = f"You are Dentsu Smart Buddy. Today is {today_str}. "
        if has_images:
            sys_content += ("Analyze any provided images in detail alongside document text. "
                           "Describe what you see, extract text/data if present. ")
        sys_content += ("Answer using the provided document/image context. "
                       "If the answer isn't in the provided materials, say so clearly. "
                       "Format with markdown. Be thorough but concise.")

        messages = [SystemMessage(content=sys_content), HumanMessage(content=content_parts)]
        response = llm.invoke(messages)
        answer = response.content if response.content else "I couldn't generate a response from your documents."
        sources = extract_sources(answer)
        tools = []
        if has_images: tools.append("Image Analysis")
        if text_entries: tools.append("Document Q&A")
        if df_entries: tools.append("Data Analysis")
        tool_info = ", ".join(tools) if tools else None
        return answer, sources, tool_info, None
    except Exception as e:
        return f"Error: {str(e)}", [], None, None


def run_dataframe_analysis(query, df_entries):
    """Analyze CSV/Excel data using pandas. Returns (answer, chart_fig_or_None)."""
    try:
        import pandas as pd
        from langchain_core.messages import HumanMessage, SystemMessage

        all_dfs = {}
        for fn, raw in df_entries.items():
            df, payload = parse_dataframe(raw)
            if df is not None:
                all_dfs[fn] = (df, payload)

        if not all_dfs:
            return "No tabular data could be loaded.", None

        primary_name = list(all_dfs.keys())[0]
        df, payload = all_dfs[primary_name]

        schema_info = f"DataFrame '{primary_name}': {payload['shape']}\nColumns:\n"
        for col in df.columns:
            sample = df[col].dropna().head(3).tolist()
            schema_info += f"  - {col} ({df[col].dtype}): sample = {sample}\n"

        llm = get_llm(max_tokens=1500)

        wants_chart = any(kw in query.lower() for kw in [
            "chart", "plot", "graph", "visuali", "bar", "pie", "line",
            "histogram", "scatter", "trend", "distribution", "show me"
        ])

        if wants_chart:
            code_prompt = f"""Given this DataFrame schema:
{schema_info}

User wants: {query}

Write Python code that:
1. Uses variable `df` (pandas DataFrame, already loaded)
2. Uses matplotlib to create the chart
3. Creates figure: fig, ax = plt.subplots(figsize=(10, 6))
4. Style: dark background '#161B25', white text, colors ['#0033A0','#00C4B3','#6B8AFF','#FF6B6B','#FFB347']
5. Add title, labels. DO NOT call plt.show()

Output ONLY Python code. No explanation. No markdown fences."""

            resp = llm.invoke([
                SystemMessage(content="Output ONLY valid Python code. Nothing else."),
                HumanMessage(content=code_prompt)
            ])
            code = resp.content.strip()
            for fence in ["```python", "```py", "```"]:
                code = code.replace(fence, "")
            code = code.strip()

            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                import numpy as np

                exec_globals = {"pd": pd, "plt": plt, "np": np, "df": df}
                exec(code, exec_globals)
                fig = exec_globals.get("fig", plt.gcf())

                # Generate insight
                resp2 = llm.invoke([
                    SystemMessage(content="You are a data analyst. Be concise — 2-3 sentences with specific numbers."),
                    HumanMessage(content=f"Schema:\n{schema_info}\n\nUser asked: {query}\nChart was generated. Write a brief insight.")
                ])
                return resp2.content.strip(), fig

            except Exception as e:
                return f"**Chart error:** {e}\n\nGenerated code:\n```python\n{code}\n```\n\nFalling back to basic stats:\n\n{df.describe().to_markdown()}", None

        else:
            code_prompt = f"""Given this DataFrame schema:
{schema_info}

First rows:
{df.head().to_markdown(index=False)}

User question: {query}

Write Python code using variable `df` (pandas DataFrame). Store final answer as string in `result`.
Output ONLY Python code. No markdown fences."""

            resp = llm.invoke([
                SystemMessage(content="Output ONLY valid Python code. Nothing else."),
                HumanMessage(content=code_prompt)
            ])
            code = resp.content.strip()
            for fence in ["```python", "```py", "```"]:
                code = code.replace(fence, "")
            code = code.strip()

            try:
                import numpy as np
                exec_globals = {"pd": pd, "np": np, "df": df, "json": json}
                exec(code, exec_globals)
                result = exec_globals.get("result", "Analysis complete — no result variable set.")
                return str(result), None
            except Exception as e:
                basic = f"**Data Overview: {primary_name}** ({payload['shape']})\n\n"
                basic += df.describe().to_markdown() + f"\n\n*Code error: {e}*"
                return basic, None

    except Exception as e:
        return f"Analysis error: {str(e)}", None


def run_doc_qa(prompt, text_entries, user, cid):
    """Answer from text documents only."""
    snippets = [f"[Document: {fn}]\n{txt[:4000]}" for fn, txt in text_entries.items()]
    doc_context = "\n\n---\n\n".join(snippets)
    augmented = f"{prompt}\n\n[Uploaded document context:]\n{doc_context}"
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        llm = get_llm()
        today_str = datetime.now().strftime("%B %d, %Y")
        resp = llm.invoke([
            SystemMessage(content=f"You are Dentsu Smart Buddy. Today is {today_str}. "
                          "Answer using ONLY the provided document context. "
                          "If the answer isn't in the documents, say so. Format with markdown."),
            HumanMessage(content=augmented)
        ])
        answer = resp.content if resp.content else "I couldn't find an answer in your documents."
        return answer, extract_sources(answer), "Document Q&A"
    except Exception as e:
        return f"Error: {str(e)}", [], None


def run_web_agent(prompt, user, cid):
    """Run the full web agent (Tavily + weather)."""
    agent = st.session_state.get("agent")
    if agent is None:
        agent, error = init_agent()
        if error:
            return f"⚠️ {error}\n\nPlease configure your API credentials.", [], None
        st.session_state["agent"] = agent
    session_id = f"{user['user_id']}_{cid}"
    try:
        response = agent.invoke({"query": prompt}, {"configurable": {"session_id": session_id}})
        answer = response.get("output", "I couldn't generate a response.")
        tool_info = None
        if response.get("intermediate_steps"):
            tools_used = set()
            for step in response["intermediate_steps"]:
                if hasattr(step[0], "tool"): tools_used.add(step[0].tool)
            if tools_used: tool_info = ", ".join(tools_used)
        return answer, extract_sources(answer), tool_info
    except Exception as e:
        return f"Error: {str(e)}\n\nTry rephrasing your question.", [], None


# ═══════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════

def extract_sources(text):
    urls = re.findall(r'https?://[^\s\)\]>"\'`,]+', text)
    seen = set(); unique = []
    for u in urls:
        u = u.rstrip('.,;:!?)')
        domain = re.sub(r'^https?://(www\.)?', '', u).split('/')[0]
        if domain not in seen and len(domain) > 2:
            seen.add(domain); unique.append({"url": u, "domain": domain})
    return unique[:8]

def clean_answer_urls(text, sources):
    if not sources: return text
    protected = text; phs = {}
    for i, m in enumerate(re.finditer(r'\[([^\]]+)\]\(https?://[^\)]+\)', text)):
        ph = f"MDLNK{i}X"; phs[ph] = m.group(0); protected = protected.replace(m.group(0), ph, 1)
    cleaned = re.sub(r'https?://[^\s\)\]>"\'`,]+', '', protected)
    for ph, orig in phs.items(): cleaned = cleaned.replace(ph, orig)
    cleaned = re.sub(r'Source:\s*$', '', cleaned, flags=re.M)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()

def get_domain_label(domain):
    parts = domain.split('.'); return parts[-2].capitalize() if len(parts) >= 2 else domain.capitalize()

def generate_title(content):
    words = content.split()[:7]; return " ".join(words) + ("..." if len(content.split()) > 7 else "")

def render_sources_and_tools(sources, tools):
    parts = []
    if sources:
        chips = ""
        for s in sources:
            d = s.get("domain", ""); u = html_lib.escape(s.get("url", "#"))
            chips += f'<a href="{u}" target="_blank" rel="noopener" class="src-chip"><span class="sd2"></span>{get_domain_label(d)} · {d}</a>'
        parts.append(f'<div class="src-box"><div class="src-label">📎 Sources</div><div class="src-chips">{chips}</div></div>')
    if tools:
        t = str(tools)
        t = t.replace("search_web_extract_info", "Web Search").replace("get_weather", "Weather")
        parts.append(f'<div class="tbadge">⚡ {t}</div>')
    if parts:
        st.markdown("\n".join(parts), unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════

def init_agent():
    EP = st.session_state.get("azure_endpoint", "")
    AK = st.session_state.get("azure_api_key", "")
    TK = "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"
    WK = "1ad27edef23e488888304546262703"

    if not all([EP, AK]):
        return None, "Azure OpenAI credentials not configured."

    from langchain_openai import AzureChatOpenAI
    llm = AzureChatOpenAI(azure_deployment="gpt-4o", api_version="2024-12-01-preview",
                          azure_endpoint=EP, api_key=AK, temperature=0)

    import requests as req
    from langchain_core.tools import tool
    tools_list = []

    if TK:
        os.environ["TAVILY_API_KEY"] = TK
        from langchain_community.tools.tavily_search import TavilySearchResults
        tavily = TavilySearchResults(max_results=5, search_depth="advanced", include_raw_content=True)

        @tool
        def search_web_extract_info(query: str) -> str:
            """Search the web for current events, news, or any information."""
            try:
                results = tavily.invoke(query)
                if not results: return "No results found."
                parts = []
                for i, r in enumerate(results, 1):
                    parts.append(f"[{i}] {r.get('title','')}\n{r.get('content','')}\nSource: {r.get('url','')}")
                return "\n\n---\n\n".join(parts)
            except Exception as e: return f"Search error: {e}"
        tools_list.append(search_web_extract_info)

    @tool
    def get_weather(query: str) -> str:
        """Get current weather for a location."""
        try:
            data = req.get("http://api.weatherapi.com/v1/current.json", params={"key": WK, "q": query}, timeout=10).json()
            if data.get("location"):
                l, c = data["location"], data["current"]
                return f"Weather in {l['name']}, {l.get('country','')}:\nTemp: {c['temp_c']}°C/{c['temp_f']}°F\nCondition: {c['condition']['text']}\nHumidity: {c['humidity']}%\nWind: {c['wind_kph']} km/h {c.get('wind_dir','')}\nFeels like: {c['feelslike_c']}°C/{c['feelslike_f']}°F"
            return "Location not found."
        except Exception as e: return f"Weather error: {e}"
    tools_list.append(get_weather)

    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    today_str = datetime.now().strftime("%B %d, %Y")
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are Dentsu Smart Buddy — an AI research assistant.
Today's date is {today_str}.
Tools: search_web_extract_info (web search), get_weather (weather).
ALWAYS use search_web_extract_info for current events, news, sports, elections, rankings.
Format answers with markdown. Include source URLs. Be thorough but concise."""),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", "{query}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
    agent = create_tool_calling_agent(llm, tools_list, prompt)
    executor = AgentExecutor(agent=agent, tools=tools_list, early_stopping_method="force",
                             max_iterations=5, verbose=False, return_intermediate_steps=True,
                             handle_parsing_errors=True)

    from langchain_community.chat_message_histories import SQLChatMessageHistory
    from langchain_core.runnables.history import RunnableWithMessageHistory
    chatbot = RunnableWithMessageHistory(executor,
        lambda sid: SQLChatMessageHistory(session_id=sid, connection="sqlite:///agent_memory.db"),
        input_messages_key="query", history_messages_key="history")
    return chatbot, None


# ═══════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════

def render_login():
    st.markdown("<style>section[data-testid='stSidebar']{display:none;}</style>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.0, 1.8, 1.0])
    with c2:
        st.markdown("""
        <div class="login-brand">
            <div class="lb-icon">🤖</div>
            <h1>Dentsu <span>Smart Buddy</span></h1>
            <div class="lb-tag">Intelligent Research Assistant</div>
            <div class="lb-desc">
                Your AI-powered research companion — analyze documents, explore data,
                search the web, and get insights in seconds.
            </div>
            <div class="login-features">
                <div class="login-feat"><span class="lf-dot"></span> Document Q&A</div>
                <div class="login-feat"><span class="lf-dot"></span> Data Analysis</div>
                <div class="login-feat"><span class="lf-dot"></span> Web Research</div>
                <div class="login-feat"><span class="lf-dot"></span> URL Ingestion</div>
                <div class="login-feat"><span class="lf-dot"></span> Smart Charts</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        t1, t2 = st.tabs(["Sign In", "Create Account"])
        with t1:
            with st.form("login_form", clear_on_submit=False):
                u = st.text_input("Username", placeholder="Enter your username", key="lu")
                p = st.text_input("Password", type="password", placeholder="Enter your password", key="lp")
                if st.form_submit_button("Sign In", use_container_width=True):
                    if u and p:
                        user = authenticate(u, p)
                        if user:
                            st.session_state.update(authenticated=True, user=user, current_conv=None, messages=[])
                            st.rerun()
                        else: st.error("Invalid credentials.")
                    else: st.warning("Please fill in both fields.")
        with t2:
            with st.form("signup_form", clear_on_submit=True):
                nu = st.text_input("Choose a username", placeholder="e.g. john.doe", key="su")
                p1 = st.text_input("Create password", type="password", placeholder="Min 4 characters", key="sp1")
                p2 = st.text_input("Confirm password", type="password", placeholder="Re-enter password", key="sp2")
                if st.form_submit_button("Create Account", use_container_width=True):
                    nc = (nu or "").strip()
                    if not nc or not p1: st.warning("Both fields required.")
                    elif len(nc) < 3: st.warning("Username must be 3+ characters.")
                    elif len(p1) < 4: st.warning("Password must be 4+ characters.")
                    elif p1 != p2: st.error("Passwords don't match.")
                    else:
                        r = register_user(nc, p1)
                        if r: st.success(f"Account created! Sign in as **{nc}**.")
                        else: st.error("Username already taken.")
        st.markdown("<p style='text-align:center;color:var(--text-400);font-size:0.68rem;margin-top:1.5rem;'>Powered by Dentsu AI · Secure & Confidential</p>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════

def render_sidebar():
    user = st.session_state["user"]
    with st.sidebar:
        st.markdown('<div class="brand-box"><div class="logo">🤖 Dentsu Smart Buddy</div><div class="sub">AI Research Assistant</div></div>', unsafe_allow_html=True)
        ini = user["display_name"][0].upper()
        st.markdown(f'<div class="user-pill"><div class="av">{ini}</div><div><div class="nm">{user["display_name"]}</div><div class="rl">{user["role"].title()}</div></div></div>', unsafe_allow_html=True)

        st.markdown('<hr class="sd">', unsafe_allow_html=True)
        with st.expander("🔑 API Configuration", expanded=not st.session_state.get("azure_endpoint")):
            ep_val = st.text_input("Model Endpoint", value=st.session_state.get("azure_endpoint", ""),
                                   placeholder="https://your-resource.openai.azure.com/", key="input_endpoint")
            ak_val = st.text_input("Azure OpenAI API Key", value=st.session_state.get("azure_api_key", ""),
                                   placeholder="Enter your API key", key="input_api_key", type="password")
            if st.button("Save Credentials", use_container_width=True, key="save_creds"):
                if ep_val.strip() and ak_val.strip():
                    st.session_state["azure_endpoint"] = ep_val.strip()
                    st.session_state["azure_api_key"] = ak_val.strip()
                    st.session_state.pop("agent", None)
                    st.success("Credentials saved!"); st.rerun()
                else: st.warning("Both fields are required.")

        if st.button("＋  New conversation", use_container_width=True, key="new_chat"):
            st.session_state["current_conv"] = None; st.session_state["messages"] = []
            st.session_state.pop("pending_web_search", None); st.rerun()

        st.markdown('<hr class="sd">', unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.72rem;font-weight:700;color:var(--text-400);letter-spacing:0.1em;text-transform:uppercase;'>History</p>", unsafe_allow_html=True)

        for c in get_conversations(user["user_id"])[:20]:
            active = st.session_state.get("current_conv") == c["id"]
            cols = st.columns([6, 1])
            with cols[0]:
                if st.button(f"{'▸ ' if active else ''}{c['title'][:35]}", key=f"c_{c['id']}", use_container_width=True):
                    st.session_state["current_conv"] = c["id"]
                    st.session_state["messages"] = get_messages(c["id"]); st.rerun()
            with cols[1]:
                if st.button("×", key=f"d_{c['id']}"):
                    delete_conversation(c["id"])
                    if st.session_state.get("current_conv") == c["id"]:
                        st.session_state["current_conv"] = None; st.session_state["messages"] = []
                    st.rerun()

        if not get_conversations(user["user_id"]): st.caption("No conversations yet")

        st.markdown('<hr class="sd">', unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.72rem;font-weight:700;color:var(--text-400);letter-spacing:0.1em;text-transform:uppercase;'>Documents & Data</p>", unsafe_allow_html=True)

        if "processed_files" not in st.session_state: st.session_state["processed_files"] = []
        if "doc_texts" not in st.session_state: st.session_state["doc_texts"] = {}

        uploaded = st.file_uploader("Upload PDF, DOCX, TXT, CSV, Excel, Images",
                                    type=["pdf","docx","txt","png","jpg","jpeg","gif","webp","csv","xlsx","xls"],
                                    accept_multiple_files=True, key="uploader")
        if uploaded:
            for uf in uploaded:
                if uf.name not in st.session_state["processed_files"]:
                    with st.spinner(f"Reading {uf.name}..."):
                        txt = process_upload(uf)
                        if txt and not txt.startswith("["):
                            st.session_state["doc_texts"][uf.name] = txt
                            preview = txt[:500] if not (is_image_data(txt) or is_dataframe_data(txt)) else txt[:100]
                            save_doc_record(user["user_id"], uf.name, uf.name.split(".")[-1], preview)
                            st.session_state["processed_files"].append(uf.name)
                            st.rerun()
                        else: st.error(f"Failed: {uf.name}")

        # URL input
        st.markdown('<hr class="sd">', unsafe_allow_html=True)
        url_input = st.text_input("🔗 Paste a blog/article URL", placeholder="https://example.com/article", key="url_input")
        if url_input and url_input.startswith("http"):
            if url_input not in st.session_state.get("url_docs", {}):
                with st.spinner("Loading URL content..."):
                    content = load_url_content(url_input)
                    if not content.startswith("["):
                        doc_name = store_url_as_doc(url_input, content)
                        st.success(f"Loaded: {doc_name}"); st.rerun()
                    else: st.error(content)

        # Show docs
        user_docs = get_user_docs(user["user_id"])
        if user_docs:
            for d in user_docs[:10]:
                dc1, dc2 = st.columns([6, 1])
                with dc1:
                    fn_l = d["filename"].lower()
                    icon = "🖼️" if fn_l.endswith((".png",".jpg",".jpeg",".gif",".webp")) else "📊" if fn_l.endswith((".csv",".xlsx",".xls")) else "📄"
                    st.markdown(f'<div class="doc-item"><span class="di">{icon}</span>{d["filename"]}</div>', unsafe_allow_html=True)
                with dc2:
                    if st.button("×", key=f"deldoc_{d['id']}"):
                        fname = delete_document(d["id"], user["user_id"])
                        if fname and fname in st.session_state.get("doc_texts", {}): del st.session_state["doc_texts"][fname]
                        if fname and fname in st.session_state.get("processed_files", []): st.session_state["processed_files"].remove(fname)
                        st.rerun()

        for url, name in st.session_state.get("url_docs", {}).items():
            st.markdown(f'<div class="doc-item"><span class="di">🔗</span>{name}</div>', unsafe_allow_html=True)

        if not user_docs and not st.session_state.get("url_docs"): st.caption("No documents uploaded")

        st.markdown('<hr class="sd">', unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True, key="logout"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()
        st.markdown("<p style='color:var(--text-400);font-size:0.62rem;text-align:center;padding-top:0.8rem;'>Dentsu Smart Buddy v5.1</p>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# CHAT — Smart Routing
# ═══════════════════════════════════════════════

def render_chat():
    if not st.session_state.get("azure_endpoint") or not st.session_state.get("azure_api_key"):
        st.markdown("""
        <div class="welcome-area">
            <div class="w-icon">🔑</div>
            <h2>Configure API Credentials</h2>
            <p>Open <b>🔑 API Configuration</b> in the sidebar to get started.</p>
        </div>""", unsafe_allow_html=True)
        return

    messages = st.session_state.get("messages", [])

    if not messages:
        st.markdown("""
        <div class="welcome-area">
            <div class="w-icon">🤖</div>
            <h2>Hi! I'm Dentsu Smart Buddy</h2>
            <p>Upload documents, paste URLs, or just ask me anything.
            I handle PDFs, images, CSVs, Excel files, and web research — all at once.</p>
        </div>""", unsafe_allow_html=True)

    for msg in messages:
        role = msg["role"]
        avatar = "🟢" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            if role == "user":
                st.markdown(msg["content"])
            else:
                sources = msg.get("sources") or []
                display_text = clean_answer_urls(msg["content"], sources) if sources else msg["content"]
                st.markdown(display_text)
                if msg.get("chart_key") and msg["chart_key"] in st.session_state.get("charts", {}):
                    st.pyplot(st.session_state["charts"][msg["chart_key"]])
                render_sources_and_tools(sources, msg.get("tool_calls"))

    prompt = st.chat_input("Type your question here...", key="chat_input")

    if prompt:
        user = st.session_state["user"]

        if not st.session_state.get("current_conv"):
            cid = create_conversation(user["user_id"], generate_title(prompt))
            st.session_state["current_conv"] = cid
        else:
            cid = st.session_state["current_conv"]

        save_message(cid, "user", prompt)
        st.session_state.setdefault("messages", []).append(
            {"role": "user", "content": prompt, "sources": None, "tool_calls": None}
        )

        with st.chat_message("user", avatar="🟢"):
            st.markdown(prompt)

        # ── Handle pending web search confirmation ──
        pending = st.session_state.pop("pending_web_search", None)
        if pending:
            yes_words = {"yes", "y", "yeah", "sure", "ok", "go ahead", "yep", "please", "do it"}
            if prompt.strip().lower() in yes_words:
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Searching the web..."):
                        answer, sources, tool_info = run_web_agent(pending, user, cid)
                    st.markdown(clean_answer_urls(answer, sources) if sources else answer)
                    render_sources_and_tools(sources, tool_info)
                save_message(cid, "assistant", answer, sources=sources, tool_calls=tool_info)
                st.session_state["messages"].append({"role": "assistant", "content": answer, "sources": sources, "tool_calls": tool_info})
                return

            no_words = {"no", "n", "nope", "nah", "cancel"}
            if prompt.strip().lower() in no_words:
                reply = "No problem! Ask me anything about your uploaded documents."
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(reply)
                save_message(cid, "assistant", reply)
                st.session_state["messages"].append({"role": "assistant", "content": reply, "sources": None, "tool_calls": None})
                return
            # If neither yes nor no, treat as a new query — fall through

        # ── Check for URL in chat ──
        detected_url = detect_url(prompt)
        if detected_url and detected_url not in st.session_state.get("url_docs", {}):
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner(f"Loading content from URL..."):
                    content = load_url_content(detected_url)
                    if not content.startswith("["):
                        doc_name = store_url_as_doc(detected_url, content)
                        answer = f"I've loaded **{doc_name}** into memory. You can now ask me questions about this article!"
                    else:
                        answer = f"I couldn't load that URL: {content}"
                st.markdown(answer)
            save_message(cid, "assistant", answer)
            st.session_state["messages"].append({"role": "assistant", "content": answer, "sources": None, "tool_calls": "URL Content"})
            return

        # ── MAIN ROUTING ──
        has_docs = bool(st.session_state.get("doc_texts"))

        if has_docs:
            # Keyword-based relevancy — fast, deterministic, no hallucination
            query_about_docs = is_query_about_docs(prompt)

            if query_about_docs:
                # Route to combined document handler (supports all doc types at once)
                image_entries, text_entries, df_entries = classify_doc_types()

                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Analyzing your documents..."):
                        answer, sources, tool_info, chart_fig = run_combined_query(
                            prompt, image_entries, text_entries, df_entries, user, cid
                        )

                    display_text = clean_answer_urls(answer, sources) if sources else answer
                    st.markdown(display_text)

                    chart_key = None
                    if chart_fig is not None:
                        chart_key = f"chart_{uuid.uuid4().hex[:8]}"
                        st.session_state.setdefault("charts", {})[chart_key] = chart_fig
                        st.pyplot(chart_fig)

                    render_sources_and_tools(sources, tool_info)

                save_message(cid, "assistant", answer, sources=sources, tool_calls=tool_info)
                st.session_state["messages"].append(
                    {"role": "assistant", "content": answer, "sources": sources,
                     "tool_calls": tool_info, "chart_key": chart_key}
                )

            else:
                # Not about docs — ask user if they want web search
                routing_msg = ("This query doesn't appear to be related to your uploaded documents.\n\n"
                              "Would you like me to **search the web** for an answer?\n\n"
                              "Type **Yes** to search the web, or **No** to cancel.")
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(routing_msg)
                st.session_state["pending_web_search"] = prompt
                save_message(cid, "assistant", routing_msg)
                st.session_state["messages"].append(
                    {"role": "assistant", "content": routing_msg, "sources": None, "tool_calls": "Smart Routing"}
                )

        else:
            # No docs uploaded — straight to web agent
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Researching your question..."):
                    answer, sources, tool_info = run_web_agent(prompt, user, cid)
                st.markdown(clean_answer_urls(answer, sources) if sources else answer)
                render_sources_and_tools(sources, tool_info)
            save_message(cid, "assistant", answer, sources=sources, tool_calls=tool_info)
            st.session_state["messages"].append({"role": "assistant", "content": answer, "sources": sources, "tool_calls": tool_info})


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

def main():
    init_database(); seed_defaults()
    if not st.session_state.get("authenticated"):
        render_login()
    else:
        render_sidebar()
        render_chat()

if __name__ == "__main__":
    main()
