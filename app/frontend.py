import sqlite3
import streamlit as st
from backend import query_rag_pipeline

# Page Configuration
st.set_page_config(page_title="ContextGuard", layout="centered")

# Database Path
DB_PATH = "users.db"

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []


# Authentication Logic
def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT password, role
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    if user:
        stored_password, role = user

        if stored_password == password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["role"] = role

            st.success(f"Welcome back, {username}!")
            st.rerun()

    st.error("Invalid username or password.")

def logout_user():
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.session_state["messages"] = []
    st.rerun()


# Interface Rendering
if not st.session_state["authenticated"]:
    # LOGIN FORM
    st.title("🔒 Sign In")
    st.write("Please enter your credentials to access the portal.")

    with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login", use_container_width=True)

        if submit_button:
            if username_input and password_input:
                login_user(username_input, password_input)
            else:
                st.warning("Please fill in both fields.")

else:
    # MAIN PROTECTED CONTENT
    st.sidebar.title(f"👤 {st.session_state['username']}")
    st.sidebar.write(f"**Role:** {st.session_state['role'].capitalize()}")

    if st.sidebar.button("Logout", use_container_width=True):
        logout_user()

    # Render previous message history
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input & Processing
    if prompt := st.chat_input("Ask a question about your department's documents..."):
        # Display user message
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and stream assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching authorized docs..."):
                stream_generator = query_rag_pipeline(prompt, st.session_state["role"])
                full_response = st.write_stream(stream_generator)
        
        # Save complete streamed output to session state history
        st.session_state["messages"].append({"role": "assistant", "content": full_response})