# models/paginated_response.py
from typing import Optional
from pydantic import BaseModel, conint, HttpUrl
from models.data_class_models.cursors import Cursors


class PaginatedResponse(BaseModel):
    href: HttpUrl  # lien vers cette page de résultats
    limit: conint(ge=1, le=50)  # type: ignore ; nombre d'éléments demandés (>=1)
    next: Optional[HttpUrl] = None  # lien vers la page suivante
    cursors: Optional[Cursors] = None  # pointeurs pour pagination basée sur curseurs
    offset: Optional[conint(ge=0)] = None  # type: ignore ; décalage de départ (>=0)
    previous: Optional[HttpUrl] = None  # lien vers la page précédente
    total: Optional[conint(ge=0)] = None  # type: ignore ; nombre total d'éléments (>=0)
