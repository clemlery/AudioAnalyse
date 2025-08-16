# models/albums.py
from typing import Union, List
from models.data_class_models.paginated_response import PaginatedResponse
from models.data_class_models.album import Album
from models.data_class_models.simplified_album import SimplifiedAlbum
from models.data_class_models.saved_album import SavedAlbum

class Albums(PaginatedResponse):
    # items peut contenir soit des Album, soit des SimplifiedAlbum, soit des SavedAlbum
    items: List[Union[Album, SimplifiedAlbum, SavedAlbum]]


    

                
    
    