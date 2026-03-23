from dao.base_dao import BaseDbDAO
from core.config import session
from models.orm.release_sql_model import Release
from models.pydantic.album import Album
from typing import List, Optional


class ReleaseDAO(BaseDbDAO):
    @staticmethod
    def add_release(release_data: Album, release_type: str) -> Release:
        """
        Ajoute ou met à jour une release avec ses métadonnées.
        """

        release = Release(
            spotify_id=release_data.id,
            release_type=release_type,
            name=release_data.name,
            popularity=release_data.popularity,
            image=release_data.images[0].url,
            release_date=release_data.release_date,
            total_tracks=release_data.total_tracks,
        )

        try:
            session.add(release)
            session.flush()
        except Exception:
            session.rollback()
            raise
        return release

    @staticmethod
    def get_all_release() -> List[Release]:
        return session.query(Release.id).all()

    @staticmethod
    def get_release_by_spotify_id(spotify_id: str) -> Optional[Release]:
        return session.query(Release).filter_by(spotify_id=spotify_id).first()

    @staticmethod
    def delete_release(release_id: str) -> None:
        release = Release.query.get(release_id)
        if release:
            session.delete(release)
        session.commit()
