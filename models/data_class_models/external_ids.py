# models/external_ids.py
from pydantic import BaseModel
from typing import Optional


class ExternalIds(BaseModel):
    isrc: Optional[str] = None
    ean: Optional[str] = None
    upc: Optional[str] = None
