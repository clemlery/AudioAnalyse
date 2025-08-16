# models/owner.py
from models.data_class_models.linked_from import LinkedFromUser
from typing import Optional

class Owner(LinkedFromUser):
    display_name : Optional[str] = None