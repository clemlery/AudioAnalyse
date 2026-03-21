from typing import Final
from dotenv import load_dotenv
import streamlit as st
import os
import re
from constants.service import UPLOADS_PATH
from constants.api import AUTH_URL, SCOPES
import random
import string
import urllib.parse
from pathlib import Path

BASE_DIR: Final[str] = Path(".")
DOT_ENV: Final[str] = "./env"

load_dotenv(DOT_ENV, override=True)

CLIENT_ID: Final[str] = os.getenv("CLIENT_ID")
REDIRECT_URI: Final[str] = os.getenv("REDIRECT_URI")

random_string = lambda N: "".join(
    random.choice(string.ascii_uppercase + string.digits) for _ in range(N)
)

st.title("Import your extended Spotify history")

# ------------------------------------------------------------------
# Session state — display current user if already authenticated
# ------------------------------------------------------------------
user_id: str | None = st.session_state.get("user_id")
if user_id:
    st.success(f"Connected as **{st.session_state.get('display_name', user_id)}**")
    if st.button("Disconnect"):
        del st.session_state["user_id"]
        st.session_state.pop("display_name", None)
        st.rerun()
    st.divider()

# ------------------------------------------------------------------
# OAuth link
# ------------------------------------------------------------------
params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPES,
}

auth_page_path = f"{AUTH_URL}?" + urllib.parse.urlencode(params)

st.subheader("1) Connect your Spotify account")
st.html(f'<a href="{auth_page_path}">Connect to Spotify</a>')

# ------------------------------------------------------------------
# OAuth callback handling
# After Spotify redirects back, the URL contains ?code=...
# Exchange the code for tokens, fetch user profile, store in session.
# ------------------------------------------------------------------
query_params = st.query_params
if "code" in query_params and not user_id:
    import requests
    from dao.db_dao.user_dao import UserDAO
    from dao.fetch_dao.user_fetch_dao import UserFetchDao

    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    TOKEN_URL = "https://accounts.spotify.com/api/token"

    code = query_params["code"]
    token_resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if token_resp.ok:
        token_data = token_resp.json()
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")

        user_profile = UserFetchDao.fetch_user(access_token)
        UserDAO.add_user(user_profile, access_token, refresh_token, expires_in)

        st.session_state["user_id"] = user_profile.id
        st.session_state["display_name"] = user_profile.display_name

        # Clear the code from the URL to avoid re-processing on refresh
        st.query_params.clear()
        st.rerun()
    else:
        st.error(f"Token exchange failed: {token_resp.text}")

# ------------------------------------------------------------------
# File upload — only available once authenticated
# ------------------------------------------------------------------
st.subheader("2) Upload your streaming history files")

if not st.session_state.get("user_id"):
    st.info("Connect your Spotify account above before uploading files.")
else:
    uploaded_files = st.file_uploader(
        "Choose Streaming_History_Audio_*.json files",
        accept_multiple_files=True,
        type="json",
    )

    for uploaded_file in uploaded_files:
        if not re.search(
            r"^Streaming_History_Audio_(?:\d{4}(?:-\d{4})*)_\d{1,2}\.json$",
            uploaded_file.name,
        ):
            st.error(
                f"Invalid filename: **{uploaded_file.name}**. "
                "Do not rename the files sent by Spotify."
            )
            continue

        path = UPLOADS_PATH + uploaded_file.name
        bytes_data = uploaded_file.read()
        with open(path, "wb") as f:
            f.write(bytes_data)
        st.write(f"{uploaded_file.name} saved.")
