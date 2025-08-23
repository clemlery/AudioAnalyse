from dao.base_dao import BaseDbDAO
from config import session
from models.sql_alchemy_models.track_sql_model import Track
from models.sql_alchemy_models.artist_sql_model import Artist
from models.sql_alchemy_models.spotify_track_sql_model import SpotifyTrack
from models.sql_alchemy_models.release_sql_model import Release
from typing import List, Optional
from models.sql_alchemy_models.association import track_artist
from operator import and_


class TrackDAO(BaseDbDAO):
    @staticmethod
    def add_track(track_data) -> Track:
        """
        Ajoute ou met à jour une track avec ses métadonnées.
        """

        track = Track(
            name=track_data.name,
            duration_ms=track_data.duration_ms,
        )

        try:
            session.add(track)
            session.flush()
        except Exception:
            session.rollback()
            raise
        return track

    @staticmethod
    def get_track_by_id(track_id: str) -> Optional[Track]:
        return session.query(Track).filter(Track.id == track_id).first()

    @staticmethod
    def get_track_by_nd(track_name: str, track_duration: int) -> Optional[Track]:
        return (
            session.query(Track)
            .filter(and_(Track.name == track_name, Track.duration_ms == track_duration))
            .first()
        )

    @staticmethod
    def get_tracks_by_name_artist_name(name: str, artist_name: str) -> List[Track]:
        track_artist_rows = (
            session.query(track_artist)
            .join(Track)
            .join(Artist)
            .filter(Track.name == name)
            .filter(Artist.name == artist_name)
            .first()
        )
        if not track_artist_rows:
            return None
        else:
            return session.query(Track).filter(Track.id == track_artist_rows[0]).first()

    @staticmethod
    def get_tracks_by_name_artist_name_release_name(
        name: str, artist_name: str, release_name: str
    ) -> Optional[List[Track]]:
        track_rows = (
            session.query(track_artist)
            .join(Track)
            .join(Artist)
            .join(SpotifyTrack)
            .join(Release)
            .filter(Track.name == name)
            .filter(Artist.name == artist_name)
            .filter(Release.name == release_name)
            .first()
        )
        return session.query(Track).filter(Track.id == track_rows[0]).first()

    @staticmethod
    def get_all_track() -> List[Track]:
        return session.query(Track.id).all()

    @staticmethod
    def delete_track(track_id: str) -> None:
        track = Track.query.get(track_id)
        if track:
            session.delete(track)
        session.commit()
