from datetime import datetime
from dao.base_dao import BaseDbDAO
from models.sql_alchemy_models.user_sql_model import User
from typing import Optional, List
from config import session


class UserDAO(BaseDbDAO):
    @staticmethod
    def add_user(user_data, access_token, refresh_token, expires_in) -> None:
        """Ajoute ou met à jour un utilisateur."""
        user = User(
            id=user_data.id,
            display_name=user_data.display_name,
            email=user_data.email,
            country=user_data.country,
            product=user_data.product,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
        session.merge(user)
        session.commit()

    @staticmethod
    def get_all() -> List[User]:
        return session.query(User).all()

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Récupère un utilisateur par son ID."""
        return session.get(User, user_id)

    @staticmethod
    def get_user_by_access_token(access_token: str) -> Optional[User]:
        """Récupère un utilisateur par son access token"""
        return session.query(User).filter_by(access_token=access_token).first()

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Récupère un utilisateur par son adresse email."""
        return session.query(User).filter_by(email=email)

    @staticmethod
    def delete_user(user_id: str) -> None:
        """Supprime un utilisateur par son ID."""
        user = User.query.get(user_id)
        if user:
            session.delete(user)
            session.commit()

    @staticmethod
    def update_user_access_token(
        user_id: str,
        access_token: Optional[str] = None,
        expires_in: Optional[int] = None,
    ) -> Optional[User]:
        """
        Met à jour les tokens d'un utilisateurs
        """
        user = session.get(User, user_id)
        if not user:
            return None

        user.access_token = access_token
        user.expires_in = expires_in
        user.token_last_update = datetime.now()

        session.commit()
        return user
