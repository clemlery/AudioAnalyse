# models/saved_track.py
from datetime import datetime, timezone
from pydantic import BaseModel, field_validator
from models.data_class_models.track import Track


class SavedTrack(BaseModel):
    added_at: datetime
    track: Track

    @field_validator('added_at', mode='before')
    def parse_and_check_added_at(cls, v):
        # Convertit une chaîne ISO en datetime
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        # Vérifie que le datetime est timezone-aware
        if v.tzinfo is None:
            raise ValueError('added_at doit être timezone-aware')
        # Vérifie que la date n'est pas dans le futur
        if v > datetime.now(timezone.utc):
            raise ValueError('added_at ne peut être dans le futur')
        return v
