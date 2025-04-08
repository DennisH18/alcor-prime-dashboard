import streamlit as st
import base64
import cv2
import services.styles as styles

from streamlit_url_fragment import get_fragment
from streamlit_cookies_controller import CookieController
from services.supabaseService import supabase_client

st.set_page_config(layout="wide", page_icon="logo.png")
st.logo("logo.png")

cookie_manager = CookieController()

hide_sidebar = """
    <style>
        [data-testid="stSidebar"] { display: none; }
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

REDIRECT_URI = st.secrets["google"]["REDIRECT_URI"]

def image_to_base64(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    _, encoded_image = cv2.imencode(".png", image)
    base64_image = base64.b64encode(encoded_image.tobytes()).decode("utf-8")
    return base64_image


def main():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
            
        with st.container(border=True):

            logo_base64 = image_to_base64("logo.png")

            st.markdown(
                f"""
                <div style="text-align: center; margin-top: 40px; margin-bottom: 40px">
                    <img src="data:image/png;base64,{logo_base64}" style="max-width: 150px; max-height: 150px; margin-bottom:30px"/>
                    <p style="font-size: 25px; font-weight: 600; margin-bottom:10px">Alcor Prime Dashboard</p>
                    <p style="margin-bottom:40px"> Sign in with your company's Google Account </p>  
                </div>
                """, 
                unsafe_allow_html=True
            )
            subcol1, subcol2, subcol3, subcol4 = st.columns([4,1,2,4])
            with subcol2:
                st.markdown(
                    """
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                        width="25" style="margin-top: 8px;" />
                    """,
                    unsafe_allow_html=True
                )            
            with subcol3:
                if st.button("Sign in", use_container_width=True):
                    response = supabase_client.auth.sign_in_with_oauth({
                        "provider": "google",
                        "options": {
                            "redirect_to": REDIRECT_URI
                        }
                    })
                    st.markdown(f"""
                    <meta http-equiv="refresh" content="0;url={response.url}" />
                    <script>window.location.replace("{response.url}");</script>
                    """, unsafe_allow_html=True)

            st.write("")
            st.write("")


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

                            cookie_manager.set("access_token", access_token, max_age=3600)
                            st.session_state["access_token"] = access_token
                            st.session_state["authenticated"] = True
                            st.session_state["user_id"] = user_id

                            st.switch_page("pages/1_Dashboard.py")

                        except Exception:
                            st.error("Login failed. Invalid token. Please try again.")
                    else:
                        st.error("Login failed. No access token found.")
                except Exception:
                    st.error("Unexpected error during login.")


if __name__ == "__main__":
    main()
