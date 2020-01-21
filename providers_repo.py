import json
import requests
from typing import Tuple, Optional, Dict
import urllib.parse
from requests.auth import HTTPBasicAuth
from providers import Provider, NJTransitProvider
import logging
import uuid


log = logging.getLogger(__name__)


class ProvidersRepo():

    def __init__(self, base_url: str, username: Optional[str], password: Optional[str],
            njt_username: Optional[str], njt_password: Optional[str]):
        self.__base_url = base_url
        self.__auth = None
        if username and password:
            self.__auth = HTTPBasicAuth(username=username, password=password)
        self.__njt_username = njt_username
        self.__njt_password = njt_password

    def get_providers(self) -> Tuple[Provider, ...]:
        url = urllib.parse.urljoin(self.__base_url, 'providers')
        response = requests.get(url, auth=self.__auth)
        if response.status_code != 200:
            raise ApiError(f"failed to query for providers {response}")

        payload = json.loads(response.content.decode('utf-8'))
        return tuple(self._to_provider(item, njt_username, njt_password) for item in payload)


    def _to_provider(provider_data: Dict[str, str]) -> Provider:
        proovider_type = provider_data.get("type")
        if 'NJTransit' == proovider_type:
            return NJTransitProvider(
                njt_username=self.__njt_username,
                njt_password=self.__njt_password,
                provider_id=uuid.UUID(provider_data.get("_id")),
                origin_station_code=provider_data.get("origin_station_code"),
                destination_station_code=provider_data.get("destination_station_code"),
            )
        else:
            log.debug(f"Unsupported provider type: {proovider_type}")


class ApiError(BaseException):
    pass