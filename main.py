#!/usr/bin/env python3

import threading
import time


def main():
    thread = threading.Thread(target=_run_bg_jobs)
    thread.start()

def _run_bg_jobs():
    while True:
        time.sleep(5)

if __name__ == '__main__':
    main()
