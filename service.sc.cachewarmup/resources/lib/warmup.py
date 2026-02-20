"""SC Cache Warmup – shared warmup logic."""

import json
import os
import sqlite3
import time
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse, parse_qs

import xbmc
import xbmcaddon

# --- Config (hardcoded for LibreELEC) ---
SC_ADDON_DIR = '/storage/.kodi/addons/plugin.video.stream-cinema'
SC_SETTINGS_FILE = '/storage/.kodi/userdata/addon_data/plugin.video.stream-cinema/settings.xml'
CACHE_DB = '/storage/.kodi/userdata/addon_data/plugin.video.stream-cinema/simplecache.db'
BASE_URL = 'https://stream-cinema.online/kodi'
API_VERSION = '2.0'

ENDPOINTS = [
    '/',
    '/FMovies',
    '/FMovies/popular',
    '/FMovies/trending',
    '/FMovies/latest',
    '/FMovies/latestd',
    '/FMovies/lastWatched',
    '/FMovies/watching',
    '/FTVShows',
    '/FTVShows/popular',
    '/FSeries',
    '/Recommended',
    '/Recommended?type=0',
    '/Filter/facet',
]

INTERVAL_MAP = {
    '30 min': 1800,
    '1 hour': 3600,
    '2 hours': 7200,
    '4 hours': 14400,
}
TAG = '[SC Cache Warmup]'


def log(msg, level=xbmc.LOGINFO):
    xbmc.log(f'{TAG} {msg}', level)


def get_interval_seconds():
    """Read the warmup interval from addon settings."""
    try:
        addon = xbmcaddon.Addon()
        value = addon.getSetting('warmup.interval')
        return INTERVAL_MAP.get(value, 7200)
    except Exception:
        return 7200  # default 2 hours


def get_addon_version():
    tree = ET.parse(os.path.join(SC_ADDON_DIR, 'addon.xml'))
    return tree.getroot().attrib['version']


def get_sc_settings():
    settings = {}
    try:
        tree = ET.parse(SC_SETTINGS_FILE)
        for s in tree.findall('.//setting'):
            sid = s.get('id')
            val = s.text if s.text else s.get('value', '')
            settings[sid] = val
    except Exception as e:
        log(f'Error reading SC settings: {e}', xbmc.LOGWARNING)
    return settings


RATING_MAP = {
    '0': 0,
    '1': 6,
    '2': 12,
    '3': 15,
    '4': 18,
}


def _is_parental_control_active(settings):
    """Replicate SC plugin's parental_control_is_active() logic."""
    import datetime
    if settings.get('parental.control.enabled') != 'true':
        return False
    now = datetime.datetime.now()
    try:
        hour_start = int(settings.get('parental.control.start', '0'))
        hour_end = int(settings.get('parental.control.end', '0'))
    except (ValueError, TypeError):
        return False
    return hour_start <= now.hour <= hour_end


def build_params(settings):
    """Build params matching SC plugin's Sc.default_params() exactly."""
    params = {}

    params['ver'] = API_VERSION
    params['uid'] = settings.get('system.uuid', '')
    params['skin'] = 'skin.nimbus'
    params['lang'] = 'cs'

    parental_control = _is_parental_control_active(settings)

    # dub: stream.dubed OR (parental_control AND parental.control.dubed)
    if settings.get('stream.dubed') == 'true' or \
       (parental_control and settings.get('parental.control.dubed') == 'true'):
        params['dub'] = 1

    # dub+tit: stream.dubed.titles when parental control is OFF
    if not parental_control and settings.get('stream.dubed.titles') == 'true':
        params['dub'] = 1
        params['tit'] = 1

    # m: only when parental control is active
    if parental_control:
        rating = settings.get('parental.control.rating', '0')
        params['m'] = RATING_MAP.get(rating, 0)

    if settings.get('plugin.show.genre') == 'true':
        params['gen'] = 1

    params['HDR'] = 0 if settings.get('stream.exclude.hdr') == 'true' else 1
    params['DV'] = 0 if settings.get('stream.exclude.dolbyvision') == 'true' else 1

    if settings.get('plugin.show.old.menu') == 'true':
        params['old'] = 1

    # Convert to sorted list of tuples (same as SC's Sc.prepare())
    return sorted(params.items(), key=lambda x: x[0])


def fetch_endpoint(path, params, headers):
    url = BASE_URL + path + '?' + urlencode(params)
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        log(f'Fetch error for {path}: {e}', xbmc.LOGWARNING)
        return None


def store_in_cache(cache_key, data, ttl):
    expires = int(time.time()) + ttl
    try:
        conn = sqlite3.connect(CACHE_DB, timeout=30)
        conn.execute(
            'CREATE TABLE IF NOT EXISTS simplecache('
            'id TEXT UNIQUE, expires INTEGER, data TEXT, checksum INTEGER)')
        conn.execute(
            'INSERT OR REPLACE INTO simplecache(id, expires, data, checksum) VALUES (?, ?, ?, ?)',
            (cache_key, expires, repr(data), 0))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        log(f'DB error: {e}', xbmc.LOGWARNING)
        return False


def run_warmup():
    """Execute one warmup cycle across all endpoints.

    Returns the number of successfully cached endpoints.
    """
    log('Starting warmup cycle')
    try:
        addon_ver = get_addon_version()
    except Exception as e:
        log(f'Cannot read SC addon version: {e}', xbmc.LOGERROR)
        return 0

    settings = get_sc_settings()
    params = build_params(settings)
    headers = {
        'User-Agent': 'Kodi/21.3 (Linux; LibreELEC)',
        'X-Uuid': settings.get('system.uuid', ''),
        'X-AUTH-TOKEN': settings.get('system.auth_token', ''),
    }

    interval = get_interval_seconds()
    cached = 0
    for ep in ENDPOINTS:
        # Parse query params from endpoint URL (e.g. /Recommended?type=0)
        # and merge them into params, matching SC's Sc.prepare() behavior
        ep_parsed = urlparse(ep)
        ep_path = ep_parsed.path
        ep_query = parse_qs(ep_parsed.query)
        # Merge: start with default params dict, add endpoint-specific ones
        merged = dict(params)
        for k, v in ep_query.items():
            merged[k] = v[0] if len(v) == 1 else v
        ep_params = sorted(merged.items(), key=lambda x: x[0])

        url = BASE_URL + ep_path
        cache_key = f'{addon_ver}{url}{ep_params}'
        data = fetch_endpoint(ep_path, ep_params, headers)
        if data and store_in_cache(cache_key, data, interval):
            if isinstance(data, dict):
                items = len(data.get('menu', []))
                log(f'{ep} -> OK ({items} items)')
            else:
                log(f'{ep} -> OK ({len(data)} entries)')
            cached += 1
        elif data is None:
            pass  # error already logged
        else:
            log(f'{ep} -> DB write failed', xbmc.LOGWARNING)

    log(f'Warmup done: {cached}/{len(ENDPOINTS)} endpoints cached')
    return cached
