import streamlit as st
from typing import Dict

# 1. Page Configuration
st.set_page_config(page_title="ContextGuard", layout="centered")

# Dummy user database
users_db: Dict[str, Dict[str, str]] = {
    "Tony": {"password": "password123", "role": "engineering"},
    "Bruce": {"password": "securepass", "role": "marketing"},
    "Sam": {"password": "financepass", "role": "finance"},
    "Peter": {"password": "pete123", "role": "engineering"},
    "Sid": {"password": "sidpass123", "role": "marketing"},
    "Natasha": {"password": "hrpass123", "role": "hr"}
}

# 2. Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""


# 3. Authentication Logic
def login_user(username, password):
    user = users_db.get(username)
    if user and user["password"] == password:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username
        st.session_state["role"] = user["role"]
        st.success(f"Welcome back, {username}!")
        st.rerun()
    else:
        st.error("Invalid username or password.")


def logout_user():
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""
    st.rerun()


# 4. Interface Rendering
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

    st.title("🚀 AI Document Assistant")
    st.write(f"Hello **{st.session_state['username']}**! You have successfully logged in.")
    
    # Example content specific to roles
    st.info(f"Access granted for the **{st.session_state['role']}** workspace.")