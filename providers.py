import uuid
import datetime
from typing import Optional, Dict
import requests
import xml.etree.ElementTree as xet
import json
from http import HTTPStatus
import csv


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
            origin_station_code: str, destination_station_code: str):
        self.__njt_username = njt_username
        self.__njt_password = njt_password

        self.__provider_id = provider_id
        self.__origin_station_code = origin_station_code
        self.__destination_station_code = destination_station_code

        self.__delay_trigger_threshold_sec = 5 * 60

    def update_notifications(self):
        raw_data = self._get_train_schedule(self.__origin_station_code)
        station_schedule = NJTransitProvider._extract_json(raw_data.content)

        schedule_updates = self._filter_schedule_updates(station_schedule)
        
        # TODO query notifications

    def _filter_schedule_updates(self, station_schedule: dict) -> list:
        res = []
        for train in station_schedule['ITEMS']['ITEM']:
            if train['STATUS'].strip().lower() != 'canceled' and \
                    int(train['SEC_LATE']) < self.__delay_trigger_threshold_sec:
                continue

            origin_met = False
            origin_station = self.__station_codes.get(self.__origin_station_code, None)
            dest_station = self.__station_codes.get(self.__destination_station_code, None)
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
