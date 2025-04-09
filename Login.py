import streamlit as st
import requests
from streamlit_javascript import st_javascript
import urllib.parse
from streamlit_url_fragment import get_fragment
from streamlit_cookies_controller import CookieController

SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]
REDIRECT_URI = st.secrets["google"]["REDIRECT_URI"]
cookie_manager = CookieController()

st.set_page_config(layout="wide", page_title="Alcor Prime Login")

def get_auth_code():
    return st.query_params.get("code")

def get_access_token_from_fragment():
    fragment = st_javascript("window.location.hash")
    if fragment and "access_token=" in fragment:
        parsed = urllib.parse.parse_qs(fragment.lstrip("#"))
        return parsed.get("access_token", [None])[0]
    return None

def exchange_code_for_token(code):
    token_url = f"{SUPABASE_URL}/auth/v1/token"
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY,
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(token_url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to exchange code for token: {response.text}")
        return None

def main():
    st.cache_data.clear()

    st.markdown("""
        <div style="text-align: center; margin-top: 40px; margin-bottom: 20px">
            <h2>Alcor Prime Dashboard Login</h2>
            <p>Sign in with your company's Google account</p>
        </div>
    """, unsafe_allow_html=True)

    code = get_auth_code()
    fragment = get_fragment()

    if fragment and "#access_token=" in fragment:
        parsed = urllib.parse.parse_qs(fragment)
        access_token = parsed.get("#access_token", [None])[0]
        access_token
        
        st.info("Authorization code received. Exchanging for token...")
        st.session_state["access_token"] = access_token

        st.success("Redirecting to dashboard...")
        st.switch_page("pages/1_Dashboard.py")
    else:
        login_url = f"{SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to={REDIRECT_URI}"

        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; margin-top: 40px;">
                <a href="{login_url}" style="text-decoration: none;">
                    <button style="
                        font-size: 16px;
                        padding: 15px 30px;
                        border-radius: 30px;
                        border: 2px solid gray;
                        background-color: white;
                        cursor: pointer;
                        display: flex;
                        align-items: center;
                    ">
                        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                            width="20" style="margin-right: 10px;" />
                        Sign in with Google
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()