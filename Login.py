import streamlit as st
import urllib.parse
import requests
import os

# Supabase details
SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]
REDIRECT_URI = st.secrets["google"]["REDIRECT_URI"]  # should match what’s set in Supabase dashboard

# Step 1: Generate the OAuth login URL manually
def get_oauth_login_url():
    provider = "google"
    return (
        f"{SUPABASE_URL}/auth/v1/authorize"
        f"?provider={provider}"
        f"&redirect_to={urllib.parse.quote(REDIRECT_URI)}"
        f"&response_type=code"
    )

# Step 2: Parse URL params to get authorization code
def get_auth_code():
    query_params = st.experimental_get_query_params()
    return query_params.get("code", [None])[0]

# Step 3: Exchange code for access token
def exchange_code_for_token(code):
    token_url = f"{SUPABASE_URL}/auth/v1/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "apikey": SUPABASE_KEY,
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to exchange code for token: {response.text}")
        return None

# UI Logic
def main():
    st.title("Alcor Prime Login")

    code = get_auth_code()

    if code:
        st.info("Authorization code received. Exchanging for token...")

        tokens = exchange_code_for_token(code)

        if tokens:
            access_token = tokens["access_token"]
            refresh_token = tokens.get("refresh_token")
            user = tokens["user"]

            st.success("Login successful!")
            st.write("Access Token:", access_token)
            st.write("User Info:", user)

            # Store in session state
            st.session_state["access_token"] = access_token
            st.session_state["user"] = user

            # Redirect to app/dashboard
            st.success("Redirecting to dashboard...")
            st.switch_page("pages/1_Dashboard.py")
        return

    # No code yet → show login button
    oauth_url = get_oauth_login_url()

    st.markdown(f"""
        <div style="text-align:center;">
            <a href="{oauth_url}">
                <button style="
                    padding: 10px 20px;
                    font-size: 16px;
                    background-color: white;
                    border: 2px solid #ccc;
                    border-radius: 25px;
                    cursor: pointer;
                ">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
                         width="20" style="margin-right: 10px; vertical-align: middle;" />
                    Sign in with Google
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()