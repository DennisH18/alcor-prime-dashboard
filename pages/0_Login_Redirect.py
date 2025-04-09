import streamlit as st
from streamlit_cookies_controller import CookieController
from services.supabaseService import supabase_client

cookie_manager = CookieController()

st.set_page_config(page_title="Logging in...", layout="centered")

st.title("🔄 Logging you in...")

# Get the ?code=... from the URL query params
code = st.query_params.get("code")

if code:
    try:
        # Exchange the code for a session (access_token, etc.)
        session = supabase_client.auth.exchange_code_for_session(code)
        access_token = session.session.access_token
        user = session.user

        if access_token and user:
            cookie_manager.set("access_token", access_token, max_age=3600)
            st.session_state["access_token"] = access_token
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = user.id

            st.success("✅ Logged in successfully!")
            st.switch_page("pages/1_Dashboard.py")
        else:
            st.error("❌ Login failed: Invalid session.")

    except Exception as e:
        st.error("❌ Failed to exchange code for session.")
        st.exception(e)
else:
    st.warning("No code in redirect URL.")