# pages/0_Login_Redirect.py
import streamlit as st
from services.supabaseService import supabase_client
from streamlit_cookies_controller import CookieController

st.set_page_config(layout="centered", page_title="Redirecting...")

cookie_manager = CookieController()
code = st.query_params.get("code")

if not code:
    st.error("No authorization code found in redirect URL.")
    st.stop()

with st.spinner("Exchanging code for session..."):
    try:
        session = supabase_client.auth.exchange_code_for_session({
            "code": code,
            # optionally: "code_verifier": "your-verifier"
        })
        access_token = session.access_token
        user = supabase_client.auth.get_user(access_token)
        user_id = user.user.id

        cookie_manager.set("access_token", access_token, max_age=3600)
        st.session_state["access_token"] = access_token
        st.session_state["authenticated"] = True
        st.session_state["user_id"] = user_id

        st.success("✅ Login successful! Redirecting to dashboard...")
        st.experimental_rerun()  # Or redirect to dashboard:
        # st.switch_page("pages/1_Dashboard.py")

    except Exception as e:
        st.error("❌ Failed to log in.")
        st.exception(e)