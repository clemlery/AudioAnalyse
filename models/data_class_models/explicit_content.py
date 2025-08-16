from pydantic import BaseModel

class ExplicitContent(BaseModel):
    filter_enabled : bool # -> When true, indicates that explicit content should not be played.
    filter_locked : bool # -> When true, indicates that the explicit content setting is locked and can't be changed by the user.
    