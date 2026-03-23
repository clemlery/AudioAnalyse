# models/copyright.py
from pydantic import BaseModel


class Copyright(BaseModel):
    text: str
    type: str
