import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
from utils import (
    validate_email, 
    validate_password_strength, 
    format_currency,
    get_timestamp,
    save_chat_session,
    load_chat_session,
    delete_chat_session,
    clear_all_chat_history,
    persist_user,
    get_persisted_users,
    save_active_session,
    get_active_session,
    clear_active_session,
    get_ollama_response,
    stream_ollama_response,
    check_ollama_connection,
    get_all_chat_sessions,
    save_chat_session,
    load_chat_session,
    delete_chat_session,
    clear_all_chat_history,
    get_faq_response,
    rewrite_banking_response,
    is_banking_query
)

st.set_page_config(
    page_title="Central Bank AI",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_custom_style(theme="dark"):
    # Define color palette based on theme
    if theme == "dark":
        colors = {
            "bg": "#0B1220",
            "card_bg": "#111827",
            "text": "#f1f5f9",
            "text_secondary": "#94a3b8",
            "primary": "#2563EB",
            "secondary": "#0ea5e9",
            "border": "#1F2937",
            "input_bg": "rgba(30, 41, 59, 0.8)",
            "shadow": "rgba(0, 0, 0, 0.4)",
            "success": "#10B981",
            "warning": "#f59e0b",
            "danger": "#EF4444",
            "sidebar_bg": "#0F172A",
            "hover": "rgba(255, 255, 255, 0.05)"
        }
    else:
        colors = {
            "bg": "#F8FAFC",
            "card_bg": "#FFFFFF",
            "text": "#0F172A",
            "text_secondary": "#64748B",
            "primary": "#1E40AF",
            "secondary": "#2563EB",
            "border": "#E2E8F0",
            "input_bg": "#F8FAFC",
            "shadow": "rgba(0, 0, 0, 0.04)",
            "success": "#10B981",
            "warning": "#d97706",
            "danger": "#EF4444",
            "sidebar_bg": "#F1F5F9",
            "hover": "#EFF6FF"
        }

    st.session_state.colors = colors

    st.markdown(f"""
    <style>
    /* Import Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');
    
    /* Global Reset & Typography */
    .stApp {{
        font-family: 'Inter', sans-serif;
        color: {colors['text']};
        background-color: {colors['bg']};
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: {colors['text']};
        margin-bottom: 0.5rem;
    }}
    
    h1 {{ font-size: 32px !important; }}
    h2 {{ font-size: 24px !important; }}
    h3 {{ font-size: 18px !important; }}
    
    /* Layout Logic */
    .main .block-container {{
        padding-top: 5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
        margin: 0 auto;
    }}
    
    header[data-testid="stHeader"] {{
        background: transparent !important;
        box-shadow: none !important;
        height: 0 !important;
    }}
    
    [data-testid="stAppToolbar"] {{
        display: none !important;
    }}
    
    [data-testid="stSidebarCollapseButton"] {{
        visibility: hidden !important;
        opacity: 0 !important;
    }}

    /* Footer still hidden */
    footer {{
        display: none !important;
    }}

    /* Global Sidebar Styling */
    /* Global Sidebar Styling - Force visibility and width */
    section[data-testid="stSidebar"] {{
        background: {colors.get('sidebar_bg', '#F1F5F9')} !important;
        border-right: 1px solid {colors['border']} !important;
        min-width: 320px !important;
        width: 320px !important;
        visibility: visible !important;
        display: block !important;
    }}
    
    /* Ensure child containers allow visibility */
    [data-testid="stSidebarContent"] {{
        visibility: visible !important;
    }}
    
    /* Hide the 'collapsed' hamburger icon in the top left if it appears */
    [data-testid="collapsedControl"] {{
        display: none !important;
    }}

    /* Remove default sidebar top padding */
    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 2rem !important;
    }}

    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
    }}
    ::-webkit-scrollbar-thumb {{
        background: {colors['border']};
        border-radius: 10px;
    }}

    /* Section Titles */
    .section-title {{
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 8px;
        margin-top: 24px;
    }}

    /* User Card */
    .user-card {{
        background: {colors['card_bg']};
        padding: 14px;
        border-radius: 12px;
        border: 1px solid {colors['border']};
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: all 0.2s ease;
    }}
    .user-card:hover {{
        transform: translateX(2px);
        background: {colors.get('hover', 'rgba(255,255,255,0.05)')};
    }}
    .user-avatar {{
        background: {colors['primary']};
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
    }}
    .user-name {{
        font-weight: 600;
        font-size: 14px;
        color: {colors['text']};
    }}
    .user-email {{
        font-size: 12px;
        color: {colors['text_secondary']};
    }}

    /* Navigation / Sidebar Buttons */
    .sidebar-btn {{
        padding: 10px 14px;
        border-radius: 8px;
        color: #cbd5e1;
        transition: all 0.2s ease;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
    }}
    .sidebar-btn:hover {{
        background-color: {colors.get('hover', 'rgba(255,255,255,0.05)')};
        color: white;
        transform: translateX(2px);
    }}
    .sidebar-active {{
        background-color: rgba(37, 99, 235, 0.15);
        border-left: 3px solid {colors['primary']};
        color: white;
        border-radius: 0 8px 8px 0;
    }}

    /* Chat History */
    .chat-history-container {{
        max-height: 250px;
        overflow-y: auto;
        margin-bottom: 24px;
        padding-right: 4px;
    }}
    .chat-item {{
        padding: 8px 10px;
        border-radius: 8px;
        color: #cbd5e1;
        transition: all 0.2s ease;
        font-size: 0.9rem;
        margin-bottom: 4px;
        cursor: pointer;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .chat-item:hover {{
        background: {colors.get('hover', 'rgba(255,255,255,0.05)')};
        color: white;
        transform: translateX(2px);
    }}

    /* Logout Button */
    .logout-btn button {{
        background: transparent !important;
        border: 1px solid {colors['danger']} !important;
        color: {colors['danger']} !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        width: 100%;
        padding: 8px !important;
    }}
    .logout-btn button:hover {{
        background: {colors['danger']} !important;
        color: white !important;
    }}

    /* AI Status Badge */
    .status-badge {{
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
        border: 1px solid {colors['border']};
    }}
    
    .status-online {{
        background: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border-color: rgba(16, 185, 129, 0.2);
    }}
    
    .status-offline {{
        background: rgba(239, 68, 68, 0.1);
        color: #ef4444;
        border-color: rgba(239, 68, 68, 0.2);
    }}
    
    /* Card Component */
    .bank-card {{
        background-color: {colors['card_bg']};
        border: 1px solid {colors['border']};
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 4px 15px {colors['shadow']};
        margin-bottom: 16px;
    }}
    
    /* Primary Buttons */
    .stButton>button {{
        border-radius: 8px;
        transition: 0.3s ease;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-2px);
    }}
    
    /* Chat Interface Styling */
    .user-bubble {{
        background: {colors['primary']};
        color: white;
        padding: 12px 20px;
        border-radius: 20px 20px 4px 20px;
        margin-bottom: 12px;
        max-width: 85%;
        margin-left: auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-size: 0.95rem;
        line-height: 1.5;
    }}
    
    .ai-bubble {{
        background: {colors['card_bg']};
        color: {colors['text']};
        padding: 12px 20px;
        border-radius: 20px 20px 20px 4px;
        margin-bottom: 12px;
        max-width: 85%;
        border: 1px solid {colors['border']};
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        font-size: 0.95rem;
        line-height: 1.5;
    }}

    /* Modern Chat Input Styling */
    section[data-testid="stChatInput"] {{
        padding-bottom: 2rem !important;
    }}
    
    section[data-testid="stChatInput"] > div {{
        background-color: transparent !important;
    }}

    section[data-testid="stChatInput"] textarea {{
        background-color: {colors['input_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 25px !important;
        padding: 12px 20px !important;
        color: {colors['text']} !important;
        box-shadow: 0 4px 12px {colors['shadow']} !important;
        transition: all 0.3s ease;
    }}

    section[data-testid="stChatInput"] textarea:focus {{
        border-color: {colors['primary']} !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
    }}
    
    /* Disable default Streamlit fading on rapid updates */
    div[data-testid="stVerticalBlock"] > div,
    div[data-testid="stVerticalBlock"],
    div.element-container, 
    div.stMarkdown, 
    div[data-testid="stMarkdownContainer"],
    div[data-testid="stChatMessage"] {{
        transition: none !important;
        animation: none !important;
        opacity: 1 !important;
    }}
    
    * {{
        animation: none !important;
    }}

    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    if "users" not in st.session_state:
        st.session_state.users = get_persisted_users()
    
    if "logged_in" not in st.session_state:
        last_user = get_active_session()
        if last_user and last_user in st.session_state.users:
            st.session_state.logged_in = True
            st.session_state.username = last_user
            st.session_state.email = st.session_state.users[last_user]["email"]
        else:
            st.session_state.logged_in = False
    
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    
    apply_custom_style(st.session_state.theme)
            
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "email" not in st.session_state:
        st.session_state.email = ""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "login"
    if "chat_sessions" not in st.session_state:
        if st.session_state.logged_in and st.session_state.username:
            st.session_state.chat_sessions = get_all_chat_sessions(st.session_state.username)
        else:
            st.session_state.chat_sessions = []
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "balance" not in st.session_state:
        st.session_state.balance = 850000.00
    if "interest_rate" not in st.session_state:
        st.session_state.interest_rate = 6.5
    if "accrued_interest" not in st.session_state:
        st.session_state.accrued_interest = 55000.00
    if "active_loans" not in st.session_state:
        st.session_state.active_loans = 2
    if "total_loan_amount" not in st.session_state:
        st.session_state.total_loan_amount = 3500000.00

init_session_state()

def login(username, password):
    if username in st.session_state.users:
        if st.session_state.users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.email = st.session_state.users[username]["email"]
            st.session_state.current_page = "dashboard"
            st.session_state.chat_sessions = get_all_chat_sessions(username)
            save_active_session(username)
            return True
    return False

def signup(username, email, password):
    if username in st.session_state.users:
        return False, "Username already exists"
    
    st.session_state.users[username] = {
        "email": email,
        "password": password
    }
    persist_user(username, email, password)
    return True, "Account created successfully!"

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.email = ""
    st.session_state.current_page = "login"
    st.session_state.messages = []
    st.session_state.current_chat_id = None
    clear_active_session()

def get_mock_transactions():
    dates = pd.date_range(end=pd.Timestamp.now(), periods=30, freq='D')
    
    types = []
    amounts = []
    cats = []
    for _ in range(30):
        if np.random.random() > 0.8:
            types.append("Income")
            cats.append(np.random.choice(["Salary", "Investment", "Refund"]))
            amounts.append(round(float(np.random.uniform(5000, 25000)), 2))
        else:
            types.append("Expense")
            cats.append(np.random.choice(["Food", "Rent", "Shopping", "Transport", "Entertainment", "Utilities"]))
            amounts.append(round(float(np.random.uniform(100, 5000)), 2))
            
    data = {"Date": dates, "Category": cats, "Type": types, "Amount": amounts}
    return pd.DataFrame(data)

def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏦 Central Bank AI")
        st.subheader("Login")
        st.divider()
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.divider()
        if st.button("Don't have an account? Sign Up", use_container_width=True):
            st.session_state.current_page = "signup"
            st.rerun()

def show_signup_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏦 Central Bank AI")
        st.subheader("Create Account")
        st.divider()
        
        with st.form("signup_form"):
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
            submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            
            if submit:
                if not username or not email or not password or not confirm_password:
                    st.error("All fields are required")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, msg = signup(username, email, password)
                    if success:
                        st.success(msg)
                        st.info("Please login with your credentials")
                        st.session_state.current_page = "login"
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
        
        st.divider()
        if st.button("Already have an account? Login", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()

def show_dashboard():
    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 0 0 1rem 0; text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🏦</div>
            <h2 style="margin: 0; font-size: 1.3rem !important; font-family: 'Poppins', sans-serif;">Central Bank AI</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # User Info Section (New CSS Class)
        st.markdown(f"""
        <div class="user-card">
            <div class="user-avatar">
                {st.session_state.username[0].upper() if st.session_state.username else 'U'}
            </div>
            <div>
                <div class="user-name">{st.session_state.username}</div>
                <div class="user-email">{st.session_state.email}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if "current_tab" not in st.session_state:
            st.session_state.current_tab = "Dashboard"

        st.markdown("<div class='section-title'>Navigation</div>", unsafe_allow_html=True)
        
        nav_btn_style1 = "primary" if st.session_state.current_tab == "Dashboard" else "secondary"
        nav_btn_style2 = "primary" if st.session_state.current_tab == "Banking Assistant" else "secondary"
        
        if st.button("📊 Dashboard", use_container_width=True, type=nav_btn_style1):
            st.session_state.current_tab = "Dashboard"
            st.rerun()
            
        if st.button("� Banking Assistant", use_container_width=True, type=nav_btn_style2):
            st.session_state.current_tab = "Banking Assistant"
            st.rerun()
            
        page = st.session_state.current_tab
        
        st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

        st.markdown("<div class='logout-btn'>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Push Chat History to the bottom
        st.markdown("<div style='flex-grow: 1; min-height: 40px;'></div>", unsafe_allow_html=True) 
        
        st.markdown("<div class='section-title'>Recent Chats</div>", unsafe_allow_html=True)
        
        new_col, clear_col = st.columns([1, 1])
        with new_col:
            if st.button("➕ New Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.current_chat_id = None
                st.rerun()
        with clear_col:
            if st.session_state.chat_sessions and st.button("🗑️ Clear All", use_container_width=True):
                clear_all_chat_history(st.session_state.username, st.session_state)
                st.session_state.messages = []
                st.session_state.current_chat_id = None
                st.rerun()

        # Chat Sessions
        st.markdown("<div class='chat-history-container'>", unsafe_allow_html=True)
        if st.session_state.chat_sessions:
            # Display only top 5 initially, or all if "show_all_chats" is True
            if "show_all_chats" not in st.session_state:
                st.session_state.show_all_chats = False
            
            display_chats = st.session_state.chat_sessions if st.session_state.show_all_chats else st.session_state.chat_sessions[:5]
            
            for chat in display_chats:
                preview = chat.get('preview', 'No messages')
                chat_id = chat['session_id']
                
                chat_col1, chat_col2 = st.columns([4, 1])
                with chat_col1:
                    if st.button(f"📄 {preview}", key=f"chat_{chat_id}", use_container_width=True):
                        st.session_state.messages = chat['messages']
                        st.session_state.current_chat_id = chat_id
                        st.rerun()
                with chat_col2:
                    if st.button("❌", key=f"del_{chat_id}", use_container_width=True):
                        delete_chat_session(st.session_state.username, st.session_state, chat_id)
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.messages = []
                            st.session_state.current_chat_id = None
                        st.rerun()
            
            # Show "See all" button if there are more than 5 chats
            if len(st.session_state.chat_sessions) > 5:
                if st.session_state.show_all_chats:
                    if st.button("See Less", use_container_width=True):
                        st.session_state.show_all_chats = False
                        st.rerun()
                else:
                    if st.button(f"See All ({len(st.session_state.chat_sessions)})", use_container_width=True):
                        st.session_state.show_all_chats = True
                        st.rerun()
        else:
            st.caption("No recent chats")
        st.markdown("</div>", unsafe_allow_html=True)

    st.title("Dashboard" if page == "Dashboard" else "Banking Assistant")
    
    if page == "Dashboard":
        st.markdown("## 📊 Dashboard Overview")
        
        # Custom Metric Cards
        st.markdown(f"""
        <div style="display: flex; gap: 20px; margin-bottom: 2rem;">
            <div class="bank-card" style="flex: 1; text-align: center;">
                <div style="color: {st.session_state.colors['text_secondary']}; font-size: 0.9rem; margin-bottom: 8px;">Account Balance</div>
                <div style="font-size: 1.8rem; font-weight: 700;">{format_currency(st.session_state.balance)}</div>
            </div>
            <div class="bank-card" style="flex: 1; text-align: center;">
                <div style="color: {st.session_state.colors['text_secondary']}; font-size: 0.9rem; margin-bottom: 8px;">Interest Rate</div>
                <div style="font-size: 1.8rem; font-weight: 700;">{st.session_state.interest_rate}%</div>
            </div>
            <div class="bank-card" style="flex: 1; text-align: center;">
                <div style="color: {st.session_state.colors['text_secondary']}; font-size: 0.9rem; margin-bottom: 8px;">Active Loans</div>
                <div style="font-size: 1.8rem; font-size: 1.8rem; font-weight: 700;">{st.session_state.active_loans}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)

        # 2 & 3. Insights & Health Score
        col_health, col_insights = st.columns(2)
        with col_health:
            st.markdown(f"""
            <div class="bank-card" style="height: 100%;">
                <h3 style="margin-top:0;">🟢 Financial Health Score</h3>
                <div style="font-size: 2.5rem; font-weight: 700; color: {st.session_state.colors['primary']};">78 <span style="font-size: 1rem; color: {st.session_state.colors['text_secondary']};">/ 100</span></div>
                <div style="margin-top: 10px; font-size: 0.95rem; color: {st.session_state.colors['text_secondary']};">
                    <div style="margin-bottom: 4px;">✓ Good savings ratio</div>
                    <div style="margin-bottom: 4px;">✓ Low EMI burden</div>
                    <div>✓ Stable spending</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_insights:
            st.markdown(f"""
            <div class="bank-card" style="height: 100%;">
                <h3 style="margin-top:0;">💡 Smart Insights</h3>
                <div style="margin-top: 15px; font-size: 0.95rem; line-height: 1.6;">
                    <div style="margin-bottom: 8px;">📈 This month your spending increased by <b>12%</b> compared to last month.</div>
                    <div style="margin-bottom: 8px;">🛍️ Most spending category: <b>Shopping</b>.</div>
                    <div>⚠️ EMI due in <b>5 days</b>.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
            
        # 4 & 5. Net Worth & Upcoming Dues
        col_nw, col_dues = st.columns(2)
        with col_nw:
            st.markdown(f"""
            <div class="bank-card" style="height: 100%;">
                <h3 style="margin-top:0;">💎 Net Worth</h3>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 1rem;">
                    <span style="color: {st.session_state.colors['text_secondary']};">Assets (Savings + FD + Investments)</span>
                    <span style="font-weight: 600; color: {st.session_state.colors['success']};">{format_currency(st.session_state.balance + 3500000)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 16px; border-bottom: 1px solid {st.session_state.colors['border']}; padding-bottom: 12px; font-size: 1rem;">
                    <span style="color: {st.session_state.colors['text_secondary']};">Liabilities (Loans + Credit Dues)</span>
                    <span style="font-weight: 600; color: {st.session_state.colors['danger']};">{format_currency(st.session_state.total_loan_amount)}</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; font-size: 1.1rem;">Total Net Worth</span>
                    <span style="font-size: 1.5rem; font-weight: 700; color: {st.session_state.colors['primary']};">{format_currency(st.session_state.balance + 3500000 - st.session_state.total_loan_amount)}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_dues:
            st.markdown(f"""
            <div class="bank-card" style="height: 100%;">
                <h3 style="margin-top:0;">📅 Upcoming Payments</h3>
                <div style="margin-top: 15px; font-size: 1rem; line-height: 1.6;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <span>Home Loan EMI</span>
                        <div><span style="font-weight: 600;">₹12,000</span> <span style="font-size: 0.85rem; color: {st.session_state.colors['text_secondary']};">due 5 Mar</span></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                        <span>Credit Card Bill</span>
                        <div><span style="font-weight: 600;">₹8,400</span> <span style="font-size: 0.85rem; color: {st.session_state.colors['text_secondary']};">due 9 Mar</span></div>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Electricity Bill</span>
                        <div><span style="font-weight: 600;">₹1,500</span> <span style="font-size: 0.85rem; color: {st.session_state.colors['text_secondary']};">due 2 Mar</span></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        
        # Visualizations
        col_left, col_right = st.columns([2, 1])
        df = get_mock_transactions()
        
        with col_left:
            st.write("### 📉 Income vs Expenses")
            daily_data = df.groupby(['Date', 'Type'])['Amount'].sum().reset_index()
            fig_bar = px.bar(
                daily_data, 
                x='Date', 
                y='Amount', 
                color='Type',
                barmode='group',
                color_discrete_map={"Income": st.session_state.colors['success'], "Expense": st.session_state.colors['danger']}
            )
            fig_bar.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            if st.session_state.theme == "dark":
                fig_bar.update_layout(font_color="white")
            else:
                fig_bar.update_layout(font_color="black")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_right:
            st.write("### 🍰 Expenses Breakdown")
            expense_df = df[df['Type'] == 'Expense']
            if expense_df.empty:
                st.info("No expenses recorded yet.")
            else:
                category_data = expense_df.groupby('Category')['Amount'].sum().reset_index()
                fig = px.pie(
                    category_data, 
                    values='Amount', 
                    names='Category',
                    hole=0.4,
                    color_discrete_sequence=[st.session_state.colors['primary'], st.session_state.colors['secondary'], '#38bdf8', '#818cf8', '#a78bfa', '#f472b6']
                )
                fig.update_layout(
                    margin=dict(t=0, b=0, l=0, r=0), 
                    height=300,
                    showlegend=False
                )
                # Ensure transparent background for the chart
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                if st.session_state.theme == "dark":
                    fig.update_layout(font_color="white")
                else:
                    fig.update_layout(font_color="black")
                    
                st.plotly_chart(fig, use_container_width=True)

        st.divider()
        
        # Consolidated Transactions
        st.markdown("### 📝 Recent Transaction History")
        st.dataframe(
            df.sort_values(by="Date", ascending=False), 
            use_container_width=True, 
            hide_index=True
        )

    else:
        is_connected = check_ollama_connection()
        col_h1, col_h2 = st.columns([4, 1])
        with col_h2:
            if is_connected:
                st.markdown('<div class="status-badge status-online"><span>●</span> Online</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-badge status-offline"><span>○</span> Offline</div>', unsafe_allow_html=True)
        
        # AI Status is now in the header, no redundant box needed
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        
        # FAQ Suggestions
        st.markdown("<div style='margin-bottom: 10px; font-size: 0.9rem; color: #64748b;'><strong>Popular Questions:</strong></div>", unsafe_allow_html=True)
        
        faq_row1_col1, faq_row1_col2, faq_row1_col3 = st.columns(3)
        with faq_row1_col1:
            if st.button("💰 Balance?", use_container_width=True):
                st.session_state.faq_trigger = "What is my balance?"
                st.rerun()
        with faq_row1_col2:
            if st.button("📈 Interest?", use_container_width=True):
                st.session_state.faq_trigger = "What are the current interest rates?"
                st.rerun()
        with faq_row1_col3:
            if st.button("📞 Support", use_container_width=True):
                st.session_state.faq_trigger = "How do I contact customer care?"
                st.rerun()
        
        faq_row2_col1, faq_row2_col2, faq_row2_col3 = st.columns(3)
        with faq_row2_col1:
            if st.button("🕒 Hours", use_container_width=True):
                st.session_state.faq_trigger = "What are the working hours?"
                st.rerun()
        with faq_row2_col2:
            if st.button("🏦 Min Bal", use_container_width=True):
                st.session_state.faq_trigger = "What is the minimum balance?"
                st.rerun()
        with faq_row2_col3:
            if st.button("📋 FD Rates", use_container_width=True):
                st.session_state.faq_trigger = "What are the FD rates?"
                st.rerun()
            
        chat_container = st.container(height=400, border=False)
        
        with chat_container:
            for message in st.session_state.messages:
                role = message["role"]
                if role == "user":
                    st.markdown(f'<div class="user-bubble">{message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="ai-bubble">{message["content"]}</div>', unsafe_allow_html=True)

        prompt = st.chat_input("Ask about your finances or banking services...")
        
        if getattr(st.session_state, 'faq_trigger', None):
            prompt = st.session_state.faq_trigger
            st.session_state.faq_trigger = None
            
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with chat_container:
                st.markdown(f'<div class="user-bubble">{prompt}</div>', unsafe_allow_html=True)
                
                faq_response = get_faq_response(prompt)
                
                res_box = st.empty()
                full_response = ""
                
                if faq_response:
                    full_response = faq_response
                    res_box.markdown(f'<div class="ai-bubble">{full_response}</div>', unsafe_allow_html=True)
                elif is_banking_query(prompt):
                    # Fallback to Ollama for unknown queries if it's banking related
                    if check_ollama_connection():
                        last_update_time = time.time()
                        for chunk in stream_ollama_response(prompt, history=st.session_state.messages[:-1]):
                            if chunk:
                                full_response += chunk
                                current_time = time.time()
                                if current_time - last_update_time > 0.05:
                                    res_box.markdown(f'<div class="ai-bubble">{full_response}▌</div>', unsafe_allow_html=True)
                                    last_update_time = current_time
                        
                        res_box.markdown(f'<div class="ai-bubble">{full_response}</div>', unsafe_allow_html=True)
                    else:
                        full_response = "I'm having trouble reaching the main AI engine right now. However, I can still help with basic queries like your balance or interest rates. How can I assist you?"
                        res_box.markdown(f'<div class="ai-bubble">{full_response}</div>', unsafe_allow_html=True)
                else:
                    # Non-banking refusal
                    full_response = "I am a banking assistant and can only answer banking-related queries. Please feel free to ask about accounts, loans, cards, or other financial services."
                    res_box.markdown(f'<div class="ai-bubble">{full_response}</div>', unsafe_allow_html=True)
            
            if not full_response:
                full_response = "I'm having trouble reaching the main AI engine right now. However, I can still help with basic queries like your balance or interest rates. How can I assist you?"
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            # Save using the persistent utility
            new_id = save_chat_session(st.session_state.username, st.session_state, st.session_state.messages, st.session_state.current_chat_id)
            if not st.session_state.current_chat_id:
                st.session_state.current_chat_id = new_id
            
            st.rerun()

if not st.session_state.logged_in:
    if st.session_state.current_page == "login":
        show_login_page()
    elif st.session_state.current_page == "signup":
        show_signup_page()
else:
    show_dashboard()
