from typing import Any
from dao.base_dao import BaseScrapDAO

from constants.scraping import SPOTIFY_INTERN_API


class SpotifyArtistScraperDAO(BaseScrapDAO):
    def get_artist_monthly_listeners(self, artist_id: str) -> None | int:
        payload = {
            "variables": {"uri": f"spotify:artist:{artist_id}"},
            "operationName": "queryArtistOverview",
            "extensions": {
                "persistedQuery": {"version": 1, "sha256Hash": self.hash_value}
            },
        }
        resp = self.sess.post(SPOTIFY_INTERN_API, json=payload)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        try:
            ml = data["data"]["artistUnion"]["stats"]["monthlyListeners"]
            return ml if isinstance(ml, int) else None
        except (KeyError, TypeError):
            return None
