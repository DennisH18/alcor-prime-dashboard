import streamlit as st
from supabase import create_client
from streamlit_url_fragment import get_fragment
from streamlit_cookies_controller import CookieController
import base64
import cv2
from services.supabaseService import supabase_client

st.set_page_config(page_title="Login", layout="centered", initial_sidebar_state="collapsed")

cookie_manager = CookieController()
hide_sidebar = """
    <style>
        [data-testid="stSidebar"] { display: none; }
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

def image_to_base64(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    _, encoded_image = cv2.imencode(".png", image)
    base64_image = base64.b64encode(encoded_image.tobytes()).decode("utf-8")
    return base64_image

def main():

    with st.container(border=True):

        logo_base64 = image_to_base64("logo.png")

        col1, col2, col3 = st.columns([1, 3, 1])

        with col2:

            st.markdown(
                f"""
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="data:image/png;base64,{logo_base64}" style="max-width: 150px; max-height: 150px; margin-bottom:20px"/>
                    <p>Sign in with your company's Google Account</p>  
                </div>
                """, 
                unsafe_allow_html=True
            )

            subcol1, subcol2 = st.columns([1, 3])
            with subcol1:
                st.image('https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg', width=20)
            with subcol2:
                if st.button("Sign in", use_container_width=True):
                    response = supabase_client.auth.sign_in_with_oauth({
                        "provider": "google",
                        "options": {
                            "redirect_to": "http://localhost:8501/"
                        }
                    })
                    st.markdown(f"""
                    <meta http-equiv="refresh" content="0;url={response.url}" />
                    <script>window.location.replace("{response.url}");</script>
                    """, unsafe_allow_html=True)

        fragment = get_fragment()
        params = dict(x.split("=") for x in fragment.split("&") if "=" in x)
        access_token = params.get("#access_token")

        if access_token is not None:
            cookie_manager.set("access_token", access_token)
            st.switch_page("pages/1_Dashboard.py")




if __name__ == "__main__":
    main()
