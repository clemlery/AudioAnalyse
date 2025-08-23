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

from config import session


def main():
    stream_day_plot_per_minutes_streamed()
    # load_streaming_history_folder()


if __name__ == "__main__":
    main()
