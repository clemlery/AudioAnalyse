# models/ids/spotify_id.py
from pydantic import constr

# Type alias pour un ID Spotify (au moins 22 caractères alphanumériques)
SpotifyID = constr(min_length=22, pattern=r"^[A-Za-z0-9]+$")
