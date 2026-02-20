"""SC Cache Warmup – manual run entry point."""

import xbmcgui

from resources.lib.warmup import run_warmup, ENDPOINTS

cached = run_warmup()
total = len(ENDPOINTS)

if cached > 0:
    xbmcgui.Dialog().notification(
        'SC Cache Warmup',
        f'Done: {cached}/{total} endpoints cached',
        xbmcgui.NOTIFICATION_INFO,
        3000,
    )
else:
    xbmcgui.Dialog().notification(
        'SC Cache Warmup',
        'Warmup failed – check log',
        xbmcgui.NOTIFICATION_ERROR,
        5000,
    )
