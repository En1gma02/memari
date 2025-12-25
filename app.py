"""
app.py - Streamlit Frontend for Ari Chatbot

3-pane WhatsApp-style interface:
- Left (20%): Chat history from CHAT.txt
- Center (60%): Active chat with Ari
- Right (20%): Debug panel (tools, context, reasoning)
"""

import streamlit as st
import requests
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# ==============================================================================
# CONFIGURATION
# ==============================================================================

API_BASE_URL = "http://localhost:8000"
CHAT_HISTORY_PATH = Path("CHAT.txt")

# Page config
st.set_page_config(
    page_title="Chat with Ari",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Global text size reduction */
    .stMarkdown, .stText {
        font-size: 0.85rem !important;
    }
    
    /* User message bubble - light green with dark text */
    .user-bubble {
        background-color: #d1f4cc;
        color: #1a1a1a;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 4px 0;
        max-width: 70%;
        margin-left: auto;
        text-align: right;
        font-size: 0.9rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Ari message bubble - light gray with dark text */
    .ari-bubble {
        background-color: #f0f0f0;
        color: #1a1a1a;
        padding: 8px 12px;
        border-radius: 8px;
        margin: 4px 0;
        max-width: 70%;
        border: 1px solid #d0d0d0;
        font-size: 0.9rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Debug sections - compact */
    .debug-section {
        background-color: #f8f9fa;
        padding: 6px 8px;
        border-radius: 4px;
        margin: 6px 0;
        font-size: 0.75rem;
        border-left: 3px solid #4CAF50;
    }
    
    /* Chat history - dark text on light background */
    .chat-history {
        background-color: #fafafa;
        color: #2a2a2a;
        padding: 8px;
        border-radius: 4px;
        max-height: 500px;
        overflow-y: auto;
        font-size: 0.75rem;
        line-height: 1.3;
        border: 1px solid #e0e0e0;
    }
    
    /* Column headers - more compact */
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        font-size: 1.2rem !important;
        margin-bottom: 0.3rem !important;
        margin-top: 0.5rem !important;
    }
    
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    /* Make chat input sticky to bottom CUSTOM*/
    .stChatInputContainer {
        position: sticky !important;
        bottom: 0 !important;
        background: white !important;
        padding: 10px 0 !important;
        z-index: 100 !important;
    }
    
    /* Reduce padding globally */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* Caption text smaller */
    .caption {
        font-size: 0.7rem !important;
        color: #666 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SESSION STATE
# ==============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

if "debug_info" not in st.session_state:
    st.session_state.debug_info = {
        "tools_called": [],
        "context_retrieved": "",
        "reasoning": ""
    }

# ==============================================================================
# API CALLS
# ==============================================================================

def send_message(message: str) -> Dict:
    """Send message to the backend API."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "session_id": st.session_state.session_id,
                "message": message
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

def check_health() -> bool:
    """Check if the backend is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# ==============================================================================
# UI COMPONENTS
# ==============================================================================

def load_chat_history() -> str:
    """Load CHAT.txt for display."""
    if CHAT_HISTORY_PATH.exists():
        with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "No chat history available."

def display_message(role: str, content: str):
    """Display a message bubble."""
    if role == "user":
        st.markdown(f'<div class="user-bubble">{content}</div>', unsafe_allow_html=True)
    else:  # ari
        st.markdown(f'<div class="ari-bubble">{content}</div>', unsafe_allow_html=True)

# ==============================================================================
# MAIN LAYOUT
# ==============================================================================

# Check backend health
if not check_health():
    st.error("⚠️ Backend server is not running. Please start it with: `cd backend && uvicorn main:app --reload`")
    st.stop()

# Title
st.title("💬 Chat with Ari")
st.caption(f"Session: {st.session_state.session_id}")

# Create 3-column layout
left_col, center_col, right_col = st.columns([1, 3, 1])

# ==============================================================================
# LEFT PANE: Chat History
# ==============================================================================

with left_col:
    st.markdown("### 📜 History")
    st.caption("Reference DB")
    
    chat_history_text = load_chat_history()
    # Display history in scrollable div with better formatting
    history_html = f'<div class="chat-history"><pre style="margin:0; white-space: pre-wrap; font-family: monospace;">{chat_history_text[:2000]}...</pre></div>'
    st.markdown(history_html, unsafe_allow_html=True)
    
    if st.button("🔄", key="reload_hist", help="Reload history"):
        st.rerun()

# ==============================================================================
# CENTER PANE: Active Chat
# ==============================================================================

with center_col:
    st.markdown("### 💭 Conversation")
    
    # Chat messages container (with fixed height for scrolling)
    chat_container = st.container(height=450)
    
    with chat_container:
        # Display all messages
        for msg in st.session_state.messages:
            if isinstance(msg["content"], list):
                # Multiple Ari messages (WhatsApp style)
                for bubble in msg["content"]:
                    display_message(msg["role"], bubble)
            else:
                # Single message
                display_message(msg["role"], msg["content"])
    
    # Spacer to push input to bottom
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Chat input (sticky to bottom via CSS)
    user_input = st.chat_input("Type your message...", key="chat_input")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Send to API
        with st.spinner("Ari is typing..."):
            response = send_message(user_input)
        
        if response:
            # Add Ari's response (multiple bubbles)
            st.session_state.messages.append({
                "role": "ari",
                "content": response["messages"]
            })
            
            # Update debug info
            if response.get("tool_calls_made"):
                st.session_state.debug_info["tools_called"] = response["tool_calls_made"]
            
            if response.get("retrieved_context"):
                st.session_state.debug_info["context_retrieved"] = response["retrieved_context"]
            
            if response.get("reasoning"):
                st.session_state.debug_info["reasoning"] = response["reasoning"]
            
            # Rerun to show new messages
            st.rerun()

# ==============================================================================
# RIGHT PANE: Ari's Brain (Debug Panel)
# ==============================================================================

with right_col:
    st.markdown("### 🧠 Debug")
    st.caption("Ari's Brain")
    
    # Active Tools
    st.markdown("**🔧 Tools**")
    if st.session_state.debug_info["tools_called"]:
        for tool in st.session_state.debug_info["tools_called"]:
            st.markdown(f"<div class='debug-section'>✓ {tool}</div>", unsafe_allow_html=True)
    else:
        st.caption("_None_")
    
    # Retrieved Context
    st.markdown("**📚 Context**")
    if st.session_state.debug_info["context_retrieved"]:
        with st.expander("View", expanded=False):
            st.text(st.session_state.debug_info["context_retrieved"][:300] + "...")
    else:
        st.caption("_None_")
    
    # Session controls
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️", key="clear_btn", help="Clear chat"):
            st.session_state.messages = []
            st.session_state.debug_info = {
                "tools_called": [],
                "context_retrieved": "",
                "reasoning": ""
            }
            st.rerun()
    
    with col2:
        if st.button("💾", key="save_btn", help="End & index session"):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/end-session",
                    json={"session_id": st.session_state.session_id}
                )
                if response.status_code == 200:
                    st.success("✓ Indexed!", icon="✅")
                    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    st.session_state.messages = []
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
