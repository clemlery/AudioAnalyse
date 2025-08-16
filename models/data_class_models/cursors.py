# models/cursors.py
from pydantic import BaseModel
from typing import Optional

class Cursors(BaseModel):
    after : Optional[str] = None
    before : Optional[str] = None