import streamlit as st
import base64
import cv2
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(layout="wide", page_icon="logo.png")

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

def main():
    PASSWORD = st.secrets["password"]["PASSWORD"]

    # Check for cookie using JS
    auth_cookie = streamlit_js_eval(
        js_expressions="document.cookie.includes('authenticated=true')", 
        key="check_auth_cookie"
    )

    # If cookie exists, mark session as authenticated
    if auth_cookie and not st.session_state.get("authenticated", False):
        st.session_state["authenticated"] = True
        st.rerun()

    if st.session_state.get("authenticated"):
        st.switch_page("pages/1_Dashboard.py")

    # Hide sidebar for login
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)

    # Centered login form
    col1, col2, col3 = st.columns([1, 2, 1]) 
    with col2:
        with st.form("login_form"):
            st.write("#")
            render_img_html(image_to_base64("logo.png"))
            st.markdown("<h3 style='text-align: center;'>Login</h3>", unsafe_allow_html=True)
            st.write("")

            password_input = st.text_input("Enter Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                if password_input == PASSWORD:
                    st.session_state["authenticated"] = True
                    streamlit_js_eval(
                        js_expressions="document.cookie = 'authenticated=true; path=/';",
                        key="set_auth_cookie"
                    )
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Incorrect password. Try again.")

if __name__ == "__main__":
    main()