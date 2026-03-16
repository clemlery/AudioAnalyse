# main.py

from streaming_history_analyser.ingest import load_streaming_history_folder
from streaming_history_analyser.reporting import (
    track_stream_day_to_csv,
    tracks_data_to_csv,
    artists_data_to_csv,
    releases_data_to_csv,
)
from streaming_history_analyser.visualize import (
    average_duration,
    playcount_artist_popularity_ratio,
    scatter_calculate_scores,
    scatter_playcount_duration,
    stream_day_plot_per_minutes_streamed,
)
from dao.db_dao.user_dao import UserDAO
from config import session


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
    stream_day_plot_per_minutes_streamed()


if __name__ == "__main__":
    main()
