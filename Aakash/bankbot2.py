import streamlit as st
import requests
import json

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="BankBot AI", layout="centered")

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "llama3.2:1b"   # ✅ Changed model

# ----------------------------
# SESSION STATE INIT
# ----------------------------
if "users" not in st.session_state:
    st.session_state.users = {}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ----------------------------
# OLLAMA FUNCTION
# ----------------------------
def chat_with_ollama(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )

        if response.status_code != 200:
            return f"Ollama Error {response.status_code}: {response.text}"

        data = response.json()
        return data.get("response", "No response from model.")

    except requests.exceptions.ConnectionError:
        return "❌ Ollama not running. Run: ollama run llama3.2:1b"
    except requests.exceptions.ReadTimeout:
        return "⏳ Model is slow. Try again."
    except Exception as e:
        return f"Error: {str(e)}"

# ----------------------------
# BUILD PROMPT
# ----------------------------
def build_prompt(user_input):
    user = st.session_state.users[st.session_state.current_user]

    return f"""
You are BankBot AI, a professional banking assistant.

User Details:
Name: {user['name']}
Balance: ₹{user['balance']:,.2f}
Credit Score: {user['credit_score']}

Question:
{user_input}
"""

# ----------------------------
# AUTH PAGE
# ----------------------------
def auth_page():
    st.title("🏦 BankBot AI Login / Register")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            if username in st.session_state.users:
                if st.session_state.users[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error("Wrong password")
            else:
                st.error("User not found")

    with tab2:
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")

        if st.button("Register"):
            if new_user and new_pass:
                if new_user not in st.session_state.users:
                    st.session_state.users[new_user] = {
                        "password": new_pass,
                        "name": new_user,
                        "balance": 5000.0,
                        "credit_score": 700,
                        "chat_history": []
                    }
                    st.success("Account created successfully")
                else:
                    st.error("User already exists")
            else:
                st.error("Enter valid details")

# ----------------------------
# CHAT PAGE
# ----------------------------
def chat_page():
    user = st.session_state.users[st.session_state.current_user]

    st.title(f"🏦 Welcome {user['name']}")

    with st.sidebar:
        st.write(f"Balance: ₹{user['balance']:,.2f}")
        st.write(f"Credit Score: {user['credit_score']}")

        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

        st.divider()

        if user["chat_history"]:
            chat_text = ""
            for msg in user["chat_history"]:
                chat_text += f"{msg['role'].upper()}: {msg['content']}\n\n"

            st.download_button(
                label="Download as TXT",
                data=chat_text,
                file_name="chat_history.txt",
                mime="text/plain"
            )

            st.download_button(
                label="Download as JSON",
                data=json.dumps(user["chat_history"], indent=4),
                file_name="chat_history.json",
                mime="application/json"
            )

    for msg in user["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask your banking question...")

    if user_input:
        user["chat_history"].append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.markdown(user_input)

        prompt = build_prompt(user_input)

        with st.spinner("Thinking..."):
            reply = chat_with_ollama(prompt)

        user["chat_history"].append({
            "role": "assistant",
            "content": reply
        })

        with st.chat_message("assistant"):
            st.markdown(reply)

# ----------------------------
# APP FLOW
# ----------------------------
if st.session_state.authenticated:
    chat_page()
else:
    auth_page()
