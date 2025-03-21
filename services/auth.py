import streamlit as st
import base64
import cv2
from streamlit_js_eval import streamlit_js_eval

def image_to_base64(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    _, encoded_image = cv2.imencode(".png", image)
    base64_image = base64.b64encode(encoded_image.tobytes()).decode("utf-8")
    return base64_image

def render_img_html(image_b64):
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center; margin-bottom: 10px;">
            <img src="data:image/png;base64,{image_b64}" style="max-width: 150px; max-height: 150px;"/>
        </div>
        """, 
        unsafe_allow_html=True
    )


def login():
    password = st.secrets["password"]["PASSWORD"]

    auth_status = streamlit_js_eval(js_expressions="document.cookie.includes('authenticated=true')", key="auth_cookie")

    if auth_status:
        st.session_state.authenticated = True

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        hide_sidebar = """
            <style>
                [data-testid="stSidebar"] { display: none; }
            </style>
        """
        st.markdown(hide_sidebar, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1]) 
        with col2:
            with st.form("login_form"):
                st.write("#")
                render_img_html(image_to_base64("logo.png"))
                st.write("#")

                subcol1, subcol2, subcol3= st.columns([1, 4, 1])
                with subcol2:
                    st.markdown("<h3 style=''>Login</h3>", unsafe_allow_html=True)
                    st.write("")
                    password_input = st.text_input("Enter Password", type="password")
                    st.write("")
                    submit = st.form_submit_button("Login")
                    st.write("#")

                if submit:
                    if password_input == password:
                        st.session_state.authenticated = True
                        streamlit_js_eval(js_expressions="document.cookie='authenticated=true; path=/;'", key="set_auth_cookie")
                        st.success("Login successful! Redirecting...")
                        st.rerun()
                    else:
                        st.error("Incorrect password. Try again.")

                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.authenticated:
        st.stop()

