import os
import re
import urllib.parse
from typing import List

import requests
from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from constants.api import AUTH_URL, CLIENT_ID, CLIENT_SECRET, SCOPES, TOKEN_URL
from constants.service import UPLOADS_PATH

router = APIRouter()
templates = Jinja2Templates(directory="templates")

REDIRECT_URI = os.getenv("REDIRECT_URI")

_FILENAME_RE = re.compile(
    r"^Streaming_History_Audio_(?:\d{4}(?:-\d{4})*)_\d{1,2}\.json$"
)


@router.get("/import", response_class=HTMLResponse)
def import_page(request: Request):
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return templates.TemplateResponse(
        "import.html",
        {
            "request": request,
            "auth_url": auth_url,
            "user_id": request.session.get("user_id"),
            "display_name": request.session.get("display_name"),
        },
    )


@router.get("/callback")
def oauth_callback(request: Request, code: str):
    from dao.db_dao.user_dao import UserDAO
    from dao.fetch_dao.user_fetch_dao import UserFetchDao

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
        user_profile = UserFetchDao.fetch_users_profile(token_data["access_token"])
        UserDAO.add_user(
            user_profile,
            token_data["access_token"],
            token_data.get("refresh_token"),
            token_data.get("expires_in"),
        )
        request.session["user_id"] = user_profile.id
        request.session["display_name"] = user_profile.display_name

    return RedirectResponse(url="/import")


@router.post("/import/disconnect")
def disconnect(request: Request):
    request.session.clear()
    return RedirectResponse(url="/import", status_code=303)


@router.post("/import/upload", response_class=HTMLResponse)
async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    if not request.session.get("user_id"):
        return HTMLResponse('<p class="warning">Not connected.</p>')

    messages = []
    for f in files:
        if not _FILENAME_RE.match(f.filename):
            messages.append(
                f'<p class="msg-error">Invalid filename: <strong>{f.filename}</strong>. Do not rename Spotify files.</p>'
            )
            continue
        path = UPLOADS_PATH + f.filename
        content = await f.read()
        with open(path, "wb") as out:
            out.write(content)
        messages.append(f'<p class="msg-success">&#10003; {f.filename} saved.</p>')

    return HTMLResponse("\n".join(messages))
