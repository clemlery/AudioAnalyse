from typing import Annotated, Optional

import matplotlib.pyplot as plt
import numpy as np
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import session as db_session
from routers.utils import df_to_csv_uri, fig_to_b64
from streaming_history_analyser.reporting import get_artists_data, get_tracks_data

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/scores", response_class=HTMLResponse)
def scores_page(request: Request):
    return templates.TemplateResponse(
        "scores.html",
        {"request": request, "user_id": request.session.get("user_id")},
    )


@router.post("/scores/artists", response_class=HTMLResponse)
def scores_artists(
    request: Request,
    w_click: Annotated[float, Form()] = 1.0,
    w_done: Annotated[float, Form()] = 0.5,
    w_skip: Annotated[float, Form()] = 0.2,
    min_done: Annotated[int, Form()] = 50,
    require_clicks: Annotated[Optional[str], Form()] = None,
    top_n: Annotated[int, Form()] = 50,
    annotate: Annotated[Optional[str], Form()] = None,
):
    user_id = request.session.get("user_id")
    if not user_id:
        return HTMLResponse(
            '<p class="warning">Not connected. <a href="/import">Connect here</a>.</p>'
        )

    chart_b64 = ""
    table_interest_html = ""
    table_commitment_html = ""
    csv_uri_interest = ""
    csv_uri_commitment = ""
    error = None

    try:
        a_df = get_artists_data(db_session, user_id)

        filt = a_df["Track_Done_Count"] > min_done
        if require_clicks:
            filt &= a_df["Click_Row_Count"] > 0
        df = a_df.loc[filt].copy()

        df["Interest_Score"] = (
            w_done * df["Track_Done_Count"]
            + w_click * df["Click_Row_Count"]
            - w_skip * df["Skipped_Count"]
        )
        denom = df["Track_Done_Count"] + df["Click_Row_Count"] + df["Skipped_Count"]
        df["Commitment_Ratio"] = (df["Track_Done_Count"] + df["Click_Row_Count"]) / denom.replace(0, np.nan)
        df = df.dropna(subset=["Commitment_Ratio"])

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(df["Interest_Score"], df["Commitment_Ratio"], alpha=0.7)
        ax.set_xlabel("Interest Score")
        ax.set_ylabel("Commitment Ratio")
        ax.set_title("Interest Score vs Commitment Ratio — Artists")

        if annotate and not df.empty:
            top_i = df.sort_values("Interest_Score", ascending=False).iloc[0]
            top_c = df.sort_values("Commitment_Ratio", ascending=False).iloc[0]
            ax.annotate(top_i["Name"], (top_i["Interest_Score"], top_i["Commitment_Ratio"]))
            if top_c["Name"] != top_i["Name"]:
                ax.annotate(top_c["Name"], (top_c["Interest_Score"], top_c["Commitment_Ratio"]))

        fig.tight_layout()
        chart_b64 = fig_to_b64(fig)

        top_interest = (
            df[["Name", "Interest_Score", "Commitment_Ratio"]]
            .sort_values("Interest_Score", ascending=False)
            .head(top_n)
        )
        top_commitment = (
            df[["Name", "Interest_Score", "Commitment_Ratio"]]
            .sort_values("Commitment_Ratio", ascending=False)
            .head(top_n)
        )
        table_interest_html = top_interest.to_html(classes="data-table", index=False, border=0)
        table_commitment_html = top_commitment.to_html(classes="data-table", index=False, border=0)
        csv_uri_interest = df_to_csv_uri(top_interest)
        csv_uri_commitment = df_to_csv_uri(top_commitment)
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse(
        "fragments/scores_artists.html",
        {
            "request": request,
            "chart_b64": chart_b64,
            "table_interest_html": table_interest_html,
            "table_commitment_html": table_commitment_html,
            "csv_uri_interest": csv_uri_interest,
            "csv_uri_commitment": csv_uri_commitment,
            "error": error,
        },
    )


@router.post("/scores/tracks", response_class=HTMLResponse)
def scores_tracks(
    request: Request,
    use_log_x: Annotated[Optional[str], Form()] = None,
    to_minutes: Annotated[Optional[str], Form()] = None,
):
    user_id = request.session.get("user_id")
    if not user_id:
        return HTMLResponse(
            '<p class="warning">Not connected. <a href="/import">Connect here</a>.</p>'
        )

    chart_b64 = ""
    error = None

    try:
        plot_df = get_tracks_data(db_session, user_id).copy()

        if to_minutes:
            plot_df["Duration_Min"] = plot_df["Duration_Ms"] / 60000.0
            y_col, y_label = "Duration_Min", "Track Duration (minutes)"
        else:
            y_col, y_label = "Duration_Ms", "Track Duration (ms)"

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(plot_df["Track_Done_Count"], plot_df[y_col], alpha=0.5)
        ax.set_xlabel("Track Playcount")
        ax.set_ylabel(y_label)
        ax.set_title("Playcount vs Duration")
        if use_log_x:
            try:
                ax.set_xscale("log")
            except Exception:
                pass
        fig.tight_layout()
        chart_b64 = fig_to_b64(fig)
    except Exception as e:
        error = str(e)

    return templates.TemplateResponse(
        "fragments/scores_tracks.html",
        {"request": request, "chart_b64": chart_b64, "error": error},
    )
