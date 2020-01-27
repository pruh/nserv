import json
import requests
from typing import Optional
import urllib.parse
from requests.auth import HTTPBasicAuth
from providers import Provider, NJTransitProvider
import logging
import uuid
from errors import ApiError
from http import HTTPStatus


log = logging.getLogger(__name__)


class ProvidersRepo():

    def __init__(self, base_url: str, username: Optional[str], password: Optional[str]):
        self.__base_url = base_url
        self.__auth = None
        if username and password:
            self.__auth = HTTPBasicAuth(username=username, password=password)

    def get_providers(self) -> tuple:
        url = urllib.parse.urljoin(self.__base_url, 'providers')
        response = requests.get(url, auth=self.__auth, timeout=20)
        if response.status_code != HTTPStatus.OK:
            raise ApiError(f"failed to query for providers {response}")

        payload = json.loads(response.content.decode('utf-8'))
        return tuple(self._to_provider(item) for item in payload)

    def _to_provider(self, provider_data: dict) -> Provider:
        log.debug(f"parsing {provider_data}")
        provider_type = provider_data.get("type")
        if 'NJTransit' == provider_type:
            return NJTransitProvider(
                provider_id=uuid.UUID(provider_data.get("_id")),
                orig_station_code=provider_data['njtransit']['orig_station_code'],
                dest_station_code=provider_data['njtransit']['dest_station_code'],
            )
        else:
            log.warn(f"Unsupported provider type: {provider_type}")
