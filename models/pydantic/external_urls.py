# models/external_urls.py
from pydantic import BaseModel, HttpUrl


class ExternalUrls(BaseModel):
    spotify: HttpUrl
