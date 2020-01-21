import uuid
import datetime
from typing import Optional, Dict
import requests
import xml.etree.ElementTree as xet
import json


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

    def __init__(self, njt_username: str, njt_password: str, provider_id: uuid, origin_station_code: str, destination_station_code: str):
        self.__njt_username = njt_username
        self.__njt_password = njt_password

        self.__provider_id = provider_id
        self.__origin_station_code = origin_station_code
        self.__destination_station_code = destination_station_code

        # TODO prepare map of two code station id to station normal name
        # TODO define delay threshold

    def update_notifications(self):
        # TODO query station schedule
        station_schedule = self._get_train_schedule(self.__origin_station_code)
        json_str = NJTransitProvider._extract_json(station_schedule.content)
        print(json_str)

        # TODO filter by direction I need

        # TODO look if there are any delayed (with threshold) or canceled trains

        # TODO query notifications
        
    def _get_train_schedule(self, station_code: str) -> dict:
        return requests.get(f"{NJTransitProvider.__njtransit_api_base_url}/getTrainScheduleJSON?" \
            f"username={self.__njt_username}&password={self.__njt_password}&station={station_code}")

    @classmethod
    def _extract_json(cls, content: str):
        """Convert schedule from xml to json"""
        json_data = json.loads(xet.XML(content).text)
        return json_data["STATION"]

