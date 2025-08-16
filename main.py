# main.py

from streaming_history_analyser.ingest import load_streaming_history_folder


from dao.fetch_dao.track_fetch_dao import TrackFetchDAO
from dao.scrap_dao.spotify_web_scraper import SpotifyWebScraperDAO

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import requests

def main():
    track_id = '5GT7fRtPrfhjJScixSFdZW'
    
    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities["goog:loggingPrefs"] = {"performance": "ALL"}

    # Create the webdriver object and pass the arguments
    options = webdriver.ChromeOptions()

    # Chrome will start in Headless mode
    options.add_argument('headless')

    # Ignores any certificate errors if there is any
    options.add_argument("--ignore-certificate-errors")
    
    wd = webdriver.Chrome()
    session = requests.Session()
    
    web_scraper = SpotifyWebScraperDAO(session, wd)
    print(web_scraper.get_track_stream('61n0wsxweHnJOYyjMlMiPm'))
    wd.quit()
    
    

    # load_streaming_history_folder()
    

    

if __name__ == "__main__":
    main()