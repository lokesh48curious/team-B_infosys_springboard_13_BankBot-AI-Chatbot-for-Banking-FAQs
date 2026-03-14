import streamlit as st
import sqlite3
import hashlib
import io
import json
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Capital Bank AI Assistant",
    page_icon="🏦",
    layout="wide"
)

# ---------------- LOAD JSON KNOWLEDGE BASE ----------------
JSON_PATH = os.path.join(os.path.dirname(__file__), "bank_knowledge.json")

def load_knowledge_base() -> dict:
    """Load the bank knowledge base from JSON file."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

KB = load_knowledge_base()

# Precompute flat FAQ list from JSON for fast lookup
def build_faq_index(kb: dict) -> list[dict]:
    """Build a flat list of all FAQs with section info for quick searching."""
    index = []
    for section in kb["sections"]:
        for faq in section["faqs"]:
            index.append({
                "section": section["name"],
                "question": faq["question"],
                "keywords": faq["keywords"],
                "answer": faq["answer"],
            })
    return index

FAQ_INDEX = build_faq_index(KB)

# ---------------- DATABASE ----------------
DB = "bank_chatbot.db"

def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

conn = get_conn()
cursor = conn.cursor()

# ---------------- COMPLETE DATABASE SETUP ----------------
def setup_database():
    """Create ALL tables safely with proper migration."""

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL
    )
    """)

    # 2. Sections table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT
    )
    """)

    # 3. Chats table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        username TEXT,
        chat_id TEXT,
        title TEXT,
        section TEXT,
        role TEXT,
        message TEXT,
        ts TEXT
    )
    """)

    # Ensure chats has section column (for old DBs)
    cursor.execute("PRAGMA table_info(chats)")
    chat_cols = [col[1] for col in cursor.fetchall()]
    if "section" not in chat_cols:
        cursor.execute("ALTER TABLE chats ADD COLUMN section TEXT")

    # 4. FAQs table
    cursor.execute("PRAGMA table_info(faqs)")
    faq_columns = [col[1] for col in cursor.fetchall()]

    if len(faq_columns) == 0:
        cursor.execute("""
        CREATE TABLE faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER,
            question TEXT,
            answer TEXT
        )
        """)
    elif "section_id" not in faq_columns:
        cursor.execute("DROP TABLE IF EXISTS faqs")
        cursor.execute("""
        CREATE TABLE faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER,
            question TEXT,
            answer TEXT
        )
        """)

    conn.commit()

setup_database()

# ---------------- SYNC JSON → DATABASE ----------------
def sync_json_to_db():
    """
    Populate sections and faqs tables from JSON knowledge base.
    Only runs if DB tables are empty, ensuring JSON is the single source of truth.
    """
    cursor.execute("SELECT COUNT(*) AS c FROM sections")
    if cursor.fetchone()["c"] > 0:
        return  # Already populated

    for section_data in KB["sections"]:
        cursor.execute(
            "INSERT OR IGNORE INTO sections (name, description) VALUES (?, ?)",
            (section_data["name"], section_data["description"])
        )
        cursor.execute("SELECT id FROM sections WHERE name=?", (section_data["name"],))
        section_id = cursor.fetchone()["id"]

        for faq in section_data["faqs"]:
            cursor.execute(
                "INSERT INTO faqs (section_id, question, answer) VALUES (?, ?, ?)",
                (section_id, faq["question"], faq["answer"])
            )

    conn.commit()

sync_json_to_db()

# ---------------- OLLAMA ----------------
import ollama

SYSTEM_PROMPT = """
You are Capital Bank's official AI assistant.
You ONLY answer questions related to banking services, products, and financial topics.
If a user asks about anything unrelated to banking or finance, politely decline and redirect them to ask a banking question.
Use provided context if available.
Keep answers short, clear, and polite.
Never make up bank-specific data (rates, limits) not in the context.
"""

def ask_ollama(prompt: str) -> str:
    response = ollama.chat(
        model="phi3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response["message"]["content"]

# ---------------- UTIL ----------------
def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.current_chat = None
    st.session_state.chat_title = None
    st.session_state.selected_section = None
    st.session_state.page = "login"

# ---------------- AUTH ----------------
def signup():
    st.title("📝 Create Account")
    with st.form("signup"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        c = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")

    if submit and u and p:
        if p == c:
            try:
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (u, hash_password(p)),
                )
                conn.commit()
                st.success("✅ Account created! Please login.")
                st.session_state.page = "login"
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("❌ Username already exists")
        else:
            st.error("❌ Passwords do not match")


def login():
    st.title("🔐 Login")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit and u and p:
        cursor.execute("SELECT * FROM users WHERE username=?", (u,))
        user = cursor.fetchone()
        if user and user["password_hash"] == hash_password(p):
            st.session_state.logged_in = True
            st.session_state.username = u
            st.rerun()
        else:
            st.error("❌ Invalid credentials")


# ---------------- DATABASE FUNCTIONS ----------------
def save_msg(chat_id, role, msg, section=None):
    cursor.execute(
        """
        INSERT INTO chats (username, chat_id, title, section, role, message, ts)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            st.session_state.username,
            chat_id,
            st.session_state.chat_title,
            section or st.session_state.selected_section,
            role,
            msg,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()


def load_chat(chat_id):
    cursor.execute(
        """
        SELECT role, message FROM chats
        WHERE username=? AND chat_id=?
        ORDER BY ts
        """,
        (st.session_state.username, chat_id),
    )
    return cursor.fetchall()


def list_chats():
    cursor.execute("PRAGMA table_info(chats)")
    chat_cols = [col[1] for col in cursor.fetchall()]

    if "section" in chat_cols:
        cursor.execute(
            """
            SELECT chat_id, title, COALESCE(section, 'General') AS section, MIN(ts) AS t
            FROM chats
            WHERE username=?
            GROUP BY chat_id
            ORDER BY t DESC
            """,
            (st.session_state.username,),
        )
    else:
        cursor.execute(
            """
            SELECT chat_id, title, 'General' AS section, MIN(ts) AS t
            FROM chats
            WHERE username=?
            GROUP BY chat_id
            ORDER BY t DESC
            """,
            (st.session_state.username,),
        )
    return cursor.fetchall()


def delete_chat(chat_id):
    cursor.execute(
        "DELETE FROM chats WHERE username=? AND chat_id=?",
        (st.session_state.username, chat_id),
    )
    conn.commit()


# ---------------- FAQ SEARCH (JSON-powered) ----------------
def find_answer_from_json(q: str) -> tuple[str, bool]:
    """
    Search FAQ_INDEX (built from JSON) for a matching answer.
    Returns (answer_text, found_in_kb).
    Matches against keywords first, then question words.
    """
    q_lower = q.lower().strip()
    q_words = set(q_lower.split())

    best_match = None
    best_score = 0

    for faq in FAQ_INDEX:
        score = 0

        # 1. Keyword match (highest priority)
        for kw in faq["keywords"]:
            if kw in q_lower:
                score += 3

        # 2. Word overlap with question text
        faq_words = set(faq["question"].lower().split())
        overlap = len(q_words & faq_words)
        score += overlap

        if score > best_score:
            best_score = score
            best_match = faq

    if best_match and best_score >= 2:
        return best_match["answer"], True

    return KB.get("fallback_response", "Please contact support at 1800-123-4567."), False


def get_section_faqs_from_json(section_name: str) -> list[dict]:
    """Get FAQs for a specific section from the JSON knowledge base."""
    for section in KB["sections"]:
        if section["name"] == section_name:
            return section["faqs"]
    return []


# ---------------- TOPIC FILTER (JSON-powered) ----------------
def build_bank_keywords_from_json(kb: dict) -> set[str]:
    """
    Dynamically build the set of banking keywords from JSON keywords fields.
    This means the filter automatically expands when you update bank_knowledge.json.
    """
    kw_set = set()
    for section in kb["sections"]:
        kw_set.add(section["name"].lower())
        for faq in section["faqs"]:
            for kw in faq["keywords"]:
                # Add the full phrase and individual words
                kw_set.add(kw.lower())
                for word in kw.lower().split():
                    if len(word) > 3:  # skip short filler words
                        kw_set.add(word)
    return kw_set

# Build keyword set once at startup from JSON
BANK_KEYWORDS = build_bank_keywords_from_json(KB)

# Supplement with common banking terms not captured in FAQs
BANK_KEYWORDS.update({
    "account", "savings", "current", "fixed deposit", "fd",
    "loan", "credit card", "debit card", "upi", "payment",
    "net banking", "internet banking", "mobile banking",
    "ifsc", "branch", "interest", "emi", "statement",
    "customer care", "capital bank", "balance", "transfer",
    "rtgs", "neft", "imps", "cheque", "rd", "investment",
    "bank", "banking", "finance", "financial", "money",
    "deposit", "withdraw", "withdrawal", "transaction",
    "passbook", "kyc", "aadhar", "aadhaar", "pan card",
    "nominee", "atm", "pin", "otp", "password", "login",
})

def is_bank_question(text: str) -> bool:
    """
    Returns True if the question is banking-related.
    Uses JSON-derived keywords for classification.
    """
    t = text.lower()
    return any(k in t for k in BANK_KEYWORDS)


# ---------------- PDF EXPORT ----------------
def export_pdf(chat_id: str):
    msgs = load_chat(chat_id)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Capital Bank Chat Transcript", styles["Title"]))
    elements.append(Spacer(1, 12))

    data = [["Role", "Message"]]
    for row in msgs:
        role = row["role"].capitalize()
        msg = row["message"]
        data.append([role, msg])

    table = Table(data, colWidths=[80, 420])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ---------------- SIDEBAR ----------------
def sidebar():
    st.sidebar.title("🏦 Banking Sections")

    # Section selector — pulled from JSON
    section_names = [s["name"] for s in KB["sections"]]
    selected_name = st.sidebar.selectbox(
        "Choose banking section:",
        options=["All Sections"] + section_names,
    )

    st.session_state.selected_section = (
        selected_name if selected_name != "All Sections" else None
    )

    # Quick FAQs from JSON
    st.sidebar.markdown("---")
    if st.session_state.selected_section:
        faqs = get_section_faqs_from_json(st.session_state.selected_section)
        for faq in faqs[:3]:
            with st.sidebar.expander(faq["question"][:50]):
                st.write(faq["answer"])

    # Chats
    st.sidebar.markdown("---")
    st.sidebar.title("💬 Chats")

    if st.sidebar.button("➕ New Chat", key="new_chat_btn"):
        st.session_state.current_chat = (
            f"chat_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        st.session_state.chat_title = None
        st.rerun()

    chats = list_chats()
    for c in chats:
        title_base = c["title"] or "New Chat"
        title = title_base
        if c["section"] != "General":
            title += f" ({c['section']})"

        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button(title[:30], key=f"chat_{c['chat_id']}"):
                st.session_state.current_chat = c["chat_id"]
                st.session_state.chat_title = c["title"]
                st.rerun()
        with col2:
            if st.button("❌", key=f"del_{c['chat_id']}"):
                delete_chat(c["chat_id"])
                st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(f"👤 {st.session_state.username}")
    if st.sidebar.button("🚪 Logout", key="logout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ---------------- MAIN CHATBOT ----------------
def chatbot():
    sidebar()

    col1, col2 = st.columns(2)
    with col1:
        st.title("🏦 Capital Bank AI Assistant")
    with col2:
        st.metric("Section", st.session_state.selected_section or "All")

    if not st.session_state.current_chat:
        st.info("👈 Start a new chat from sidebar")
        return

    # Show chat history
    msgs = load_chat(st.session_state.current_chat)
    for row in msgs:
        with st.chat_message(row["role"]):
            st.markdown(row["message"])

    # New message input
    q = st.chat_input("💬 Ask a banking question...")
    if q:
        # Set chat title on first user message
        if not st.session_state.chat_title:
            st.session_state.chat_title = q[:40] + ("..." if len(q) > 40 else "")

        save_msg(st.session_state.current_chat, "user", q)

        with st.chat_message("user"):
            st.markdown(q)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                # ── Step 1: Topic guard (from JSON-derived keywords) ──
                if not is_bank_question(q):
                    ans = KB.get(
                        "off_topic_response",
                        "I can only assist with banking-related questions. "
                        "Please ask about accounts, cards, loans, UPI, or other banking services."
                    )

                else:
                    # ── Step 2: Search JSON knowledge base ──
                    faq_ans, found_in_kb = find_answer_from_json(q)

                    # ── Step 3: Build RAG prompt for Ollama ──
                    prompt = f"""User question: {q}

Capital Bank Knowledge Base:
{faq_ans}

Instructions:
- Answer politely and concisely
- Only answer banking-related questions
- If the knowledge base has a relevant answer, use it
- Do NOT invent specific numbers, rates, or limits not in the knowledge base
- If information is missing, tell the user to contact support at 1800-123-4567

Answer:"""

                    # ── Step 4: Call Ollama ──
                    ans = ask_ollama(prompt)

            # ── Step 5: Display & save ──
            st.markdown(ans)
            save_msg(st.session_state.current_chat, "assistant", ans)

    # PDF download
    if msgs:
        pdf = export_pdf(st.session_state.current_chat)
        st.download_button(
            "📄 Download PDF",
            pdf,
            "chat.pdf",
            "application/pdf",
            key="download_pdf",
        )


# ---------------- ROUTING ----------------
if not st.session_state.logged_in:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 Login", key="login_tab_btn"):
            st.session_state.page = "login"
    with col2:
        if st.button("📝 Signup", key="signup_tab_btn"):
            st.session_state.page = "signup"

    if st.session_state.get("page") == "signup":
        signup()
    else:
        login()
else:
    chatbot()
