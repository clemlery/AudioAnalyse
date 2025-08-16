# service.py



from constants.service import RELEASE_TYPE, ALBUM_MIN_DURATION_MS, ALBUM_MIN_TRACK_NUMBER, EP_MIN_TRACK_NUMBER
from datetime import datetime, timedelta, timezone

from dao.db_dao.user_dao import UserDAO
from auth import ConfigAuth


def chunk_list(lst, size):
    """Yield successive chunks of given size from lst."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]
        
def total_duration_ms(tracks) -> int:
    return sum(track.duration_ms for track in tracks)

def define_release_type(release_data) -> RELEASE_TYPE:
    """ Return SINGLE, EP or ALBUM based on the spotify rules """
    track_number = len(release_data.tracks.items)
    release_duration_ms = total_duration_ms(release_data.tracks.items)
    if release_duration_ms >= ALBUM_MIN_DURATION_MS or track_number >= ALBUM_MIN_TRACK_NUMBER:
        return RELEASE_TYPE.ALBUM
    elif track_number >= EP_MIN_TRACK_NUMBER and release_duration_ms <= ALBUM_MIN_DURATION_MS:
        return RELEASE_TYPE.EP
    else:
        return RELEASE_TYPE.SINGLE
        
def verify_token(user):
    exp = user.updated_at + timedelta(seconds=user.expires_in)
    if datetime.now(timezone.utc) >= exp:
        tokens = ConfigAuth.refresh_token(user.refresh_token)
        UserDAO.update_user_access_token(
            user_id=user.id,
            access_token=tokens['access_token'],
            expires_in=tokens['expires_in']
        )
    

    

    
    