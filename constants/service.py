from typing import Final
import enum

# Contants used in all codes made for services puposes 
ALBUM_MIN_DURATION_MS : Final[int] = 30 * 60 * 1000
ALBUM_MIN_TRACK_NUMBER : Final[int] = 7
EP_MIN_TRACK_NUMBER : Final[int] = 4

# Enumeration used to define a type of release
class RELEASE_TYPE(enum.Enum):
    SINGLE = "single"
    EP = "ep"
    ALBUM = "album"
    COMPILATION = "compilation"
    
# Enumeration describing ordering type for function that calcul tops
class ORDER_TYPE(enum.Enum):
    MINUTES_STREAMED : Final[str] = 'minutes_streamed'
    TRACK_DONE_COUNT : Final[str] = 'track_done_count'
    
# This variable defines every how many new rows in the database we commit
BATCH_SIZE : Final[int] = 200

# The Spotify ID of the only User that is in the table User 
USER_ID : Final[str] = '31b3yikgfs3a6dypwxxij2ts5jz4'

# Folder streaming history data path 
UPLOADS_PATH : Final[str] = './data/uploads/'

# Folder streaming history data path (test files)
UPLOADS_TEST_PATH : Final[str] = './data/test/'

# Path of the csv files containing all the most interesting data in the database
CSV_TRACK_PATH : Final[str] = "./data/csv/tracks_data.csv"
CSV_ARTIST_PATH : Final[str] = "./data/csv/artists_data.csv"
CSV_RELEASE_PATH: Final[str] = "./data/csv/releases_data.csv"
CSV_STREAM_DAY_PATH : Final[str] = "./data/csv/stream_day_data.csv"



    