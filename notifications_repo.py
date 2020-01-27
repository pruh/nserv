import json
import requests
from typing import Optional
import urllib.parse
from requests.auth import HTTPBasicAuth
from notification import Notification
import uuid
import dateutil.parser
from errors import ApiError
from http import HTTPStatus


class NotificationsRepo:

    def __init__(self, base_url: str, username: Optional[str], password: Optional[str]):
        self.__base_url = base_url
        self.__auth = None
        if username and password:
            self.__auth = HTTPBasicAuth(username=username, password=password)

    def get(self, only_current: bool = True) -> tuple:
        url_end = "notifications?only_current=" + 'true' if only_current else 'false'
        url = urllib.parse.urljoin(self.__base_url, url_end)
        r = requests.get(url, auth=self.__auth, timeout=5)
        if r.status_code != HTTPStatus.OK:
            raise ApiError(f"failed to query for notifications {r}")

        payload = json.loads(r.content.decode('utf-8'))
        return tuple(NotificationsRepo._to_notification(item) for item in payload)

    def create(self, notif: Notification) -> uuid:
        url = urllib.parse.urljoin(self.__base_url, 'notifications')
        data = NotificationsRepo._from_notification(notif)
        r = requests.post(url, auth=self.__auth, json=data, timeout=20)
        if r.status_code != HTTPStatus.CREATED:
            raise ApiError(f"error while storing notification {r.content}")

        if 'Location' in r.headers:
            location = r.headers.get('Location')
            return location.split('/')[-1]

        return 

    def delete(self, notif_uuid: uuid) -> bool:
        url = urllib.parse.urljoin(self.__base_url, f"notifications/{notif_uuid}")
        r = requests.delete(url, auth=self.__auth, timeout=20)
        if r.status_code != HTTPStatus.NO_CONTENT:
            raise ApiError(f"error while deleting notification {r.content}")

    @classmethod
    def _to_notification(cls, notif_dict: dict) -> Notification:
        return Notification(
            notif_id=uuid.UUID(notif_dict.get("_id")),
            title=notif_dict.get("title"),
            message=notif_dict.get("message"),
            start_time=dateutil.parser.parse(notif_dict.get("start_time")),
            end_time=dateutil.parser.parse(notif_dict.get("end_time")),
            source=notif_dict.get("source"),
        )

    @classmethod
    def _from_notification(cls, notif: Notification) -> dict:
        return {
            "_id": notif.notif_id, \
            "title": notif.title, \
            "message": notif.message, \
            "start_time": notif.start_time, \
            "end_time": notif.end_time, \
            "source": notif.source,
        }
