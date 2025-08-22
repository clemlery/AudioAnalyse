# main.py

from streaming_history_analyser.ingest import load_streaming_history_folder

from streaming_history_analyser.reporting import tracks_data_to_csv, artists_data_to_csv, releases_data_to_csv
from streaming_history_analyser.visualize import average_duration, playcount_artist_popularity_ratio, scatter_calculate_scores, scatter_playcount_duration

from config import session 

def main():
    
    scatter_calculate_scores()
    scatter_playcount_duration()
    # load_streaming_history_folder()


if __name__ == "__main__":
    main()
