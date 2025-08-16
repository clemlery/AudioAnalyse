"""dao/fetch_dao/user_fetch_dao.py

Contains the Fetch DAO (Data Access Object) for all operations related to Spotify user profiles.
Each method corresponds to a Spotify API REST endpoint returning user information.
"""
from constants.api import SPOTIFY_USER_PROFILE_URL
from dao.base_dao import BaseFetchDAO
from models.data_class_models.user import User


class UserFetchDao(BaseFetchDAO):
    """Data Access Object for Spotify user profile information."""
    
    @staticmethod
    def fetch_users_profile(
        access_token : str,
    ) -> User:
        """Retrieve the user's profile information.

        Keyword arguments:
        access_token -- a valid Spotify access token
        """
        data = UserFetchDao._request(SPOTIFY_USER_PROFILE_URL, access_token)
        return User.model_validate(data)