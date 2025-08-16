# main.py

from dao.service import BrowserManager, get_tokens
from streaming_history_analyser.ingest import load_streaming_history_folder


from dao.db_dao.spotify_track_dao import SpotifyTrackDAO
from dao.scrap_dao.spotify_web_scraper import SpotifyWebScraperDAO

from selenium import webdriver
from constants.scraping import SPOTIFY_BASE_URL, TRACK_URL

import requests

def main():
    track_id = '5GT7fRtPrfhjJScixSFdZW'
    
    bm = BrowserManager()
    bm.open_page(SPOTIFY_BASE_URL)
    bm.consent_cookies()
    bm.open_page(TRACK_URL+track_id)
    logs = bm.get_cdp_log()
    client_token, access_token, hash_value = get_tokens(logs)
    print(get_tokens(bm.get_cdp_log()))
    cookies = bm.get_cookies()
    user_agent = bm.get_user_agent()
    bm.quit_driver()
    web_scraper = SpotifyWebScraperDAO(access_token, client_token, user_agent, hash_value, cookies)
    
    spotify_tracks = SpotifyTrackDAO.get_all_track()
    for i in range(100):
        if web_scraper.get_track_stream(spotify_tracks[i].spotify_id):
            print(f'{i} : OK')
        else:
            print('NOP')
    
    
    

    # load_streaming_history_folder()
    

    

if __name__ == "__main__":
    main()