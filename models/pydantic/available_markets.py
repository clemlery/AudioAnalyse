# models/available_markets
from pydantic import conlist, constr

# Alias de type pour les codes ISO 3166-1 alpha-2
# Liste d'au moins un code à deux lettres majuscules
AvailableMarkets = conlist(
    constr(pattern=r"^[A-Z]{2}$"),
)
