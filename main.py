#!/usr/bin/env python3

import argparse
import threading
import time
from providers_repo import ProvidersRepo
from notifications_repo import NotificationsRepo
from controller import Controller
from njt_controller import NJTController
from logger import setup_uncaught_exceptions_logger, setup_default_loggers


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

    providers_repo = ProvidersRepo(base_url=args.api_base_url, username=args.username, password=args.password)
    notifications_repo = NotificationsRepo(base_url=args.api_base_url, username=args.username, password=args.password)
    njt_controller = NJTController(njt_username=args.njt_username, njt_password=args.njt_password)
    controller = Controller(providers_repo=providers_repo, notifs_repo=notifications_repo, \
        njt_controller=njt_controller)
    thread = threading.Thread(target=_run_bg_jobs, args=(controller,))
    thread.start()


def _run_bg_jobs(controller: Controller) -> None:
    while True:
        controller.run()

        time.sleep(5 * 60)


if __name__ == '__main__':
    main()
