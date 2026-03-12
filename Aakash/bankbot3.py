import streamlit as st
import json
import os
import hashlib

# ======================================
# CONFIG
# ======================================
DATA_FILE = "users.json"

st.set_page_config(page_title="BankBot AI", layout="centered")

# ======================================
# BANKING FAQ JSON
# ======================================
BANK_FAQ = {
    "what is savings account": "A savings account allows customers to deposit money securely and earn interest.",

    "what is current account": "A current account is used mainly by businesses for frequent transactions.",

    "how to open bank account": "You can open a bank account by providing ID proof, address proof and completing KYC verification.",

    "what is atm": "ATM stands for Automated Teller Machine used to withdraw cash and check balance.",

    "what is debit card": "A debit card allows you to pay directly using money from your bank account.",

    "what is credit card": "A credit card allows you to borrow money from the bank to make purchases.",

    "what is loan": "A loan is money borrowed from a bank that must be repaid with interest.",

    "what is fixed deposit": "A fixed deposit allows you to invest money for a fixed period with higher interest.",

    "what is net banking": "Net banking allows customers to perform banking transactions online.",

    "what is mobile banking": "Mobile banking allows customers to manage their bank accounts using mobile apps.",

    "what is upi": "UPI is a digital payment system that allows instant bank transfers.",

    "what is neft": "NEFT is an electronic fund transfer system used for transferring money between banks.",

    "what is rtgs": "RTGS is used for high value real-time money transfers.",

    "what is kyc": "KYC means Know Your Customer, a verification process required by banks.",

    "how to check balance": "You can check your bank balance using ATM, mobile banking or net banking.",

    "how to withdraw money": "You can withdraw money using an ATM card or by visiting the bank branch.",

    "how to deposit money": "Money can be deposited through bank counter or cash deposit machines.",

    "what is bank statement": "A bank statement shows all transactions made in your bank account.",

    "what is ifsc code": "IFSC code identifies a specific bank branch for online transactions.",

    "what is overdraft": "Overdraft allows customers to withdraw more money than their account balance."
}

# ======================================
# PASSWORD HASH
# ======================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ======================================
# LOAD USERS
# ======================================
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}}

# ======================================
# SAVE USERS
# ======================================
def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ======================================
# BANK ANSWER FUNCTION
# ======================================
def get_bank_answer(question):
    question = question.lower().strip()

    if question in BANK_FAQ:
        return BANK_FAQ[question]
    else:
        return "❌ I answer only banking related questions."

# ======================================
# SESSION INIT
# ======================================
if "data" not in st.session_state:
    st.session_state.data = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ======================================
# REGISTER PAGE
# ======================================
def register_page():

    st.title("📝 Register Account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register"):

        data = st.session_state.data

        if not username or not password:
            st.warning("All fields required")
            return

        if password != confirm:
            st.error("Passwords do not match")
            return

        if username in data["users"]:
            st.error("User already exists")
            return

        data["users"][username] = {
            "password": hash_password(password),
            "balance": 5000,
            "chat_history": []
        }

        save_users(data)

        st.success("Account created successfully")

# ======================================
# LOGIN PAGE
# ======================================
def login_page():

    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        data = st.session_state.data
        hashed = hash_password(password)

        if username in data["users"] and data["users"][username]["password"] == hashed:

            st.session_state.logged_in = True
            st.session_state.current_user = username

            st.success("Login successful")
            st.rerun()

        else:
            st.error("Invalid username or password")

# ======================================
# DASHBOARD
# ======================================
def dashboard():

    user = st.session_state.current_user
    user_data = st.session_state.data["users"][user]

    st.title(f"🏦 Welcome {user}")
    st.write(f"💰 Balance: ₹{user_data['balance']}")

    st.divider()

    st.subheader("💬 Banking Chat Assistant")

    # Show chat history
    for msg in user_data["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Ask banking question...")

    if prompt:

        user_data["chat_history"].append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.write(prompt)

        reply = get_bank_answer(prompt)

        user_data["chat_history"].append({
            "role": "assistant",
            "content": reply
        })

        with st.chat_message("assistant"):
            st.write(reply)

        save_users(st.session_state.data)

    st.sidebar.divider()

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.session_state.current_user = None

        st.rerun()

# ======================================
# MAIN
# ======================================
def main():

    if st.session_state.logged_in:

        dashboard()

    else:

        page = st.sidebar.selectbox(
            "Navigation",
            ["Login", "Register"]
        )

        if page == "Login":
            login_page()
        else:
            register_page()

if __name__ == "__main__":
    main()