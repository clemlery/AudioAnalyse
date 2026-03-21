from typing import Annotated, Optional

import matplotlib.pyplot as plt
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import session as db_session
from constants.service import ORDER_TYPE
from routers.utils import df_to_csv_uri, fig_to_b64
from streaming_history_analyser.reporting import (
    get_artists_data,
    get_releases_data,
    get_tracks_data,
)
from streaming_history_analyser.visualize import top_artists, top_releases, top_tracks

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _order(sort: str) -> tuple[ORDER_TYPE, str]:
    if sort == "minutes":
        return ORDER_TYPE.MINUTES_STREAMED, "Minutes_Streamed"
    return ORDER_TYPE.TRACK_DONE_COUNT, "Track_Done_Count"


def _bar_chart(df, name_col: str, metric_col: str, title: str) -> str:
    if df.empty:
        return ""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df[name_col], df[metric_col])
    ax.set_title(title)
    ax.set_xlabel("Name")
    ax.set_ylabel(metric_col.replace("_", " "))
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig_to_b64(fig)


@router.get("/top-items", response_class=HTMLResponse)
def top_items_page(request: Request):
    return templates.TemplateResponse(
        "top_items.html",
        {"request": request, "user_id": request.session.get("user_id")},
    )


@router.post("/top-items/data", response_class=HTMLResponse)
def top_items_data(
    request: Request,
    sort: Annotated[str, Form()] = "minutes",
    n: Annotated[int, Form()] = 10,
    tab: Annotated[str, Form()] = "tracks",
):
    user_id = request.session.get("user_id")
    if not user_id:
        return HTMLResponse(
            '<p class="warning">Not connected. <a href="/import">Connect here</a>.</p>'
        )

    order, metric_col = _order(sort)
    chart_b64 = ""
    table_html = ""
    csv_uri = ""
    filename = "data.csv"
    error = None

    try:
        if tab == "tracks":
            df = top_tracks(n, order, get_tracks_data(db_session, user_id))
            name_col = next(
                (c for c in ["Name", "Track_Name"] if c in df.columns), df.columns[0]
            )
            filename = "top_tracks.csv"
        elif tab == "artists":
            df = top_artists(n, order, get_artists_data(db_session, user_id))
            name_col = next(
                (c for c in ["Name", "Artist_Name"] if c in df.columns), df.columns[0]
            )
            filename = "top_artists.csv"
        else:
            df = top_releases(n, order, get_releases_data(db_session, user_id))
            name_col = next(
                (c for c in ["Name", "Release_Name"] if c in df.columns), df.columns[0]
            )
            filename = "top_releases.csv"

        chart_b64 = _bar_chart(df, name_col, metric_col, f"Top {n} {tab.capitalize()}")
        table_html = df.to_html(classes="data-table", index=False, border=0)
        csv_uri = df_to_csv_uri(df)
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse(
        "fragments/top_items_content.html",
        {
            "request": request,
            "chart_b64": chart_b64,
            "table_html": table_html,
            "csv_uri": csv_uri,
            "filename": filename,
            "error": error,
        },
    )
