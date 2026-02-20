"""SC Cache Warmup – Kodi service addon.
Periodically fetches Stream Cinema API responses and stores them in the
addon's SimpleCache SQLite DB so content loads faster.
"""

import xbmc

from resources.lib.warmup import run_warmup, get_interval_seconds, log


def main():
    monitor = xbmc.Monitor()
    log('Service started')

    while not monitor.abortRequested():
        run_warmup()

        interval = get_interval_seconds()
        log(f'Next warmup in {interval // 60} minutes')

        if monitor.waitForAbort(interval):
            break

    log('Service stopped')


if __name__ == '__main__':
    main()
