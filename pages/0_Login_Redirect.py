import streamlit as st
import urllib.parse
from streamlit_cookies_controller import CookieController
from services.supabaseService import supabase_client
from streamlit_javascript import st_javascript

cookie_manager = CookieController()

st.set_page_config(page_title="Logging in...", layout="centered")

st.title("🔄 Redirecting...")

# Use JS to get full URL with fragment
url = st_javascript("await fetch('').then(r => window.parent.location.href)")

if url and "#access_token=" in url:
    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).fragment)
    access_token = parsed.get("access_token", [None])[0]

    if access_token:
        try:
            user = supabase_client.auth.get_user(access_token)
            user_id = user.user.id

            cookie_manager.set("access_token", access_token, max_age=3600)
            st.session_state["access_token"] = access_token
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = user_id

            st.success("✅ Logged in successfully!")

            st.switch_page("pages/1_Dashboard.py")

        except Exception as e:
            st.error("❌ Login failed. Invalid token.")
            st.exception(e)
    else:
        st.error("❌ Login failed: No access token found.")
else:
    st.warning("Waiting for redirect...")
    st.write("Raw URL:", url)