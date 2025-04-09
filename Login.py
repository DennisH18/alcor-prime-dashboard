import streamlit as st
import urllib.parse
from streamlit_javascript import st_javascript
from streamlit_cookies_controller import CookieController
from services.supabaseService import supabase_client
import services.styles as styles  # If you use any custom styling
import time

st.set_page_config(layout="wide", page_icon="logo.png")
cookie_manager = CookieController()

REDIRECT_URI = st.secrets["google"]["REDIRECT_URI"]

def main():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):

            st.markdown(
                """
                <div style="text-align: center; margin-top: 40px; margin-bottom: 40px">
                    <p style="font-size: 25px; font-weight: 600; margin-bottom:10px">Alcor Prime Dashboard</p>
                    <p style="margin-bottom:40px"> Sign in with your company's Google Account </p>  
                </div>
                """,
                unsafe_allow_html=True,
            )

            response = supabase_client.auth.sign_in_with_oauth(
                {"provider": "google", "options": {"redirect_to": REDIRECT_URI},"flow_type": "implicit"
}
            )

            login_url = response.url

            st.markdown(f"""
                <div style="display: flex; justify-content: center; margin-top: 20px;">
                    <a href="{login_url}" id="login-btn" style="text-decoration: none;">
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
            """, unsafe_allow_html=True)

    url = st_javascript("await fetch('').then(() => window.parent.location.href)")
    url

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

                st.success("✅ Logged in successfully. Redirecting...")
                time.sleep(1)
                st.switch_page("pages/1_Dashboard.py")

            except Exception as e:
                st.error("Login failed. Invalid token.")
                st.exception(e)

        else:
            st.error("Access token not found.")


if __name__ == "__main__":
    main()