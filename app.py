import os
import matplotlib
matplotlib.use("Agg")

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from routers import home, top_items, scores, import_data

app = FastAPI(title="Lyra — Spotify Analytics")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-change-me"),
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(home.router)
app.include_router(top_items.router)
app.include_router(scores.router)
app.include_router(import_data.router)
