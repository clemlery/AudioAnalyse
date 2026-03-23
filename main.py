# main.py

from pipeline.ingest import load_streaming_history_folder
from pipeline.reporting import (
    get_stream_day_data,
    get_tracks_data,
    get_artists_data,
    get_releases_data,
    artists_data_to_csv,
    tracks_data_to_csv,
    releases_data_to_csv,
    track_stream_day_to_csv,
)
from pipeline.visualize import (
    average_duration,
    playcount_artist_popularity_ratio,
    stream_day_plot_per_minutes_streamed,
)
from dao.db.user_dao import UserDAO
from core.config import session


def _get_cli_user_id() -> str:
    """Return the first user in DB for CLI use. Raise if none exists."""
    users = UserDAO.get_all()
    if not users:
        raise RuntimeError(
            "No user found in database. "
            "Run the Streamlit app and authenticate with Spotify first."
        )
    return users[0].id


def main():
    user_id = _get_cli_user_id()
    # load_streaming_history_folder(user_id)
    df = get_stream_day_data(session, user_id)
    fig = stream_day_plot_per_minutes_streamed(df)
    fig.show()


if __name__ == "__main__":
    main()
