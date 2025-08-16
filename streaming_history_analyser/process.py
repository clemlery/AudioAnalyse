# process.py

# We import all the Fetch DAOs
from auth import ConfigAuth
from constants.service import RELEASE_TYPE, UPLOADS_PATH
from dao.db_dao.track_stream_day_dao import TrackStreamDayDAO
from dao.fetch_dao.track_fetch_dao import TrackFetchDAO
from dao.fetch_dao.artist_fetch_dao import ArtistFetchDAO
from dao.fetch_dao.album_fetch_dao import AlbumFetchDAO
from dao.fetch_dao.user_fetch_dao import UserFetchDao

# We import all the DAOs
from dao.db_dao.track_stream_dao import TrackStreamDAO
from dao.db_dao.artist_dao import ArtistDAO
from dao.db_dao.release_dao import ReleaseDAO
from dao.db_dao.track_dao import TrackDAO
from dao.db_dao.spotify_track_dao import SpotifyTrackDAO
from dao.db_dao.user_dao import UserDAO

# We import the association table
from models.sql_alchemy_models.association import track_artist, release_artist

# We import the logger global variable 
from config import logger

# Other imports
from config import session
from sqlalchemy import select
from streaming_history_analyser.service import chunk_list, define_release_type, verify_token
from datetime import datetime

# defining some variable for TrackStream and TrackStreamDay table's metadatas
last_track_played : str = ''
last_date = datetime(1,1,1).date()
current_loop_streak : int = 1
current_loop_streak_day : int = 1

def filter_new_track_ids(records):
    """Return set of Spotify track IDs not in local DB."""
    ids = set()
    for item in records:
        uri = item.get('spotify_track_uri')
        try:
            _, data_type, tid = uri.split(':')
            if data_type == 'track' and not SpotifyTrackDAO.get_spotify_track_by_spotify_id(tid):
                ids.add(tid)
        except Exception:
            logger.error(f"Invalid URI or error: {uri}")
    return ids

def fetch_tracks_in_batches(token, ids, batch_size=50):
    """Fetch track objects in sub-batches."""
    tracks = []
    for chunk in chunk_list(list(ids), batch_size):
        tracks.extend(TrackFetchDAO.fetch_tracks(token, chunk))
    return tracks


def process_track_metadata(tracks, token, seen_artists, seen_releases, seen_spotify_tracks):
    """Handle insertion of tracks, releases, artists and associations."""
    # Identify new releases and artists
    new_releases = {t.album.id for t in tracks if t.album.id not in seen_releases and not ReleaseDAO.get_release_by_spotify_id(t.album.id)}
    new_artists = {a.id for t in tracks for a in t.artists if a.id not in seen_artists and not ArtistDAO.get_artist_by_spotify_id(a.id)}

    # Fetch missing artist data
    for chunk in chunk_list(list(new_artists), 50):
        artists = ArtistFetchDAO.fetch_artists(token, chunk)
        for art in artists:
            ArtistDAO.add_artist(art)
            seen_artists.add(art.id)

    # Fetch missing release data in batches of 20
    releases = []
    for chunk in chunk_list(list(new_releases), 20):
        releases.extend(AlbumFetchDAO.fetch_albums(token, chunk))

    for rel in releases:
        rel_type = (define_release_type(rel) if rel.album_type != 'compilation'
                    else RELEASE_TYPE.COMPILATION)
        ReleaseDAO.add_release(rel, rel_type.value)
        seen_releases.add(rel.id)

    # Now insert individual tracks and SpotifyTrack entries
    for t in tracks:
        seen_spotify_tracks.add(t.id)
        track_obj = TrackDAO.get_track_by_nd(t.name, t.duration_ms) or TrackDAO.add_track(t)
        if not SpotifyTrackDAO.get_spotify_track_by_spotify_id(t.id):
            SpotifyTrackDAO.add_spotify_track(t.id, track_obj.id, ReleaseDAO.get_release_by_spotify_id(t.album.id).id)
            seen_spotify_tracks.add(t.id)

    # Link track<->artist and release<->artist
    for t in tracks:
        track_obj = TrackDAO.get_track_by_nd(t.name, t.duration_ms)
        rel_obj = ReleaseDAO.get_release_by_spotify_id(t.album.id)
        for a in t.artists:
            art_obj = ArtistDAO.get_artist_by_spotify_id(a.id)
            # Track-Artist
            if not session.execute(
                select(track_artist)
                .where((track_artist.c.track_id == track_obj.id) & (track_artist.c.artist_id == art_obj.id))
            ).first():
                track_obj.artists.append(art_obj)
            # Release-Artist
            if not session.execute(
                select(release_artist)
                .where((release_artist.c.release_id == rel_obj.id) & (release_artist.c.artist_id == art_obj.id))
            ).first():
                rel_obj.artists.append(art_obj)
        session.flush()


def process_stream_batch(records, user_id):
    """Insert or update stream records from history batch."""
    global last_track_played, last_date, current_loop_streak, current_loop_streak_day

    for rec in records:
        done = rec.get('reason_end') == 'trackdone'
        skip = rec.get('skipped')
        click = rec.get('reason_start') == 'clickrow'
        name = rec.get('master_metadata_track_name')
        artist = rec.get('master_metadata_album_artist_name')

        track_obj = None
        spotify_track_obj = SpotifyTrackDAO.get_spotify_track_by_spotify_id(rec.get('spotify_track_uri', ''))
        if spotify_track_obj:
            track_obj = TrackDAO.get_track_by_id(spotify_track_obj.track_id)
            
        if not track_obj and done:
            track_obj = TrackDAO.get_track_by_nd(name, rec.get('ms_played'))
        elif not track_obj:
            track_obj = TrackDAO.get_tracks_by_name_artist_name(name, artist)
        if not track_obj:
            continue
        
        track_bd_id = track_obj.id
        rec_ts = rec.get('ts')
        rec_duration_play = rec.get('ms_played')
        
        clean_ts = rec_ts.replace("Z", "")  
        date_time_obj = datetime.strptime(clean_ts, "%Y-%m-%dT%H:%M:%S")
        date = date_time_obj.date()
        
        if track_bd_id == last_track_played:
            current_loop_streak += 1

            if date > last_date:
                current_loop_streak_day = 1
            else:
                current_loop_streak_day += 1
        else:
            last_track_played = track_bd_id
            current_loop_streak = 1
            current_loop_streak_day = 1

        
        
        TrackStreamDAO.add_or_update_stream_track(
            track_bd_id,
            user_id,
            done,
            skip,
            click,
            current_loop_streak,
            date_time_obj,
            rec_duration_play
        )
        
        TrackStreamDayDAO.add_or_update_stream_track_day(
            track_bd_id,
            user_id,
            done,
            skip,
            click,
            current_loop_streak_day,
            date,
            rec_duration_play
        )
        
def exploit_streaming_history(streaming_history : list[dict]):
    new_auth = ConfigAuth()
    user = UserDAO.get_all()[0]
    
    user_id = user.id
    token = new_auth.access_token
    
    if not streaming_history:
        raise ValueError('Streaming history file was not provided in exploit_streaming_history function')
            
    seen_artists = set()
    seen_releases = set()
    seen_spotify_tracks = set()

    for batch in chunk_list(streaming_history, 50):
        track_ids = filter_new_track_ids(batch)
        if track_ids:
            tracks = fetch_tracks_in_batches(token, track_ids)
            process_track_metadata(tracks, token, seen_artists, seen_releases, seen_spotify_tracks)
        process_stream_batch(batch, user_id)
        session.commit()
        session.expunge_all()

    logger.info("Algorithm completed successfully")