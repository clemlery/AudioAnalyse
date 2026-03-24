from typing import Final
import enum

# Contants used in all codes made for services puposes
ALBUM_MIN_DURATION_MS: Final[int] = 30 * 60 * 1000
ALBUM_MIN_TRACK_NUMBER: Final[int] = 7
EP_MIN_TRACK_NUMBER: Final[int] = 4


# Enumeration used to define a type of release
class RELEASE_TYPE(enum.Enum):
    SINGLE = "single"
    EP = "ep"
    ALBUM = "album"
    COMPILATION = "compilation"


# Enumeration describing ordering type for function that calcul tops
class ORDER_TYPE(enum.Enum):
    MINUTES_STREAMED: str = "minutes_streamed"
    TRACK_DONE_COUNT: str = "track_done_count"


# This variable defines every how many new rows in the database we commit
BATCH_SIZE: Final[int] = 200

# Folder streaming history data path
UPLOADS_PATH: Final[str] = "./data/uploads/"

# Folder streaming history data path (test files)
UPLOADS_TEST_PATH: Final[str] = "./data/test/"

# Base directory for per-user CSV exports
CSV_BASE_DIR: Final[str] = "./data/csv"


def user_csv_paths(user_id: str) -> dict[str, str]:
    """Return the CSV file paths for a given user."""
    base = f"{CSV_BASE_DIR}/{user_id}"
    return {
        "tracks": f"{base}/tracks_data.csv",
        "artists": f"{base}/artists_data.csv",
        "releases": f"{base}/releases_data.csv",
        "stream_day": f"{base}/stream_day_data.csv",
    }