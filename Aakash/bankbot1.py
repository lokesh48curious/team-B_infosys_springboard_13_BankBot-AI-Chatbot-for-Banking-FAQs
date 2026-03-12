import streamlit as st
import openai

# 1. Page Configuration
st.set_page_config(page_title="FinBot Live", page_icon="💬", layout="wide")
openai.api_key = "YOUR_OPENAI_API_KEY"

# 2. Database Initialization
if "user_db" not in st.session_state:
    st.session_state.user_db = {
        "admin": {
            "password": "123", "name": "Alex", "balance": 5240.50, 
            "query_history": [], "transactions": ["Oct 12: Starbucks -$5.50"],
            "loans": "No active loans.", "credit_score": 745, "card_status": "Active"
        }
    }

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CORE ACTION ENGINE ---
def execute_chat_action(user_text):
    """Processes either typed text or button clicks and returns a response."""
    user = st.session_state.user_db[st.session_state.current_user]
    st.session_state.messages.append({"role": "user", "content": user_text})
    user["query_history"].append(user_text)
    
    cmd = user_text.lower()
    
    if "balance" in cmd:
        resp = f"💰 Your current balance is **${user['balance']:,.2f}**."
    elif "transaction" in cmd:
        resp = f"📜 **Recent Activity:**\n" + "\n".join(user['transactions'])
    elif "block" in cmd or "lock" in cmd:
        user['card_status'] = "Blocked"
        resp = "⚠️ **Security Alert:** Your card is now blocked. Contact us to unblock."
    elif "loan" in cmd:
        resp = f"🏦 **Loan Status:** {user['loans']}"
    elif "score" in cmd or "credit" in cmd:
        resp = f"📈 Your credit score is **{user['credit_score']}**."
    elif "transfer" in cmd:
        resp = "💸 Please specify: 'Transfer [Amount] to [Name]'."
    elif "support" in cmd:
        resp = "🎧 Transferring you to our support queue..."
    elif "rate" in cmd:
        resp = "🏠 Current Mortgage Rates: 30-Year Fixed is at 6.5%."
    else:
        resp = "I'm not sure about that. Try asking for your 'balance' or to 'block my card'."

    st.session_state.messages.append({"role": "assistant", "content": resp})
    st.rerun()

# --- MAIN APP PAGE ---
def chatbot_page():
    user = st.session_state.user_db[st.session_state.current_user]

    # SIDEBAR
    with st.sidebar:
        st.title(f"👤 {user['name']}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        st.divider()
        st.subheader("📜 History")
        for q in reversed(user["query_history"][-5:]):
            st.caption(f"💬 {q}")
        
        chat_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
        st.download_button("📄 Download Chat", chat_text, file_name="chat.txt")

    # CHAT DISPLAY
    st.title("Banking Assistant")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # QUICK ACTION BUTTONS (Placed above input for immediate access)
    st.write("---")
    cols = st.columns(4)
    with cols[0]:
        if st.button("💰 Balance", key="btn_bal"): execute_chat_action("Check my balance?")
    with cols[1]:
        if st.button("📜 Transactions", key="btn_tx"): execute_chat_action("See transactions?")
    with cols[2]:
        if st.button("🚫 Block Card", key="btn_blk"): execute_chat_action("Block my card?")
    with cols[3]:
        if st.button("📈 Credit Score", key="btn_cs"): execute_chat_action("Check credit score?")

    # CHAT INPUT
    if prompt := st.chat_input("Type your message..."):
        execute_chat_action(prompt)

# --- LOGIN & REGISTER ---
def auth():
    st.title("🔒 FinBot Login")
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Sign In"):
            if u in st.session_state.user_db and st.session_state.user_db[u]["password"] == p:
                st.session_state.authenticated = True
                st.session_state.current_user = u
                st.rerun()
    with tab2:
        nu = st.text_input("New User")
        np = st.text_input("New Pass", type="password")
        if st.button("Register"):
            st.session_state.user_db[nu] = {"password": np, "name": nu, "balance": 1000.0, "query_history": [], "transactions": ["Welcome!"], "loans": "None", "credit_score": 700, "card_status": "Active"}
            st.success("User created!")

if not st.session_state.authenticated:
    auth()
else:
    chatbot_page()