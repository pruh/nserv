import uuid


class Provider:
    """
    Data class to describe data received from API.
    """

    def __init__(self, provider_id: uuid):
        self.provider_id = provider_id
        # default duration of produced notifications in minutes
        self.duration = 60

    def __str__(self) -> str:
        props = ', '.join(f"{name}={value}" for name, value in vars(self).items())
        return f"{type(self).__name__}({props})"


class NJTransitProvider(Provider):

    def __init__(self, provider_id: uuid, orig_station_code: str, dest_station_code: str):
        super().__init__(provider_id)

        self.orig_station_code = orig_station_code
        self.dest_station_code = dest_station_code

        self.duration = 15
