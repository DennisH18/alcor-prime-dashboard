# pages/0_Login.py
import streamlit as st
from services.supabaseService import supabase_client

st.set_page_config(layout="centered", page_title="Login")

st.title("🔐 Login to Alcor Prime Dashboard")
st.write("Sign in with your Google account to continue.")

# Supabase will redirect back to this page after login
REDIRECT_URI = "https://alcor-prime-dashboard.streamlit.app/~/+/Login_Redirect"  # Update if needed

response = supabase_client.auth.sign_in_with_oauth(
    {
        "provider": "google",
        "options": {
            "redirect_to": REDIRECT_URI
        }
    }
)

login_button = f"""
<div style="display: flex; justify-content: center;">
    <a href="{response.url}" target="_self">
        <button style="font-size: 16px; padding: 10px 20px; border-radius: 5px;">
            Sign in with Google
        </button>
    </a>
</div>
"""
st.markdown(login_button, unsafe_allow_html=True)