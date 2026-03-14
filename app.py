import ollama
import streamlit as st
import difflib

from faqs import faqs
from faq_aliases import FAQ_ALIASES

# Page Configuration
st.set_page_config(
    page_title="BankBot AI Chatbot",
    page_icon="🏦",
    layout="centered"
)

# Banking Keywords (Domain Filter)
BANK_KEYWORDS = [
    "bank", "account", "atm", "loan", "interest",
    "balance", "deposit", "withdraw", "credit",
    "debit", "transaction", "branch", "net banking"
]

# Check Banking Domain
def is_banking_query(query):
    query = query.lower()

    # Check keywords
    for keyword in BANK_KEYWORDS:
        if keyword in query:
            return True

    # Check FAQ aliases
    for alias in FAQ_ALIASES.keys():
        if alias in query:
            return True

    # Check FAQ questions
    for faq in faqs.keys():
        if any(word in query for word in faq.split()):
            return True
    return False

# Spell Correction
def correct_spelling(question, faq_questions):
    # First, check for any direct matches in the FAQ aliases
    for alias, alias_question in FAQ_ALIASES.items():
        if alias in question:
            return alias_question

    # Use difflib to find the closest match for the user's question
    matches = difflib.get_close_matches(
        question, 
        faq_questions, 
        n=1, 
        cutoff=0.6
    )

    # If a close match is found, return it; otherwise, return the original question
    if matches:
        return matches[0]
    return question

# FAQ Response
def get_bot_response(user_query, faqs):
    question = user_query.strip().lower()
    user_question = correct_spelling(question, faqs.keys())

    # First, check for an exact match
    if user_question in faqs:
        return faqs[user_question]

    # Next, check for partial matches
    for faq_question, answer in faqs.items():
        if user_question in faq_question or faq_question in user_question:
            return answer

    # Finally, check for common keywords
    user_words = set(user_question.split())
    best_match = None
    best_score = 0
    for faq_question, answer in faqs.items():
        faq_words = set(faq_question.split())
        common_words = user_words.intersection(faq_words)
        if len(common_words) > best_score:
            best_score = len(common_words)
            best_match = answer

    if best_score > 0:
        return best_match

    # If no matches found, return a default response
    return None

# AI Response using Ollama
def get_ai_response(user_query):
    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role": "system",
                "content": "You are BankBot, a professional banking assistant. Answer only banking-related questions clearly and briefly in 2 - 5 short sentences. If the question is not related to banking, politely inform the user that you can only answer banking-related questions."
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )
    return response["message"]["content"]

# Session State
if "conversations" not in st.session_state:
    st.session_state.conversations = {
        "Chat 1" : {"title": "New Chat", "messages": []}
    }
    st.session_state.current_chat = "Chat 1"
    st.session_state.chat_count = 1

# Sidebar
with st.sidebar:
    st.title("🏦 BankBot Menu")
    st.caption("Your banking FAQ assistant")
    st.divider()

    # Button to start a new chat
    if st.button("➕ New Chat"):
        st.session_state.chat_count += 1
        chat_id = f"Chat {st.session_state.chat_count}"
        st.session_state.conversations[chat_id] = {
            "title": "New Chat", 
            "messages": []
        }
        st.session_state.current_chat = chat_id
        st.rerun()

    # List existing chats and allow switching between them
    for chat_id, chat_data in st.session_state.conversations.items():
        if st.button(chat_data["title"], key=chat_id):
            st.session_state.current_chat = chat_id
            st.rerun()

    st.divider()

    # Button to clear chat history
    if st.button("🧹 Clear Chat History"):
        st.session_state.conversations = {
            "Chat 1" : {"title": "New Chat", "messages": []}
        }
        st.session_state.current_chat = "Chat 1"
        st.session_state.chat_count = 1
        st.rerun()

# Main Interface
st.title("🏦 BankBot AI Chatbot")
st.caption("Welcome! Ask me banking-related questions.")
st.divider()

# Display sample FAQs
st.markdown("- **What is a savings account?**")
st.markdown("- **How to open a bank account?** ")
st.markdown("- **What is ATM?**")
st.markdown("- **What is interest rate?**")
st.markdown("- **How to check account balance?**")
st.divider()

# Get the current chat conversation
current_chat = st.session_state.conversations[st.session_state.current_chat]
current_messages = current_chat["messages"]

# Display the conversation history
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input box for user queries
user_query = st.chat_input("Enter your question...")

# Process the user query and generate bot response
if user_query:
    # Set chat title based on first user query
    if current_chat["title"] == "New Chat":
        title = user_query.strip().capitalize()
        if len(title) > 30:
            title = title[:27] + "..."
        current_chat["title"] = title

    # Append user message to conversation history
    current_chat["messages"].append(
        {"role": "user", "content": user_query}
    )

    # First check FAQ
    bot_response = get_bot_response(user_query, faqs)

    if bot_response is None:
        # Then check banking domain
        if not is_banking_query(user_query):
            bot_response = "⚠️ I can only answer banking related questions."
        else:
            with st.spinner("BankBot is thinking..."):
                try:
                    bot_response = get_ai_response(user_query)
                except Exception:
                    bot_response = "⚠️ Sorry, AI service is temporarily unavailable. Please try later."

    # Append bot response to conversation history
    current_chat["messages"].append(
        {"role": "assistant", "content": f"{bot_response}"}
    )

    st.rerun()