# constants/api.py
from datetime import datetime
from typing import Final
import os

# Spotify API base
SPOTIFY_API_BASE_URL: Final[str] = "https://api.spotify.com/v1"

# Endpoints tracks
SPOTIFY_TRACKS_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/tracks"
SPOTIFY_SAVED_TRACKS_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/me/tracks"
SPOTIFY_TRACK_IS_SAVED_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/me/tracks/contains"

# Endpoints player
SPOTIFY_RECENT_PLAY_HISTORY_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/me/player/recently-played"
SPOTIFY_TOP_TRACKS_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/me/top/tracks"

# Pour playlist tracks : on utilisera le .format() ou f-string au moment de l'appel
SPOTIFY_PLAYLIST_TRACKS_URL_TEMPLATE: Final[str] = f"{SPOTIFY_API_BASE_URL}/playlists/{{playlist_id}}/tracks"

# Constantes pour le fichier artist_fetch_dao :
SPOTIFY_ARTISTS_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/artists"
SPOTIFY_TOP_ARTISTS_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/me/top/artists"
SPOTIFY_FOLLOWED_ARTISTS_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/me/following"
SPOTIFY_CHECK_FOLLOWED_ARTISTS_URL_TEMPLATE: Final[str] = f"{SPOTIFY_API_BASE_URL}/me/following/contains?type=artist"

# Constantes pour le fichier album_fetch_dao :
SPOTIFY_ALBUMS_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/albums"
SPOTIFY_ALBUM_TRACKS_URL_TEMPLATE: Final[str] = f"{SPOTIFY_API_BASE_URL}/albums/{{album_id}}/tracks"
SPOTIFY_SAVED_ALBUMS_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/me/albums"
SPOTIFY_CHECK_SAVED_ALBUMS_URL: Final[str] = f"{SPOTIFY_API_BASE_URL}/me/albums/contains"

# Endpoints User
SPOTIFY_USER_PROFILE_URL : Final[str] = f"{SPOTIFY_API_BASE_URL}/me"

# Spotify API constants
SCOPES : Final[str] = 'user-read-private user-read-email user-top-read user-read-recently-played user-library-read user-follow-read'
AUTH_URL : Final[str] = "https://accounts.spotify.com/authorize"
TOKEN_URL : Final[str] = "https://accounts.spotify.com/api/token"
CLIENT_ID : Final[str] = os.getenv('CLIENT_ID')
CLIENT_SECRET : Final[str] = os.getenv('CLIENT_SECRET')
REDIRECT_URI : Final[str] = os.getenv('REDIRECT_URI')


    





