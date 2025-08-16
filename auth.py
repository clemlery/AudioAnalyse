import requests
from datetime import datetime

from constants.api import CLIENT_ID, CLIENT_SECRET, TOKEN_URL

class ConfigAuth:
    def __init__(self):
        self.access_token,_, self.expires = self.get_token_app().values()
    
    @staticmethod    
    def refresh_token(refresh_token):
        if not refresh_token:
            raise ValueError('Refresh_token is missing')
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(TOKEN_URL, data=data, headers=headers)
        resp.raise_for_status()
        return resp.json() 
    
    def get_token_app(self) -> dict:
        data = {
            "grant_type" : "client_credentials",
            "client_id" : CLIENT_ID,
            "client_secret" : CLIENT_SECRET
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(TOKEN_URL, data=data, headers=headers)
        resp.raise_for_status()
        return resp.json() 

        
