import streamlit as st
import sqlite3
import hashlib
import io
import json
import os
import re
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Capital Bank AI Assistant",
    page_icon="🏦",
    layout="wide"
)

# ---------------- LOAD JSON KNOWLEDGE BASE ----------------
JSON_PATH = os.path.join(os.path.dirname(__file__), "bank_knowledge.json")

def load_knowledge_base() -> dict:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

KB = load_knowledge_base()

def build_faq_index(kb: dict) -> list[dict]:
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

def setup_database():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT
    )
    """)
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
    cursor.execute("PRAGMA table_info(chats)")
    chat_cols = [col[1] for col in cursor.fetchall()]
    if "section" not in chat_cols:
        cursor.execute("ALTER TABLE chats ADD COLUMN section TEXT")

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

def sync_json_to_db():
    cursor.execute("SELECT COUNT(*) AS c FROM sections")
    if cursor.fetchone()["c"] > 0:
        return
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

def _clean_response(text: str) -> str:
    """Strip sign-offs that small models append despite instructions."""
    sign_off_patterns = [
        r"\n+best[,.]?\s*(regards|wishes)?[,.]?\s*[\w\s]*assistant[.!]?\s*$",
        r"\n+sincerely[,.]?\s*[\w\s]*[.!]?\s*$",
        r"\n+regards[,.]?\s*[\w\s]*[.!]?\s*$",
        r"\n+thank you[,.]?\s*[\w\s]*[.!]?\s*$",
        r"\n+yours (truly|sincerely)[,.]?\s*[\w\s]*[.!]?\s*$",
        r"\n+[-–—]+\s*[\w\s]*assistant[.!]?\s*$",
        r"\n+capital bank assistant[.!]?\s*$",
        r"\n+- capital bank[.!]?\s*$",
        r"\n+warm regards[,.]?\s*[\w\s]*[.!]?\s*$",
    ]
    for pattern in sign_off_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).rstrip()
    return text


def ask_ollama(user_question: str, kb_context: str) -> str:
    """
    All instructions + KB context go into the system message.
    User message is ONLY the bare question — prevents context leaking into reply.
    num_predict caps tokens to stop infinite looping.
    Low temperature gives fast, focused answers.
    """
    system_prompt = f"""You are Capital Bank's AI assistant.
Answer the customer's banking question using the context below.
Be short and direct. One to three sentences maximum.
Never add sign-offs, greetings, or signatures.
Never repeat the question.
If unsure, say: contact support at 1800-123-4567.

CONTEXT:
{kb_context}
"""
    try:
        response = ollama.chat(
            model="phi3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_question},
            ],
            options={
                "num_predict": 150,  # hard cap — stops infinite looping
                "temperature": 0.1,  # focused, fast answers
                "top_p": 0.9,
            },
        )
        return _clean_response(response["message"]["content"].strip())
    except Exception:
        return (
            "I'm having trouble responding right now. "
            "Please contact support at 1800-123-4567."
        )


# ---------------- UTIL ----------------
def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in   = False
    st.session_state.username    = None
    st.session_state.current_chat = None
    st.session_state.chat_title  = None
    st.session_state.selected_section = None
    st.session_state.page        = "login"

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
            st.session_state.username  = u
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


# ---------------- FAQ SEARCH ----------------
def find_answer_from_json(q: str) -> tuple[str, bool]:
    q_lower  = q.lower().strip()
    q_words  = set(q_lower.split())
    best_match = None
    best_score = 0

    for faq in FAQ_INDEX:
        score = 0
        for kw in faq["keywords"]:
            if kw in q_lower:
                score += 3
        faq_words = set(faq["question"].lower().split())
        score += len(q_words & faq_words)

        if score > best_score:
            best_score = score
            best_match = faq

    if best_match and best_score >= 2:
        return best_match["answer"], True

    return KB.get(
        "fallback_response",
        "Please contact support at 1800-123-4567."
    ), False


def get_section_faqs_from_json(section_name: str) -> list[dict]:
    for section in KB["sections"]:
        if section["name"] == section_name:
            return section["faqs"]
    return []


# ---------------- TOPIC FILTER ----------------
def build_bank_keywords_from_json(kb: dict) -> set[str]:
    kw_set = set()
    for section in kb["sections"]:
        kw_set.add(section["name"].lower())
        for faq in section["faqs"]:
            for kw in faq["keywords"]:
                kw_set.add(kw.lower())
                for word in kw.lower().split():
                    if len(word) > 3:
                        kw_set.add(word)
    return kw_set

BANK_KEYWORDS = build_bank_keywords_from_json(KB)
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
    t = text.lower()
    return any(k in t for k in BANK_KEYWORDS)


# ---------------- PDF EXPORT (FIXED) ----------------
def export_pdf(chat_id: str):
    """
    PDF FIX: Wraps every cell in Paragraph() so long text wraps properly.
    Previously used raw strings → text was clipped at cell boundary.
    Now uses:
      - Paragraph() for all cells   → full word-wrap
      - A4 page with proper margins → full usable width
      - repeatRows=1                → header repeats on every page
      - Alternating row colours     → easy to read
    """
    msgs = load_chat(chat_id)
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Cell styles
    role_style = styles["Normal"].clone("RoleStyle")
    role_style.fontSize = 9
    role_style.leading  = 13

    user_style = styles["Normal"].clone("UserStyle")
    user_style.fontSize  = 10
    user_style.leading   = 15
    user_style.textColor = colors.HexColor("#1a1a2e")

    bot_style = styles["Normal"].clone("BotStyle")
    bot_style.fontSize  = 10
    bot_style.leading   = 15
    bot_style.textColor = colors.HexColor("#0f3460")

    elements = []

    # ── Title ──
    title_style = styles["Title"].clone("MyTitle")
    title_style.fontSize  = 16
    title_style.textColor = colors.HexColor("#0f3460")
    elements.append(Paragraph("Capital Bank — Chat Transcript", title_style))
    elements.append(Spacer(1, 0.2 * cm))

    # ── Export timestamp ──
    sub_style = styles["Normal"].clone("Sub")
    sub_style.fontSize  = 8
    sub_style.textColor = colors.grey
    elements.append(Paragraph(
        f"Exported on {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        sub_style
    ))
    elements.append(Spacer(1, 0.5 * cm))

    # ── Column widths (must sum to usable page width = 17 cm) ──
    col_role = 2.5 * cm
    col_msg  = 14.5 * cm

    # ── Header row ──
    hdr_style = styles["Normal"].clone("HdrStyle")
    hdr_style.fontSize  = 10
    hdr_style.textColor = colors.white

    table_data = [[
        Paragraph("<b>Role</b>",    hdr_style),
        Paragraph("<b>Message</b>", hdr_style),
    ]]

    # ── Message rows — KEY FIX: Paragraph() enables word-wrap ──
    row_colors = []
    for i, row in enumerate(msgs):
        is_user = row["role"] == "user"
        label   = "You" if is_user else "Bot"
        style   = user_style if is_user else bot_style
        bg      = colors.HexColor("#eef2ff") if is_user else colors.white

        # Preserve newlines from the message
        msg_text = str(row["message"]).replace("&", "&amp;") \
                                      .replace("<", "&lt;") \
                                      .replace(">", "&gt;") \
                                      .replace("\n", "<br/>")

        table_data.append([
            Paragraph(label, role_style),
            Paragraph(msg_text, style),
        ])

        # +1 because row 0 is the header
        row_colors.append(("BACKGROUND", (0, i + 1), (-1, i + 1), bg))

    table = Table(
        table_data,
        colWidths=[col_role, col_msg],
        repeatRows=1,           # header repeats on every page
        hAlign="LEFT",
    )

    table.setStyle(TableStyle([
        # Header styling
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#0f3460")),
        ("FONTSIZE",      (0, 0), (-1, 0), 10),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),

        # All cells
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING",    (0, 1), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),

        # Borders
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.5, colors.HexColor("#0f3460")),

        *row_colors,
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5 * cm))

    # ── Footer ──
    foot_style = styles["Normal"].clone("Foot")
    foot_style.fontSize  = 8
    foot_style.textColor = colors.grey
    elements.append(Paragraph(
        "Capital Bank — Confidential | Support: 1800-123-4567 | support@capitalbank.com",
        foot_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ---------------- SIDEBAR ----------------
def sidebar():
    st.sidebar.title("🏦 Banking Sections")

    section_names = [s["name"] for s in KB["sections"]]
    selected_name = st.sidebar.selectbox(
        "Choose banking section:",
        options=["All Sections"] + section_names,
    )

    st.session_state.selected_section = (
        selected_name if selected_name != "All Sections" else None
    )

    st.sidebar.markdown("---")
    if st.session_state.selected_section:
        faqs = get_section_faqs_from_json(st.session_state.selected_section)
        for faq in faqs[:3]:
            with st.sidebar.expander(faq["question"][:50]):
                st.write(faq["answer"])

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
                st.session_state.chat_title   = c["title"]
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

    msgs = load_chat(st.session_state.current_chat)
    for row in msgs:
        with st.chat_message(row["role"]):
            st.markdown(row["message"])

    q = st.chat_input("💬 Ask a banking question...")
    if q:
        if not st.session_state.chat_title:
            st.session_state.chat_title = q[:40] + ("..." if len(q) > 40 else "")

        save_msg(st.session_state.current_chat, "user", q)

        with st.chat_message("user"):
            st.markdown(q)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                # Step 1: Topic guard
                if not is_bank_question(q):
                    ans = KB.get(
                        "off_topic_response",
                        "I can only assist with banking-related questions. "
                        "Please ask about accounts, cards, loans, UPI, or other banking services."
                    )
                else:
                    # Step 2: Retrieve best KB answer as context
                    kb_context, _ = find_answer_from_json(q)

                    # Step 3: Call Ollama
                    ans = ask_ollama(q, kb_context)

            st.markdown(ans)
            save_msg(st.session_state.current_chat, "assistant", ans)

    if msgs:
        pdf = export_pdf(st.session_state.current_chat)
        st.download_button(
            "📄 Download Chat as PDF",
            pdf,
            file_name=f"capital_bank_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
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
