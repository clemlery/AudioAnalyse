# models/saved_album.py
from pydantic import BaseModel, field_validator
from datetime import datetime, timezone
from models.pydantic.album import Album


class SavedAlbum(BaseModel):
    added_at: datetime
    album: Album

    @field_validator("added_at", mode="before")
    def parse_and_check_added_at(cls, v):
        # Convertit une chaîne ISO en datetime
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        # Vérifie que le datetime est timezone-aware
        if v.tzinfo is None:
            raise ValueError("added_at doit être timezone-aware")
        # Vérifie que la date n'est pas dans le futur
        if v > datetime.now(timezone.utc):
            raise ValueError("added_at ne peut être dans le futur")
        return v
