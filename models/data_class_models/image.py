# models/image.py
from pydantic import BaseModel
from typing import Optional

class Image(BaseModel):
    url : str
    width: Optional[int]
    height: Optional[int]