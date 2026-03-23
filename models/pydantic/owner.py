# models/owner.py
from models.pydantic.linked_from import LinkedFromUser
from typing import Optional


class Owner(LinkedFromUser):
    display_name: Optional[str] = None
