
from dao.base_dao import BaseScrapDAO

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from constants.scraping import SPOTIFY_INTERN_API




class SpotifyWebScraperDAO(BaseScrapDAO):
    
    def get_track_stream(self, track_id : str) -> int:
        payload = {
            "variables": {"uri": f"spotify:track:{track_id}"},
            "operationName": "getTrack",
            "extensions": {"persistedQuery": {"version": 1, "sha256Hash": self.hash_value}},
        }        
        resp = self.sess.post(SPOTIFY_INTERN_API, json=payload)
        return resp.text

    def get_artist_monthly_listeners(self, artist_id) -> int:
        pass
    

        
    
    