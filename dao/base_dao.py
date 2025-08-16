# base_dao.py

from config import logger
from typing import Callable, Optional, Dict, Any
import requests
from functools import wraps
import re
from selenium.webdriver.common.by import By
import time 
import json

from constants.scraping import SPOTIFY_BASE_URL, TRACK_URL
from dao.service import get_class_that_defined_method, get_cookies, get_user_agent

# We create the logging decorator 
def logging_func_fetch_dao(fn : Callable) -> Callable:
    # To keep the function metadata
    @wraps(fn)
    def wrapper(*args, **kwargs):
        args_name = fn.__code__.co_varnames[:fn.__code__.co_argcount]
        filtered = [
            f"{name}: {value}"
            for name, value in zip(args_name, args)
            if re.search(r'^(?:album|artist|track)_(?:ids|id)', name)
        ]
        logger.info(
            f"EXECUTING {fn.__name__} "
            f"FROM CLASS {get_class_that_defined_method(fn)} "
            f"WITH ARGS ({' | '.join(filtered)})"
        )        
        try:
            res = fn(*args,**kwargs)
        except Exception as e:
            logger.error(f"ERROR EXECUTING {fn.__name__}: {e}", exc_info=True)
            raise 
        else: return res
    return wrapper

def loggin_func_db_dao(fn : Callable) -> Callable:
    # To keep the function metadata 
    @wraps(fn)
    def wrapper(*args, **kwargs):
        logger.info(f"EXECUTING {fn.__name__} FROM CLASS {get_class_that_defined_method(fn)}")
        try:
            res = fn(*args,**kwargs)
        except Exception as e:
            logger.error(f"ERROR EXECUTING {fn.__name__}: {e}", exc_info=True)
            raise 
        else: return res
    return wrapper
        

# We create the mother class of BaseDbDAO and BaseFetchDAO
class BaseDAO:
    pass
  
class BaseDbDAO(BaseDAO):
    # We apply the logging decorator to all subclasses 
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attr, value in cls.__dict__.items():
            if callable(value) and not value.__name__.startswith('__') and isinstance(value, staticmethod):
                func = value.__func__
                setattr(cls, attr, staticmethod(loggin_func_db_dao(func)))

class BaseFetchDAO(BaseDAO):
    # We apply the logging decorator to all subclasses 
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for attr, value in cls.__dict__.items():
            if callable(value) and not value.__name__.startswith('__') and isinstance(value, staticmethod):
                func = value.__func__
                setattr(cls, attr, staticmethod(logging_func_fetch_dao(func)))
    
    def _request(
        url: str,
        access_token: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Private method used to execute GET request on the Spotify API,handle headers and validate the JSON parsing

        Keyword arguments:
        url -- a valid URL
        access_token -- a valid spotify access token
        params -- and Optional dictionary (parameter_name : parameter_value) that contains all the parameters to add in the GET request parameters
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

class BaseScrapDAO(BaseDAO):
    def __init__(self, session, webdriver):

        self.delay = 10
        webdriver.get(SPOTIFY_BASE_URL)
        
        cookie_button_id = 'onetrust-accept-btn-handler'

        time.sleep(5)
        webdriver.find_element(By.ID, cookie_button_id).click()
        
        webdriver.get(TRACK_URL+'5GT7fRtPrfhjJScixSFdZW')
        time.sleep(10)
        logs = webdriver.get_log("performance")
        
        for log in logs:
            msg = json.loads(log["message"]).get("message", {})
            if msg.get("method") == "Network.requestWillBeSent":
                req = msg.get("params", {}).get("request")
                if not req:
                    continue
                if not req.get("url", "").endswith("/pathfinder/v2/query"):
                    continue

                headers = req.get("headers", {})
                post_data = req.get("postData")  # camelCase correct
                if not post_data:
                    continue

                try:
                    post_json = json.loads(post_data)
                except json.JSONDecodeError:
                    continue

                uri = post_json.get("variables", {}).get("uri", "")
                if not uri.startswith("spotify:track"):
                    continue

                client_token = headers.get("client-token")
                access_token = headers.get("authorization")
                hash_value = post_json.get("extensions", {}).get("persistedQuery", {}).get("sha256Hash")

                if client_token and access_token and hash_value:
                    print(f"client-token: {client_token}")
                    print(f"access_token: {access_token}")
                    print(f"sha256Hash: {hash_value}")
                    break


        
        cookies = get_cookies(webdriver)
        user_agent = get_user_agent(webdriver)

        session.headers.update(
            {
                'Accept': 'application/json',
                'authorization': access_token,
                'client-token' : client_token,
                'content-type': 'application/json;charset=UTF-8',
                'User-Agent': user_agent
            }
        )
        
        simple_cookies = {c['name'] : str(c['value']) for c in cookies}
        
        jar = requests.utils.cookiejar_from_dict(simple_cookies)
        session.cookies = jar
        
        self.hash_value = hash_value
        self.session = session
        self.webdriver = webdriver
        
    # We apply the logging decorator to all subclasses
    # def __init_subclass__(cls, **kwargs):
    #     super().__init_subclass__(**kwargs)
    #     for attr, value in cls.__dict__.items():
    #         if callable(value) and not value.__name__.startswith('__') and isinstance(value, staticmethod):
    #             func = value.__func__
    #             setattr(cls, attr, staticmethod(logging_func_fetch_dao(func)))