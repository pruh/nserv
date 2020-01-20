#!/usr/bin/env python3

import argparse
import threading
import time
import logging
from repository import Repository


log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', action='store', type=str, help='API base URL', required=True)
    parser.add_argument('-a', '--username', action='store', type=str, help='HTTP basic auth username')
    parser.add_argument('-p', '--password', action='store', type=str, help='HTTP basic auth password')
    args = parser.parse_args()

    repo = Repository(base_url=args.url, username=args.username, password=args.password)
    thread = threading.Thread(target=_run_bg_jobs, args=(repo,))
    thread.start()


def _run_bg_jobs(repo: Repository) -> None:
    while True:
        _execute_notification_providers(repo)

        # TODO increase timeout
        time.sleep(5)


def _execute_notification_providers(repo: Repository):
    try:
        providers = repo.get_providers()
    except:
        logging.exception('failed to query for providers')
        return

    log.debug(f"queried providers: {providers}")

    # TODO add new notifications for each provider

    # TODO handle duplicates


if __name__ == '__main__':
    main()
