#!/usr/bin/env python3

import argparse
import threading
import time
import logging
from providers_repo import ProvidersRepo
from providers import NJTransitProvider
from notifications_repo import NotificationsRepo
from logger import setup_uncaught_exceptions_logger, setup_default_loggers


log = logging.getLogger(__name__)


def main():
    setup_uncaught_exceptions_logger()
    setup_default_loggers()

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--api-base-url', action='store', type=str, help='API base URL', required=True)
    parser.add_argument('-a', '--username', action='store', type=str, help='HTTP basic auth username')
    parser.add_argument('-p', '--password', action='store', type=str, help='HTTP basic auth password')
    parser.add_argument('--njt-username', action='store', type=str, help='Username to access NJT API')
    parser.add_argument('--njt-password', action='store', type=str, help='Password to access NJT API')
    args = parser.parse_args()

    notifications_repo = NotificationsRepo(base_url=args.api_base_url, username=args.username, password=args.password)
    repo = ProvidersRepo(base_url=args.api_base_url, username=args.username, password=args.password,
            njt_username=args.njt_username, njt_password=args.njt_password, notifications_repo=notifications_repo)
    thread = threading.Thread(target=_run_bg_jobs, args=(repo,notifications_repo,))
    thread.start()


def _run_bg_jobs(repo: ProvidersRepo, notifications_repo: NotificationsRepo) -> None:
    while True:
        _execute_notification_providers(repo, notifications_repo)

        # TODO increase timeout
        time.sleep(5)


def _execute_notification_providers(repo: ProvidersRepo, notifications_repo: NotificationsRepo):
    try:
        providers = repo.get_providers()
    except:
        logging.exception('failed to query for providers')
        return

    log.debug(f"queried providers: {providers}")

    for provider in providers:
        provider.update_notifications()


if __name__ == '__main__':
    main()
