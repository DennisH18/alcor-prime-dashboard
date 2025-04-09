import streamlit as st
import requests

# Set your secrets in .streamlit/secrets.toml
SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]
REDIRECT_URI = st.secrets["google"]["REDIRECT_URI"]

st.set_page_config(layout="wide", page_title="Alcor Prime Login", page_icon="🔐")

def get_auth_code():
    # Use new Streamlit API
    return st.query_params.get("code")

def exchange_code_for_token(code):
    token_url = f"{SUPABASE_URL}/auth/v1/token"
    headers = {
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY,
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(token_url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"❌ Failed to exchange code for token: {response.text}")
        return None

def main():
    st.markdown("""
        <div style="text-align: center; margin-top: 40px; margin-bottom: 20px">
            <h2>🔐 Alcor Prime Dashboard Login</h2>
            <p>Sign in with your company's Google account</p>
        </div>
    """, unsafe_allow_html=True)

    code = get_auth_code()

    if code:
        st.info("Authorization code received. Exchanging for token...")
        token_data = exchange_code_for_token(code)

        if token_data:
            st.success("✅ Login successful!")
            st.session_state["access_token"] = token_data["access_token"]
            st.session_state["refresh_token"] = token_data.get("refresh_token")
            st.session_state["user"] = token_data.get("user")

            st.write("### User Info:")
            st.json(token_data.get("user"))

            st.success("Redirecting to dashboard...")
            st.switch_page("pages/1_Dashboard.py")
    else:
        # No auth code yet: show login button
        login_url = f"{SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to={REDIRECT_URI}"

        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; margin-top: 40px;">
                <a href="{login_url}" style="text-decoration: none;">
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
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()