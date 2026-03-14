import re
import requests
from datetime import datetime
import uuid
import json
import os
import random
import streamlit as st
from ollama_integration import (
    get_ollama_response,
    stream_ollama_response,
    rewrite_banking_response,
    is_banking_query
)

USER_FILE = "users.json"
SESSION_FILE = "session.json"
HISTORY_FILE = "chat_history.json"
INTENTS_FILE = os.path.join("data", "intents.json")

@st.cache_data
def load_intents():
    if not os.path.exists(INTENTS_FILE):
        return {"intents": []}
    try:
        with open(INTENTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading intents: {e}")
        return {"intents": []}

# Global intents data, initialized from cached function
intents_data = load_intents()

def persist_user(username, email, password):
    users = get_persisted_users()
    users[username] = {"email": email, "password": password}
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def get_persisted_users():
    if not os.path.exists(USER_FILE):
        return {}
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_active_session(username):
    with open(SESSION_FILE, "w") as f:
        json.dump({"username": username}, f)

def get_active_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            return data.get("username")
    except:
        return None

def clear_active_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"

def format_currency(amount):
    return f"₹{amount:,.2f}"

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def generate_session_id():
    return str(uuid.uuid4())

def get_chat_preview(messages, max_length=50):
    if not messages:
        return "Empty chat"
    
    for msg in messages:
        if msg["role"] == "user":
            content = msg["content"]
            if len(content) > max_length:
                return content[:max_length] + "..."
            return content
    
    return "No user messages"

@st.cache_data(ttl=30)
def load_history_file():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_history_file(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_all_chat_sessions(username):
    history = load_history_file()
    return history.get(username, [])

def save_chat_session(username, session_state, messages, session_id=None):
    if not messages or len(messages) == 0:
        return None
    
    history = load_history_file()
    user_sessions = history.get(username, [])
    
    if session_id:
        # Update existing session
        found = False
        for session in user_sessions:
            if session["session_id"] == session_id:
                session["messages"] = messages
                session["preview"] = get_chat_preview(messages)
                session["timestamp"] = get_timestamp()
                found = True
                break
        
        # Also update in-memory session_state for immediate UI feedback
        for session in session_state.chat_sessions:
            if session["session_id"] == session_id:
                session["messages"] = messages
                session["preview"] = get_chat_preview(messages)
                session["timestamp"] = get_timestamp()
                break
    else:
        # Create new session
        session_id = generate_session_id()
        new_session = {
            "session_id": session_id,
            "timestamp": get_timestamp(),
            "messages": messages,
            "preview": get_chat_preview(messages)
        }
        user_sessions.insert(0, new_session)
        
        if "chat_sessions" not in session_state:
            session_state.chat_sessions = []
        session_state.chat_sessions.insert(0, new_session)

    history[username] = user_sessions
    save_history_file(history)
    return session_id

def load_chat_session(username, session_id):
    user_sessions = get_all_chat_sessions(username)
    for session in user_sessions:
        if session["session_id"] == session_id:
            return session["messages"]
    return None

def delete_chat_session(username, session_state, session_id):
    history = load_history_file()
    user_sessions = history.get(username, [])
    
    user_sessions = [s for s in user_sessions if s["session_id"] != session_id]
    history[username] = user_sessions
    save_history_file(history)
    
    if "chat_sessions" in session_state:
        session_state.chat_sessions = [s for s in session_state.chat_sessions if s["session_id"] != session_id]
    return True

def clear_all_chat_history(username, session_state):
    history = load_history_file()
    history[username] = []
    save_history_file(history)
    
    session_state.chat_sessions = []
    return True

@st.cache_data(ttl=10)
def check_ollama_connection():
    """
    Checks if the local Ollama server is running.
    """
    try:
        # A 2s timeout here can block the main thread; caching reduces this impact
        response = requests.get("http://127.0.0.1:11434/", timeout=2)
        return response.status_code == 200
    except:
        return False

def get_faq_response(prompt):
    """
    Checks if the user's prompt matches any common frequently asked questions
    using the structured intents.json data.
    """
    prompt_lower = prompt.lower().strip()
    
    if not intents_data or "intents" not in intents_data:
        return None

    # Iterate through intents to find a matching pattern
    for intent in intents_data["intents"]:
        for pattern in intent["patterns"]:
            p_lower = pattern.lower()
            # For short patterns (like 'hi'), use word boundary check
            if len(p_lower) <= 3:
                if re.search(rf"\b{re.escape(p_lower)}\b", prompt_lower):
                    return random.choice(intent["responses"])
            # For longer patterns, substring match is usually fine and more flexible
            elif p_lower in prompt_lower:
                return random.choice(intent["responses"])
            
    return None
