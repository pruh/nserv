import logging
import datetime
from providers_repo import ProvidersRepo
from providers import Provider, NJTransitProvider
from notifications_repo import NotificationsRepo
from njt_controller import ProviderController, NJTController


log = logging.getLogger(__name__)


class Controller():

    def __init__(self, providers_repo: ProvidersRepo, notifs_repo: NotificationsRepo, njt_controller: NJTController):
        self.__providers_repo = providers_repo
        self.__notifs_repo = notifs_repo

        self.__njt_controller = njt_controller

        # dict of provider id to tuple of provider, its corresponding controller and its current notifications
        self.__providers = {}

        self._cleanup()

    def run(self) -> None:
        try:
            providers = self.__providers_repo.get_providers()
        except:
            logging.exception('failed to query for providers')
            return
        
        log.debug(f"queried providers: {providers}")

        self._update_providers(providers)

        self._update_notifications()

    def _update_providers(self, providers: list) -> None:
        new_providers_ids = {prov.provider_id : prov for prov in providers}

        removed_providers = []
        for provider_id, _ in self.__providers.items():
            if provider_id not in new_providers_ids:
                log.debug(f"provider with id {provider_id} no longer exists")
                removed_providers.append(provider_id)

        if removed_providers:
            self._process_removed_providers(removed_providers)

        # add new providers
        for provider in providers:
            if provider.provider_id not in removed_providers and \
                    provider.provider_id not in self.__providers:
                log.debug(f"adding new provider: {provider}")
                cont = self._get_prov_controller(provider)
                self.__providers[provider.provider_id] = (provider, cont, (),)


    def _process_removed_providers(self, removed_providers: set) -> None:
        for provider_uuid in removed_providers:
            provider, notifs = self.__providers.pop(provider_uuid)
            log.debug(f"processing removed provider: {provider}")
            if not notifs:
                continue

            for notif in notifs:
                log.debug(f"removing notification: {notif}")
                self.__notifications_repo.delete_notification()

    def _get_prov_controller(self, provider: Provider) -> ProviderController:
        if isinstance(provider, NJTransitProvider):
            return self.__njt_controller

        log.warn(f"unsupported provider: {provider}")
        return None

    def _update_notifications(self):
        for provider_uuid, value in self.__providers.items():
            provider, cont, old_notifs = value
            new_notifs = cont.get_notifications(provider)

            try:
                # to avoid complex logic of comparing previous and current notifications,
                # I will create new and then delete old
                for notif in new_notifs:
                    notif_id = self.__notifs_repo.create(notif)
                    notif.notif_id = notif_id
                    log.debug(f"new notification create: {notif}")

                for notif in old_notifs:
                    log.debug(f"removing old notification with id: {notif.notif_id}")
                    self.__notifs_repo.delete(notif.notif_id)

                self.__providers[provider_uuid] = (provider, cont, new_notifs)
            except:
                logging.exception(f"cannot update notifications for provider: {provider}")

    def _cleanup(self):
        self.__njt_controller.cleanup(self.__notifs_repo.get, self.__notifs_repo.delete)
