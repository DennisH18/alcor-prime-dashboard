import streamlit as st
from supabase import create_client
import services.auth as auth

# Supabase client
SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🔐 Login with Google")

if st.button("Sign in with Google"):
    response = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
            "redirect_to": "http://localhost:8501"
        }
    })
    st.markdown(f"""
    <meta http-equiv="refresh" content="0;url={response.url}" />
    <script>window.location.replace("{response.url}");</script>
    """, unsafe_allow_html=True)

access_token = auth.extract_access_token_from_fragment()
access_token

auth.set_access_token_cookie(access_token)

st.write(auth.get_access_token_from_cookie())