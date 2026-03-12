import ollama
import streamlit as st
import uuid, time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
# ---------------- LOAD BANK LIBRARY ----------------
def load_bank_library():
    with open("bank_library.json", "r") as f:
        return json.load(f)
# ---------------- CHECK BANKING QUERY ----------------
# ---------------- CHECK BANKING QUERY ----------------
def check_bank_query(user_input):
    user_input = user_input.lower()

    for keyword, answer in bank_library.items():
        if keyword.lower() in user_input:
            return answer

    return None


# ---------------- BANKING DOMAIN CHECK ----------------
def is_banking_related(user_input):
    banking_keywords = [
        "bank", "loan", "credit", "debit", "account",
        "balance", "interest", "emi", "card",
        "deposit", "withdraw", "transaction",
        "atm", "ifsc", "net banking"
    ]

    user_input = user_input.lower()

    for word in banking_keywords:
        if word in user_input:
            return True

    return False


bank_library = load_bank_library()
def get_response(chat_history):

    user_input = chat_history[-1]["content"]

    # 1️⃣ Check JSON Library
    library_answer = check_bank_query(user_input)

    if library_answer:
        return library_answer

    # 2️⃣ Strict Restriction BEFORE Ollama
    if not is_banking_related(user_input):
        return "Please ask banking related questions only."

    # 3️⃣ If banking but not in JSON → Call Ollama
    messages = [
        {
            "role": "system",
            "content": "You are a professional banking assistant. "
                       "Answer clearly and briefly."
        }
    ]

    for m in chat_history[-5:]:
        messages.append({"role": m["role"], "content": m["content"]})

    response = ollama.chat(
        model="phi3:latest",
        messages=messages,
        options={
            "temperature": 0.2,
            "num_predict": 150
        }
    )

    return response["message"]["content"]



USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f ,indent=4)
def save_user_data(username):
    users = load_users()
    if username in users:
        users[username]["conversations"] = st.session_state.conversations
        users[username]["chat_titles"] = st.session_state.chat_titles
        users[username]["pinned_chats"] = list(st.session_state.pinned_chats)
        save_users(users)



st.set_page_config(page_title="BankBot AI", page_icon="🏦", layout="wide")

# ================= PREMIUM BACKGROUND =================
st.markdown("""
<style>

/* GLOBAL BACKGROUND */
html, body, .stApp, [data-testid="stAppViewContainer"], .main {
    background: linear-gradient(180deg,#E6E6FA 0%, #FFD6CC 100%) !important;
}

/* REMOVE HEADER + FOOTER */
header {visibility: hidden;}
footer {visibility: hidden;}

/* MAIN AREA TRANSPARENT */
[data-testid="stMain"] {
    background: transparent !important;
}

/* REMOVE WHITE CONTAINERS */
.block-container {
    background: transparent !important;
    padding-bottom: 0rem !important;
}

div[data-testid="stVerticalBlock"] {
    background: transparent !important;
}

/* SIDEBAR COLOR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#E6E6FA 0%, #FFD6CC 100%) !important;
    border-right: 2px solid rgba(120, 90, 180, 0.18) !important;
}

/* REMOVE SIDEBAR INNER WHITE */
section[data-testid="stSidebar"] > div {
    background: transparent !important;
}

/* ✅ STRONG SIDEBAR SPACE REDUCTION */
section[data-testid="stSidebar"] .block-container {
    padding-top: 0.6rem !important;
    padding-bottom: 0.6rem !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    margin-top: 0.2rem !important;
    margin-bottom: 0.25rem !important;
}

section[data-testid="stSidebar"] .stMarkdown {
    margin-bottom: 0.25rem !important;
}

section[data-testid="stSidebar"] .stButton {
    margin-bottom: 0.20rem !important;
}

section[data-testid="stSidebar"] hr {
    margin-top: 0.4rem !important;
    margin-bottom: 0.4rem !important;
}

/* REMOVE DIVIDER LINE */
hr {
    border: none !important;
    background: transparent !important;
    height: 0px !important;
}

/* BUTTON STYLE */
.stButton>button {
    border-radius: 12px;
    font-weight: 600;
    border: none !important;
}

/* CHAT INPUT BOX */
[data-testid="stChatInput"] textarea {
    background: rgba(255,255,255,0.35) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    color: black !important;
    font-weight: 500;
}

/* SEND BUTTON */
[data-testid="stChatInput"] button {
    background: #8A7FFF !important;
    border-radius: 12px !important;
    color: white !important;
    border: none !important;
}

/* DROPDOWN MENU STYLE */
.dropdown-box {
    background: linear-gradient(180deg,#E6E6FA 0%, #FFD6CC 100%);
    padding: 8px;
    border-radius: 12px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.15);
    margin-bottom: 10px;
}

/* ===== FIX WHITE STRIP BEHIND CHAT INPUT ===== */
div[data-testid="stBottom"],
div[data-testid="stBottomBlockContainer"] {
    background: #FFD6CC !important;
}

div[data-testid="stChatFloatingInputContainer"] {
    background: #FFD6CC !important;
    border-top: none !important;
    box-shadow: none !important;
}

div[data-testid="stChatInputContainer"] {
    background: transparent !important;
    border-top: none !important;
    box-shadow: none !important;
}

div[data-testid="stChatFloatingInputContainer"] > div {
    background: transparent !important;
}

div[data-testid="stChatFloatingInputContainer"]::before,
div[data-testid="stChatFloatingInputContainer"]::after {
    background: transparent !important;
}

/* ✅ CHAT SCROLL ONLY */
div[data-testid="stChatMessageContainer"] {
    height: 60vh !important;
    overflow-y: auto !important;
    padding-bottom: 130px !important;
}

</style>
""", unsafe_allow_html=True)


# ================= SESSION =================
if "page" not in st.session_state:
    st.session_state.page = "login"

if "username" not in st.session_state:
    st.session_state.username = ""

if "conversations" not in st.session_state:
    st.session_state.conversations = {}

if "view" not in st.session_state:
    st.session_state.view = "chat"

if "menu_open" not in st.session_state:
    st.session_state.menu_open = None

if "chat_titles" not in st.session_state:
    st.session_state.chat_titles = {}

if "pinned_chats" not in st.session_state:
    st.session_state.pinned_chats = set()

if "rename_mode" not in st.session_state:
    st.session_state.rename_mode = None


# ================= AUTO CHAT TITLE =================
def auto_title_from_text(text, max_words=4):
    text = text.strip().replace("\n", " ")
    if not text:
        return "Chat"
    words = text.split()
    title = " ".join(words[:max_words]).title()
    if len(words) > max_words:
        title += "..."
    return title

def set_auto_title_if_default(title_text):
    cid = st.session_state.current_chat
    if cid in st.session_state.chat_titles:
        if st.session_state.chat_titles[cid] == "Chat":
            st.session_state.chat_titles[cid] = title_text


# ================= LOGIN / SIGNUP =================
# ================= LOGIN / SIGNUP =================
if st.session_state.page == "login":

    st.title("🏦 BankBot AI")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # -------- LOGIN --------
    with tab1:
        user = st.text_input("Username", key="login_user")
        pw = st.text_input("Password", type="password", key="login_pw")

        if st.button("Login", use_container_width=True):

            users = load_users()

            if user in users and users[user]["password"] == pw:
                st.session_state.username = user
                st.session_state.page = "chat"
                # Load previous conversations
                st.session_state.conversations = dict(users[user].get("conversations", {}))
                st.session_state.chat_titles = dict(users[user].get("chat_titles", {}))
                st.session_state.pinned_chats = set(users[user].get("pinned_chats", []))
                if not st.session_state.conversations:
                    cid = str(uuid.uuid4())
                    st.session_state.current_chat = cid
                    st.session_state.conversations[cid] = [
                        {"role": "assistant", "content": "Hi! I am BankBot. How can I help you today?"}
                    ]
                    st.session_state.chat_titles[cid] = "Chat"
                else:
                    # Set current chat to the last chat
                    st.session_state.current_chat = list(st.session_state.conversations.keys())[-1]
                st.rerun()
            else:
                st.error("Invalid username or password")

    # -------- SIGNUP --------
    with tab2:
        new_user = st.text_input("Create Username", key="signup_user")
        new_pw = st.text_input("Create Password", type="password", key="signup_pw")

        if st.button("Create Account", use_container_width=True):

            users = load_users()

            if new_user in users:
                st.warning("Username already exists")

            elif new_user == "" or new_pw == "":
                st.warning("Please enter username and password")

            else:
                users[new_user] = {
                    "password": new_pw,
                    "conversations": {},
                    "chat_titles": {},
                    "pinned_chats": []
                }
                save_users(users)
                st.success("Account created! Now login.")



# ================= MAIN APP =================
elif st.session_state.page == "chat":

    # -------- SIDEBAR --------
    # -------- SIDEBAR --------
    # -------- SIDEBAR ACCOUNT --------
    st.sidebar.title("👤 Account")
    # Using a clickable username
    if "show_account_menu" not in st.session_state:
        st.session_state.show_account_menu = False
    # Username button
    if st.sidebar.button(f"👤 {st.session_state.username}", key="account_btn"):
        st.session_state.show_account_menu = not st.session_state.show_account_menu
    # Conditional account menu
    if st.session_state.show_account_menu:
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Logout", key="logout_btn"):
            st.session_state.clear()
            st.rerun()

    st.sidebar.divider()

    st.sidebar.title("📂 Menu")

    if st.sidebar.button("📊 Dashboard"):
        st.session_state.view = "dashboard"

    if st.sidebar.button("🤖 AI Chat"):
        st.session_state.view = "chat"

    st.sidebar.divider()

    # -------- DASHBOARD --------

    if st.session_state.view == "dashboard":

        import pandas as pd
        import matplotlib.pyplot as plt

        st.title("🏦 Bank Dashboard")
        st.markdown("## 📊 Financial Analytics")

        # metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(label="💰 Account Balance", value="₹1,25,000", delta="↑ 5%")

        with col2:
            st.metric(label="📄 Active Loans", value="2", delta="No Change")

        with col3:
            st.metric(label="⭐ Credit Score", value="785", delta="↑ Good")

        st.markdown("---")

        # line chart
        st.subheader("📈 Balance Growth")
        months = ["Jan","Feb","Mar","Apr","May","Jun"]
        balance = [100000,110000,105000,120000,123000,130000]

        df = pd.DataFrame({"Month": months, "Balance": balance})
        st.line_chart(df.set_index("Month"))

        st.markdown("---")

        # pie chart
        # pie chart
        st.subheader("💳 Expense Distribution")
        labels = ["Food","Bills","Travel","Shopping","Others"]
        values = [25,30,15,20,10]
        center1, center2, center3 = st.columns([1,2,1])
        with center2:
            fig, ax = plt.subplots(figsize=(3.2,3.2))
            ax.pie(values, labels=labels, autopct='%1.1f%%',textprops={'fontsize':8})
            ax.axis('equal')
            st.pyplot(fig, use_container_width=False)


    # -------- AI CHAT --------
    else:

        st.sidebar.markdown("### 💬 Conversations")

        if st.sidebar.button("➕ New Chat", use_container_width=True):
            cid = str(uuid.uuid4())
            st.session_state.conversations[cid] = [
                {"role": "assistant", "content": "Hi! I am BankBot. How can I help you today?"}
            ]
            st.session_state.current_chat = cid
            st.session_state.chat_titles[cid] = "Chat"
            st.session_state.menu_open = None
            st.session_state.rename_mode = None
            st.rerun()
        st.sidebar.markdown("### 🕘 Chat History")

        if "current_chat" not in st.session_state or not st.session_state.conversations:
            cid = str(uuid.uuid4())
            st.session_state.current_chat = cid
            st.session_state.conversations[cid] = [
                {"role": "assistant", "content": "Hi! I am BankBot. How can I help you today?"}
            ]
            st.session_state.chat_titles[cid] = "Chat"

        chat_ids = list(st.session_state.conversations.keys())

        pinned = [c for c in chat_ids if c in st.session_state.pinned_chats]
        normal = [c for c in chat_ids if c not in st.session_state.pinned_chats]

        final_chat_list = (
            sorted(pinned, key=lambda x: st.session_state.chat_titles.get(x, x)) +
            sorted(normal, key=lambda x: st.session_state.chat_titles.get(x, x))
        )

        for cid in final_chat_list:

            if cid not in st.session_state.chat_titles:
                st.session_state.chat_titles[cid] = "Chat"

            title = st.session_state.chat_titles[cid]
            if cid in st.session_state.pinned_chats:
                title = "📌 " + title

            col1, col2 = st.sidebar.columns([4, 1])

            with col1:
                if st.button(title, key=f"chat{cid}", use_container_width=True):
                    st.session_state.current_chat = cid
                    st.session_state.menu_open = None
                    st.session_state.rename_mode = None
                    st.rerun()

            with col2:
                if st.button("⋮", key=f"menu{cid}"):
                    st.session_state.menu_open = None if st.session_state.menu_open == cid else cid
                    st.session_state.rename_mode = None
                    st.rerun()

            if st.session_state.menu_open == cid:

                if cid in st.session_state.pinned_chats:
                    if st.sidebar.button("📌 Unpin", key=f"unpin{cid}", use_container_width=True):
                        st.session_state.pinned_chats.remove(cid)
                        st.session_state.menu_open = None
                        save_user_data(st.session_state.username)

                        st.rerun()
                else:
                    if st.sidebar.button("📌 Pin", key=f"pin{cid}", use_container_width=True):
                        st.session_state.pinned_chats.add(cid)
                        st.session_state.menu_open = None
                        save_user_data(st.session_state.username)

                        st.rerun()

                if st.sidebar.button("✏ Rename", key=f"rename_btn{cid}", use_container_width=True):
                    st.session_state.rename_mode = cid
                    st.rerun()

                if st.session_state.rename_mode == cid:
                    new_name = st.sidebar.text_input(
                        "New name",
                        value=st.session_state.chat_titles[cid],
                        key=f"rename_input{cid}"
                    )
                    if st.sidebar.button("✅ Save", key=f"save{cid}", use_container_width=True):
                        st.session_state.chat_titles[cid] = new_name.strip() or st.session_state.chat_titles[cid]
                        st.session_state.rename_mode = None
                        st.session_state.menu_open = None
                        save_user_data(st.session_state.username)

                        st.rerun()

                if st.sidebar.button("🗑 Delete", key=f"del{cid}", use_container_width=True):

                    del st.session_state.conversations[cid]
                    st.session_state.chat_titles.pop(cid, None)
                    st.session_state.pinned_chats.discard(cid)
                    save_user_data(st.session_state.username)


                    if st.session_state.current_chat == cid:
                        if st.session_state.conversations:
                            st.session_state.current_chat = list(st.session_state.conversations.keys())[0]
                        else:
                            newcid = str(uuid.uuid4())
                            st.session_state.conversations[newcid] = [
                                {"role": "assistant", "content": "Hi! I am BankBot. How can I help you today?"}
                            ]
                            st.session_state.current_chat = newcid
                            st.session_state.chat_titles[newcid] = "Chat"

                    st.rerun()

        # -------- CHAT AREA --------
        st.title("🏦 BankBot AI Assistance")

        chat = st.session_state.conversations[st.session_state.current_chat]

        st.markdown("### ⚡ Quick Access")
        c1, c2, c3 = st.columns(3)

        if c1.button("💰 Balance"):
            set_auto_title_if_default("Balance")
            chat.append({"role": "assistant", "content": "Your balance is ₹1,25,000"})
            save_user_data(st.session_state.username)


        if c2.button("📄 Loans"):
            set_auto_title_if_default("Loans")
            chat.append({"role": "assistant", "content": "We offer home & personal loans."})
            save_user_data(st.session_state.username)


        if c3.button("☎ Support"):
            set_auto_title_if_default("Support")
            chat.append({"role": "assistant", "content": "Call 1800-123-456"})
            save_user_data(st.session_state.username)


        for m in chat:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        prompt = st.chat_input("Message BankBot...")

        if prompt:
            with st.chat_message("user"):
                st.markdown(prompt)
            chat.append({"role": "user", "content": prompt})

            cid = st.session_state.current_chat
            if st.session_state.chat_titles.get(cid) == "Chat":
                st.session_state.chat_titles[cid] = auto_title_from_text(prompt)

            with st.chat_message("assistant"):
                msg = st.empty()
                msg.markdown("Typing...")
                reply = get_response(chat)
                msg.markdown(reply)

            chat.append({"role": "assistant", "content": reply})
            # SAVE USER DATA PERMANENTLY
            save_user_data(st.session_state.username)
