import uuid
import datetime
from typing import Optional


class Provider:
    """
    Data class to describe data received from API.
    """

    def __str__(self) -> str:
        props = ', '.join(f"{name}={value}" for name, value in vars(self).items())
        return f"{type(self).__name__}({props})"

class NJTransitProvider(Provider):
    
    def __init__(self, id: uuid, station_id: str):
        self.id = id
        self.station_id = station_id
