from dao.base_dao import BaseDbDAO
from core.config import session
from models.orm.track_stream_day_sql_model import TrackStreamDay
from typing import Optional, List
from datetime import datetime
from sqlalchemy import desc


class TrackStreamDayDAO(BaseDbDAO):
    @staticmethod
    def add_or_update_stream_track_day(
        track_id: int,
        user_id: str,
        track_done_bool: bool,
        skipped_bool: bool,
        clicked_row_bool: bool,
        current_loop_streak: int,
        ts: str,
        duration_played_ms: int,
    ) -> None:
        """
        Ajoute ou met à jour une ligne dans TrackStreamDay pour un utilisateur.
        """

        track_stream_day = session.get(TrackStreamDay, (track_id, user_id, ts))
        duration_played_s = duration_played_ms // 1000

        if track_stream_day is None:
            track_stream_day = TrackStreamDay(
                track_id=track_id,
                user_id=user_id,
                date=ts,
                track_done_count=1 if track_done_bool else 0,
                skipped_count=1 if skipped_bool else 0,
                click_row_count=1 if clicked_row_bool else 0,
                total_duration_play_s=duration_played_s,
                highest_loop_streak=1,
            )
            session.add(track_stream_day)
        else:
            session.expunge(track_stream_day)
            if track_done_bool:
                track_stream_day.track_done_count += 1
            elif skipped_bool:
                track_stream_day.skipped_count += 1

            if clicked_row_bool:
                track_stream_day.click_row_count += 1

            if current_loop_streak > track_stream_day.highest_loop_streak:
                track_stream_day.highest_loop_streak = current_loop_streak

            track_stream_day.total_duration_play_s += duration_played_s
            session.merge(track_stream_day)

    @staticmethod
    def get_user_track_stream(user_id: str, track_id: str) -> Optional[TrackStreamDay]:
        """
        Récupère un stream spécifique pour un utilisateur et une track.
        """
        return session.get(TrackStreamDay, {"user_id": user_id, "track_id": track_id})

    @staticmethod
    def get_user_streams(user_id: str) -> List[TrackStreamDay]:
        """
        Retourne toutes les entrées de stream pour un utilisateur donné.
        """
        return TrackStreamDay.query.filter_by(user_id=user_id).all()
