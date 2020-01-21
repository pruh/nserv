import uuid
import datetime
from typing import Optional, Dict
import requests
import xml.etree.ElementTree as xet
import json
from http import HTTPStatus
import csv
from notifications_repo import NotificationsRepo
import logging
from notification import Notification
from datetime import datetime


log = logging.getLogger(__name__)


def _load_station_codes() -> dict:
    station_codes = {}
    with open('njt_stations.csv', 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            station_codes[row[1]] = row[0].lower()
    return station_codes


class Provider:
    """
    Data class to describe data received from API.
    """
    def update_notifications(self):
        pass

    def __str__(self) -> str:
        props = ', '.join(f"{name}={value}" for name, value in vars(self).items())
        return f"{type(self).__name__}({props})"

class NJTransitProvider(Provider):

    __njtransit_api_base_url = 'http://traindata.njtransit.com:8092/NJTTrainData.asmx'
    __station_codes = _load_station_codes()

    def __init__(self, njt_username: str, njt_password: str, provider_id: uuid,
            orig_station_code: str, dest_station_code: str, notifications_repo: NotificationsRepo):
        self.__njt_username = njt_username
        self.__njt_password = njt_password

        self.__provider_id = provider_id
        self.__orig_station_code = orig_station_code
        self.__dest_station_code = dest_station_code

        self.__delay_trigger_threshold_sec = 5 * 60

        self.__notifications_repo = notifications_repo

    def update_notifications(self):
        log.debug(f"querying notifications for {self.__orig_station_code}")
        raw_data = self._get_train_schedule(self.__orig_station_code)
        try:
            station_schedule = NJTransitProvider._extract_json(raw_data.content)
        except:
            logging.exception(f"not able to parse NJT response: {raw_data.content}")
            return

        schedule_updates = self._filter_schedule_updates(station_schedule)
        if len(schedule_updates) == 0:
            log.debug('no schedule updates')
            return

        notifs = self.__get_njt_notifications(title)

        self._store_notifications_if_missing(schedule_updates, notifs)

    def _store_notification_if_missing(self, schedule_updates: list, notifs: list) -> None:
        title = f"{len(schedule_updates)} train(s) from " \
            f"{self.__station_codes.get(self.__orig_station_code, None)} " \
            f"to {self.__station_codes.get(self.__dest_station_code, None)} have modified schedule "
        
        now = datetime.now()
        if len(notifs) == 0:
            log.debug('no NJTransit notification, storing one')
            self.__notifications_repo.store_notification(Notification(
                title=title,
                start_time=now,
                end_time=now + datetime.timedelta(hours=1),
                source=notif_dict.get(njtransit),
            ))
            return

        for notif in notifs:
            if notif.title == title:
                log.debug('notification with the same title exists')
                break
        else:
            log.debug('no NJTransit notification with given title, storing one')
            self.__notifications_repo.store_notification(Notification(
                title=title,
                start_time=now,
                end_time=now + datetime.timedelta(hours=1),
                source=notif_dict.get(njtransit),
            ))

    def __get_njt_notifications(self) -> list:
        return [notif for notif in self.__notifications_repo.get_notifications(True) if notif.source == 'njtransit']

    def _filter_schedule_updates(self, station_schedule: dict) -> list:
        if 'ITEMS' not in station_schedule or not station_schedule['ITEMS']:
            return []

        res = []
        origin_station = self.__station_codes.get(self.__orig_station_code, None)
        dest_station = self.__station_codes.get(self.__dest_station_code, None)
        for train in station_schedule['ITEMS']['ITEM']:
            if train['STATUS'].strip().lower() != 'canceled' and \
                    int(train['SEC_LATE']) < self.__delay_trigger_threshold_sec:
                continue

            origin_met = False
            for stop in train['STOPS']['STOP']:
                if stop['NAME'].strip().lower() == origin_station:
                    if stop['DEPARTED'] == 'YES':
                        break
                    origin_met = True
                if stop['NAME'].strip().lower() == dest_station:
                    if origin_met:
                        res.append(train)
                    break

        return res
    
    def _get_train_schedule(self, station_code: str) -> dict:
        return requests.get(f"{NJTransitProvider.__njtransit_api_base_url}/getTrainScheduleJSON?" \
            f"username={self.__njt_username}&password={self.__njt_password}&station={station_code}")

    @classmethod
    def _extract_json(cls, content: str):
        """Convert schedule from xml to json"""
        json_data = json.loads(xet.XML(content).text)
        return json_data['STATION']
