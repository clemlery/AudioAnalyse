from dao.base_dao import BaseDbDAO
from config import session
from models.sql_alchemy_models.spotify_track_sql_model import SpotifyTrack
from typing import List, Optional


class SpotifyTrackDAO(BaseDbDAO):
    
    @staticmethod
    def add_spotify_track(spotify_id :str, track_id : str, release_id : str) -> None: 
        """
        Ajoute ou met à jour une track avec ses métadonnées.
        """
                
        track = SpotifyTrack(
            track_id=track_id,
            spotify_id=spotify_id,
            release_id=release_id
        )

        try:
            session.add(track)
            session.flush()
        except Exception:
            session.rollback()
            raise
    
    
    @staticmethod
    def get_all_track() -> List[SpotifyTrack]:
        return session.query(SpotifyTrack).all()
    
    @staticmethod
    def get_spotify_track_by_spotify_id(spotify_id : str) -> Optional[SpotifyTrack]:
        return session.query(SpotifyTrack).filter_by(spotify_id=spotify_id).first()

    @staticmethod
    def delete_track(track_id: str) -> None:
        track = SpotifyTrack.query.get(track_id)
        if track:
            session.delete(track)
        session.commit()
