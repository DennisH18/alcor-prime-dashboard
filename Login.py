import streamlit as st

st.set_page_config(layout="wide", page_icon="logo.png")

import base64
import cv2
import services.styles as styles

from streamlit_url_fragment import get_fragment
from streamlit_cookies_controller import CookieController
from services.supabaseService import supabase_client


cookie_manager = CookieController()

REDIRECT_URI = st.secrets["google"]["REDIRECT_URI"]


def main():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:

        with st.container(border=True):

            st.markdown(
                f"""
                <div style="text-align: center; margin-top: 40px; margin-bottom: 40px">
                    <p style="font-size: 25px; font-weight: 600; margin-bottom:10px">Alcor Prime Dashboard</p>
                    <p style="margin-bottom:40px"> Sign in with your company's Google Account </p>  
                </div>
                """,
                unsafe_allow_html=True,
            )

            response = supabase_client.auth.sign_in_with_oauth(
                {"provider": "google", "options": {"redirect_to": REDIRECT_URI}}
            )

            st.components.v1.html(
                f"""
                <div style="display: flex; justify-content: center; align-items: center; width: 100%; text-align: center;">
                    <a href="{response.url}" target="_blank" style="text-decoration: none;">
                        <button style="
                            font-size: 16px; 
                            padding: 15px; 
                            border-radius: 30px; 
                            display: flex; 
                            border: 2px solid gray;
                            align-items: center; 
                            justify-content: center;
                            cursor: pointer;
                            background-color: white;
                        ">
                            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                                width="20" style="margin-right: 10px;" />
                            Sign in with Google
                        </button>
                    </a>
                </div>
            """
            )

        fragment = get_fragment()

        if fragment:
            if "error=" in fragment:
                params = dict(x.split("=") for x in fragment.split("&") if "=" in x)
                error_desc = params.get("error_description", "Unknown error occurred.")
                st.error(f"Login failed: {error_desc.replace('+', ' ')}")

            elif "#access_token" in fragment:
                try:
                    params = dict(x.split("=") for x in fragment.split("&") if "=" in x)
                    access_token = params.get("#access_token")

                    if access_token:
                        try:
                            user = supabase_client.auth.get_user(access_token)
                            user_id = user.user.id

                            cookie_manager.set(
                                "access_token", access_token, max_age=3600
                            )
                            st.session_state["access_token"] = access_token
                            st.session_state["authenticated"] = True
                            st.session_state["user_id"] = user_id

                            print("Sucess Log in")

                            st.switch_page("pages/1_Dashboard.py")

                        except Exception:
                            st.error("Login failed. Invalid token. Please try again.")
                    else:
                        st.error("Login failed. No access token found.")
                except Exception:
                    st.error("Unexpected error during login.")


if __name__ == "__main__":
    main()
