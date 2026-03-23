from dao.base_dao import BaseDbDAO
from core.config import session
from models.orm.artist_sql_model import Artist
from models.orm.track_sql_model import Track
from models.orm.track_stream_sql_model import TrackStream
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import desc


class SORT_TYPE(Enum):
    PLAYED_COUNT = "played_count"
    DURATION_PLAYED = "duration_played"


class TrackStreamDAO(BaseDbDAO):
    @staticmethod
    def add_or_update_stream_track(
        track_id: int,
        user_id: str,
        track_done_bool: bool,
        skipped_bool: bool,
        clicked_row_bool: bool,
        current_loop_streak: int,
        ts,
        duration_played_ms: int,
    ) -> None:
        """
        Ajoute ou met à jour une ligne dans TrackStream pour un utilisateur.
        """

        track_stream = session.get(TrackStream, (user_id, track_id))
        duration_played_s = duration_played_ms // 1000

        if track_stream is None:
            track_stream = TrackStream(
                track_id=track_id,
                user_id=user_id,
                first_played_at=ts,
                last_played_at=ts,
                track_done_count=1 if track_done_bool else 0,
                skipped_count=1 if skipped_bool else 0,
                click_row_count=1 if clicked_row_bool else 0,
                total_duration_play_s=duration_played_s,
            )
            session.add(track_stream)
        else:
            session.expunge(track_stream)
            if track_done_bool:
                track_stream.track_done_count += 1
            elif skipped_bool:
                track_stream.skipped_count += 1
            if clicked_row_bool:
                track_stream.click_row_count += 1

            if current_loop_streak > track_stream.highest_loop_streak:
                track_stream.highest_loop_streak = current_loop_streak

            track_stream.last_played_at = ts
            track_stream.total_duration_play_s += duration_played_s
            session.merge(track_stream)

    @staticmethod
    def get_user_track_stream(user_id: str, track_id: str) -> Optional[TrackStream]:
        """
        Récupère un stream spécifique pour un utilisateur et une track.
        """
        return session.get(TrackStream, {"user_id": user_id, "track_id": track_id})

    @staticmethod
    def get_user_streams(user_id: str) -> List[TrackStream]:
        """
        Retourne toutes les entrées de stream pour un utilisateur donné.
        """
        return TrackStream.query.filter_by(user_id=user_id).all()

    @staticmethod
    def delete_user_track_stream(user_id: str, track_id: str) -> None:
        """
        Supprime une ligne de stream pour un utilisateur et une track.
        """
        stream = session.get(TrackStream, {"user_id": user_id, "track_id": track_id})
        if stream:
            session.delete(stream)
            session.commit()
