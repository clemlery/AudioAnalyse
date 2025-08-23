# models/followers.py
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional


class Followers(BaseModel):
    href: Optional[HttpUrl] = None
    total: int = Field(..., ge=0)
