import json
import requests
from typing import Tuple, Optional, Dict
import urllib.parse
from requests.auth import HTTPBasicAuth
from provider import Provider, NJTransitProvider
import logging
import uuid


log = logging.getLogger(__name__)


class Repository():

    def __init__(self, base_url: str, username: Optional[str], password: Optional[str]):
        self.__base_url = base_url
        self.__auth = None
        if username and password:
            self.__auth = HTTPBasicAuth(username=username, password=password)

    def get_providers(self) -> Tuple[Provider, ...]:
        url = urllib.parse.urljoin(self.__base_url, 'providers')
        response = requests.get(url, auth=self.__auth)
        if response.status_code != 200:
            raise ApiError(f"failed to query for providers {response}")

        payload = json.loads(response.content.decode('utf-8'))
        return tuple(self.__to_provider(item) for item in payload)
    
    def __to_provider(self, provider_data: Dict[str, str]) -> Provider:
        proovider_type = provider_data.get("type")
        if 'NJTransit' == proovider_type:
            return NJTransitProvider(
                id=uuid.UUID(provider_data.get("_id")),
                njtransit=provider_data.get("njtransit"),
            )
        else:
            log.debug(f"Unsupported provider type: {proovider_type}")


class ApiError(BaseException):
    pass