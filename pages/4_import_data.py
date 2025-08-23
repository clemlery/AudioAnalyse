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

print(f"redirect_uri : {REDIRECT_URI}")

random_string = lambda N: "".join(
    random.choice(string.ascii_uppercase + string.digits) for _ in range(N)
)

params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPES,
}

# Page title
st.title("Upload your extended spotify history here !")

auth_page_path = f"{AUTH_URL}?" + urllib.parse.urlencode(params)

print(f"auth_page_path: {auth_page_path}")

st.html(f'<a href="{auth_page_path}">Connect to your spotify account</a>')

uploaded_files = st.file_uploader(
    "Choose a Streaming History file", accept_multiple_files=True
)

for uploaded_file in uploaded_files:
    if not re.search(
        r"^Streaming_History_Audio_(?:\d{4}(?:-\d{4})*)_\d{1,2}\.json$",
        uploaded_file.name,
    ):
        raise ValueError(
            f"The file name {uploaded_file.name} is not correct, you should not rename the files sent by Spotify."
        )
    path = UPLOADS_PATH + uploaded_file.name
    bytes_data = uploaded_file.read()
    with open(path, "wb") as f:
        f.write(bytes_data)
    st.write(f"{uploaded_file.name} Uploaded")
