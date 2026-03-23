from typing import Any

from requests import HTTPError
from dao.base_dao import BaseScrapDAO

from constants.scraping import SPOTIFY_INTERN_API


class SpotifyTrackScraperDAO(BaseScrapDAO):
    def get_track_playcount(self, track_id: str) -> int:
        payload = {
            "variables": {"uri": f"spotify:track:{track_id}"},
            "operationName": "getTrack",
            "extensions": {
                "persistedQuery": {"version": 1, "sha256Hash": self.hash_value}
            },
        }

        resp = self.sess.post(SPOTIFY_INTERN_API, json=payload)

        try:
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            ml = int(data["data"]["trackUnion"]["playcount"])
            return ml if isinstance(ml, int) else None
        except (KeyError, TypeError, HTTPError):
            return None
