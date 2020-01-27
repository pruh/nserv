import requests
import logging
import datetime
from dateutil.tz import tzlocal
import csv
import json
import xml.etree.ElementTree as xet
from notification import Notification
from providers import Provider, NJTransitProvider
from typing import Callable


log = logging.getLogger(__name__)


class ProviderController:

    def get_notifications(self, prov: Provider) -> tuple:
        pass

    def cleanup(self, query_notifs_fun: Callable, delete_notif_fun: Callable) -> None:
        pass


class NJTController(ProviderController):

    NJT_SOURCE = 'njtransit'
    API_BASE = 'http://traindata.njtransit.com:8092/NJTTrainData.asmx'
    
    def __init__(self, njt_username: str, njt_password: str):
        self.__njt_username = njt_username
        self.__njt_password = njt_password

        self.__delay_trigger_threshold_sec = 5 * 60
        self.__station_codes = self._load_station_codes()

    def _load_station_codes(self) -> dict:
        station_codes = {}
        with open('njt_stations.csv', 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                station_codes[row[1]] = row[0].lower()
        return station_codes

    def get_notifications(self, prov: NJTransitProvider) -> tuple:
        log.debug(f"querying notifications for {prov.orig_station_code}")
        try:
            raw_data = NJTController._get_train_schedule(self.__njt_username, \
                self.__njt_password, prov.orig_station_code)
            station_schedule = NJTController._extract_json(raw_data.content)
        except:
            logging.exception(f"error while requesting NJT schedule: {raw_data.content}")
            return ()

        orig_station = self.__station_codes.get(prov.orig_station_code, None)
        dest_station = self.__station_codes.get(prov.dest_station_code, None)
        schedule_updates = self._filter_schedule_updates(station_schedule, \
            orig_station, dest_station, self.__delay_trigger_threshold_sec)
        log.debug(f"found {len(schedule_updates)} NJT train schedule changes")
        if len(schedule_updates) == 0:
            return ()

        return NJTController._to_notifications(schedule_updates, orig_station, dest_station, \
            prov.duration ,self.__delay_trigger_threshold_sec)

    @classmethod
    def _to_notifications(cls, schedule_updates: list, orig_station: str, dest_station: str, \
            duration: int, delay_trigger_threashold: int) -> tuple:
        now = datetime.datetime.now(tzlocal()).replace(microsecond=0)
        
        notifs = []
        for updated in schedule_updates:
            departure_time = updated['SCHED_DEP_DATE']
            if int(updated['SEC_LATE']) >= delay_trigger_threashold:
                time = datetime.timedelta(seconds=int(updated['SEC_LATE']))
                reason = f"{time} minutes late"
            elif updated['STATUS'].strip().lower() == 'canceled':
                reason = 'canceled'
            else:
                reason = 'unknown status'
            title = f"{departure_time} train from {orig_station.title()} to {dest_station.title()} is {reason}"
            notif = Notification(
                notif_id=None,
                title=title,
                message=None,
                start_time=now.isoformat(),
                end_time=(now + datetime.timedelta(minutes=duration)).isoformat(),
                source=NJTController.NJT_SOURCE,
            )
            log.debug(f"new notification {notif} for train id {updated['TRAIN_ID']}")
            notifs.append(notif)

        return tuple(notifs)

    @classmethod
    def _get_train_schedule(cls, njt_username: str, njt_password: str, station_code: str) -> dict:
        log.debug('checking for NJT train schedule changes')
        try:
            return requests.get(f"{NJTController.API_BASE}/getTrainScheduleJSON?" \
                f"username={njt_username}&password={njt_password}&station={station_code}")
        except:
            logging.exception('cannot query for NJT train schedule')

    @classmethod
    def _extract_json(cls, content: str):
        """Convert schedule from xml to json"""
        json_data = json.loads(xet.XML(content).text)
        return json_data['STATION']

    @classmethod
    def _filter_schedule_updates(cls, station_schedule: dict, orig_station: str, \
            dest_station: str, delay_trigger_threashold: int) -> list:
        if 'ITEMS' not in station_schedule or not station_schedule['ITEMS']:
            return []

        changes = []
        for train in station_schedule['ITEMS']['ITEM']:
            if train['STATUS'].strip().lower() != 'canceled' and \
                    int(train['SEC_LATE']) < delay_trigger_threashold:
                continue

            orig_passed = False
            for stop in train['STOPS']['STOP']:
                if stop['NAME'].strip().lower() == orig_station:
                    if stop['DEPARTED'] == 'YES':
                        break
                    orig_passed = True
                if stop['NAME'].strip().lower() == dest_station:
                    if orig_passed:
                        changes.append(train)
                    break

        return changes

    def cleanup(self, query_notifs_fun: Callable, delete_notif_fun: Callable) -> None:
        log.debug('cleaning up NJT controller')
        try:
            notifs = query_notifs_fun()
            for notif in notifs:
                if notif.source == NJTController.NJT_SOURCE:
                    log.debug(f"cleaning up NJT notification {notif}")
                    delete_notif_fun(notif.notif_id)
        except:
            logging.exception('error while cleaning up NJT controller')
