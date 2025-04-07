import streamlit as st
from supabase import create_client
from streamlit_url_fragment import get_fragment
from streamlit_cookies_controller import CookieController

SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

cookie_manager = CookieController()

def extract_access_token_from_fragment():
    fragment = get_fragment()
    if not fragment:
        return None
    params = dict(x.split("=") for x in fragment.split("&") if "=" in x)
    return params.get("#access_token")

def main():


    st.title("🔐 Google Login")

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

    fragment = get_fragment()
    if not fragment:
        return None
    params = dict(x.split("=") for x in fragment.split("&") if "=" in x)

    access_token = params.get("#access_token")

    if access_token:
        cookie_manager.set("access_token", access_token)

    token = cookie_manager.get("access_token")
    st.write(token)

    user = supabase.auth.get_user(token)
    st.write(user)
    
if __name__ == "__main__":
    main()
