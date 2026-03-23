from dao.base_dao import BaseDbDAO
from core.config import session
from models.orm.artist_sql_model import Artist as ArtistDbModel
from models.pydantic.artist import Artist as ArtistDataClasseModel
from typing import Optional, List


class ArtistDAO(BaseDbDAO):
    @staticmethod
    def add_artist(artist_data: ArtistDataClasseModel) -> ArtistDbModel:
        """
        add or update an artist with its metadatas
        """

        artist = ArtistDbModel(
            spotify_id=artist_data.id,
            name=artist_data.name,
            followers=artist_data.followers.total,
            popularity=artist_data.popularity,
            genres=artist_data.genres,
            image=artist_data.images[0].url
            if artist_data.images
            else ["https://example.com/placeholder.png"],
        )

        try:
            session.add(artist)
            session.flush()
        except Exception:
            session.rollback()
            raise
        return artist

    @staticmethod
    def get_all_artist() -> List[ArtistDbModel]:
        return session.query(ArtistDbModel).all()

    @staticmethod
    def get_artist_by_id(artist_id: str) -> Optional[ArtistDbModel]:
        return ArtistDbModel.query.get(artist_id)

    @staticmethod
    def get_artist_by_spotify_id(spotify_id: str) -> Optional[ArtistDbModel]:
        return session.query(ArtistDbModel).filter_by(spotify_id=spotify_id).first()

    @staticmethod
    def delete_artist(artist_id: str) -> None:
        ArtistDbModel = ArtistDbModel.query.get(artist_id)
        if ArtistDbModel:
            session.delete(ArtistDbModel)
        session.commit()
