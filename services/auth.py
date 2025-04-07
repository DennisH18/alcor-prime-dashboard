# services/auth.py
from streamlit_url_fragment import get_fragment
from streamlit_javascript import st_javascript
import streamlit as st
from http.cookies import SimpleCookie


def extract_access_token_from_fragment():
    fragment = get_fragment()
    if not fragment:
        return None
    params = dict(x.split("=") for x in fragment.split("&") if "=" in x)
    return params.get("#access_token")


def set_access_token_cookie(access_token: str, redirect_to: str = "/test"):
    js_code = f"""
        document.cookie = "access_token={access_token}; path=/";
        window.location.href = "{redirect_to}";
    """
    st_javascript(js_code)


def get_access_token_from_cookie():
    cookie_str = st_javascript("document.cookie") or ""
    cookies = SimpleCookie()
    cookies.load(cookie_str)
    return cookies.get("access_token").value if "access_token" in cookies else None


def get_logged_in_user(supabase):
    print("get_logged_in_user")
    token = get_access_token_from_cookie()
    st.write(token)
    if token:
        return supabase.auth.get_user(token)
    return None