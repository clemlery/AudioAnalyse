import os
import re
import threading
import urllib.parse
from typing import List

import requests
from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from constants.api import AUTH_URL, CLIENT_ID, CLIENT_SECRET, SCOPES, TOKEN_URL
from constants.service import UPLOADS_PATH
from routers.job import job, lock, scrape_job, scrape_lock

router = APIRouter()
templates = Jinja2Templates(directory="templates")

REDIRECT_URI = os.getenv("REDIRECT_URI")
LOG_PATH = "./log/exploit_streaming_history.log"

_FILENAME_RE = re.compile(
    r"^Streaming_History_Audio_(?:\d{4}(?:-\d{4})*)_\d{1,2}\.json$"
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _read_log_tail(n: int = 18) -> str:
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "".join(lines[-n:]).strip()
    except Exception:
        return ""


def _list_uploads() -> list[str]:
    try:
        files = [f for f in os.listdir(UPLOADS_PATH) if _FILENAME_RE.match(f)]
        pattern = re.compile(r"(\d+)(?=\.json$)")
        return sorted(files, key=lambda fn: int(pattern.search(fn).group(1)))
    except Exception:
        return []


def _status_fragment(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "fragments/job_status.html",
        {
            "request": request,
            "job": job,
            "log_tail": _read_log_tail() if job.status in ("running", "done", "error") else "",
        },
    )


# ── Background ingestion ──────────────────────────────────────────────────────

def _run_ingestion(user_id: str, filenames: list[str]) -> None:
    from streaming_history_analyser.ingest import (
        delete_log_backup,
        load_streaming_history_file,
    )
    from streaming_history_analyser.process import IngestContext, exploit_streaming_history
    from streaming_history_analyser.factory import BrowserTokenSource, ScraperFactory

    try:
        delete_log_backup()
        ctx = IngestContext(user_id=user_id)
        scraper_factory = ScraperFactory(BrowserTokenSource())

        for filename in filenames:
            with lock:
                job.current_file = filename
                job.message = f"Processing {filename}…"

            streaming_history = load_streaming_history_file(filename)
            file_timings = exploit_streaming_history(
                streaming_history, ctx, scraper_factory, scrape=False
            )

            with lock:
                job.files_done += 1
                job.message = f"Done: {filename}"
                job.timings[filename] = file_timings

        with lock:
            job.status = "done"
            job.message = f"All {job.files_total} files processed."

    except Exception as exc:
        with lock:
            job.status = "error"
            job.error = str(exc)


# ── Routes ────────────────────────────────────────────────────────────────────

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
            "uploads": _list_uploads(),
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

    # Refresh uploads list after saving
    uploads = _list_uploads()
    uploads_html = _render_uploads_list(uploads)
    return HTMLResponse("\n".join(messages) + uploads_html)


def _render_uploads_list(uploads: list[str]) -> str:
    if not uploads:
        return ""
    items = "".join(f"<li>{f}</li>" for f in uploads)
    return f'<script>document.getElementById("uploads-list").innerHTML = "<ul>{items}</ul>";</script>'


@router.post("/import/process", response_class=HTMLResponse)
def start_process(request: Request, filenames: List[str] = Form(default=[])):
    user_id = request.session.get("user_id")
    if not user_id:
        return HTMLResponse('<p class="warning">Not connected.</p>')

    with lock:
        if job.status == "running":
            return _status_fragment(request)

        if not filenames:
            return HTMLResponse('<p class="msg-error">No files selected.</p>')

        job.status = "running"
        job.files_total = len(filenames)
        job.files_done = 0
        job.current_file = ""
        job.message = "Starting…"
        job.error = ""
        job.timings = {}

    thread = threading.Thread(
        target=_run_ingestion, args=(user_id, filenames), daemon=True
    )
    thread.start()

    return _status_fragment(request)


@router.get("/import/status", response_class=HTMLResponse)
def get_status(request: Request):
    return _status_fragment(request)


# ── Scraping job ──────────────────────────────────────────────────────────────

def _scrape_status_fragment(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "fragments/scrape_status.html",
        {"request": request, "job": scrape_job},
    )


def _run_scraping() -> None:
    from streaming_history_analyser.scrape import run_metrics_scraping
    from streaming_history_analyser.factory import BrowserTokenSource, ScraperFactory

    try:
        scraper_factory = ScraperFactory(BrowserTokenSource())

        def _progress(message: str, done: int, total: int) -> None:
            with scrape_lock:
                scrape_job.message = message
                scrape_job.files_done = done
                scrape_job.files_total = total

        timings = run_metrics_scraping(
            scraper_factory=scraper_factory,
            progress_callback=_progress,
        )

        with scrape_lock:
            scrape_job.status = "done"
            scrape_job.message = "Metrics update complete."
            scrape_job.timings = timings

    except Exception as exc:
        with scrape_lock:
            scrape_job.status = "error"
            scrape_job.error = str(exc)


@router.post("/import/scrape", response_class=HTMLResponse)
def start_scrape(request: Request):
    if not request.session.get("user_id"):
        return HTMLResponse('<p class="warning">Not connected.</p>')

    with scrape_lock:
        if scrape_job.status == "running":
            return _scrape_status_fragment(request)

        scrape_job.status = "running"
        scrape_job.files_done = 0
        scrape_job.files_total = 0
        scrape_job.message = "Starting…"
        scrape_job.error = ""
        scrape_job.timings = {}

    thread = threading.Thread(target=_run_scraping, daemon=True)
    thread.start()

    return _scrape_status_fragment(request)


@router.get("/import/scrape/status", response_class=HTMLResponse)
def get_scrape_status(request: Request):
    return _scrape_status_fragment(request)
