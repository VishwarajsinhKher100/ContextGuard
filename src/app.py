import streamlit as st
from database import authenticate_user
from rag import query_rag_pipeline

# Page Configuration
st.set_page_config(page_title="ContextGuard", layout="centered")

# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Auth Actions
def handle_login(username, password):
    is_valid, role = authenticate_user(username, password)
    if is_valid:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["role"] = role
        st.success(f"Welcome back, {username}!")
        st.rerun()
    else:
        st.error("Invalid username or password.")

def handle_logout():
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.session_state["messages"] = []
    st.rerun()

# UI Rendering logic
if not st.session_state["authenticated"]:
    st.title("🔒 Sign In")
    st.write("Please enter your credentials to access the portal.")

    with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login", use_container_width=True)

        if submit_button:
            if username_input and password_input:
                handle_login(username_input, password_input)
            else:
                st.warning("Please fill in both fields.")

else:
    st.sidebar.title(f"👤 {st.session_state['username']}")
    st.sidebar.write(f"**Role:** {st.session_state['role'].capitalize()}")

    if st.sidebar.button("Logout", use_container_width=True):
        handle_logout()

    # Chat history rendering
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input & Processing
    if prompt := st.chat_input("Ask a question about your department's documents..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching authorized docs..."):
                stream_generator = query_rag_pipeline(prompt, st.session_state["role"])
                full_response = st.write_stream(stream_generator)
        
        st.session_state["messages"].append({"role": "assistant", "content": full_response})