# models/playlist_track.py
from datetime import datetime, timezone
from typing import Union
from pydantic import BaseModel, field_validator, conlist, constr
from models.data_class_models.linked_from import LinkedFromUser
from models.data_class_models.track import Track

class PlaylistTrack(BaseModel):
    track: Track
    added_at: datetime
    added_by: LinkedFromUser
    is_local: bool


    @field_validator('added_at', mode='before')
    def played_at_timezone_and_not_future(cls, v: Union[str, datetime]) -> datetime:
        """
        Validator pour s'assurer que :
        - la date est au format ISO avec timezone (ou datetime à tzinfo)
        - la date n'est pas dans le futur
        """
        # Conversion depuis une chaîne ISO
        if isinstance(v, str):
            # Gère le suffixe 'Z' pour UTC
            iso = v
            if iso.endswith('Z'):
                iso = iso[:-1] + '+00:00'
            v = datetime.fromisoformat(iso)
        # Vérifier timezone-aware
        if v.tzinfo is None:
            raise ValueError('added_at doit être timezone-aware')
        # Vérifier que ce n'est pas une date future
        if v > datetime.now(timezone.utc):
            raise ValueError('added_at ne peut être dans le futur')
        return v