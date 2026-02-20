#!/usr/bin/env python3
"""Stream Cinema cache pre-warming script.
Fetches API responses and stores them in the addon's SimpleCache SQLite DB."""

import json
import os
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.parse import urlencode

# --- Config ---
ADDON_DIR = '/storage/.kodi/addons/plugin.video.stream-cinema'
SETTINGS_FILE = '/storage/.kodi/userdata/addon_data/plugin.video.stream-cinema/settings.xml'
CACHE_DB = '/storage/.kodi/userdata/addon_data/plugin.video.stream-cinema/simplecache.db'
BASE_URL = 'https://stream-cinema.online/kodi'
API_VERSION = '2.0'
CACHE_TTL = 7200  # 2 hours

ENDPOINTS = [
    '/',
    '/FMovies',
    '/FMovies/popular',
    '/FTVShows',
    '/FTVShows/popular',
    '/FSeries',
    '/Recommended',
]

def get_addon_version():
    tree = ET.parse(os.path.join(ADDON_DIR, 'addon.xml'))
    return tree.getroot().attrib['version']

def get_settings():
    settings = {}
    try:
        tree = ET.parse(SETTINGS_FILE)
        for s in tree.findall('.//setting'):
            sid = s.get('id')
            val = s.text if s.text else s.get('value', '')
            settings[sid] = val
    except Exception as e:
        print(f'  Error reading settings: {e}')
    return settings

def build_params(settings):
    params = []
    params.append(('DV', 0 if settings.get('stream.exclude.dolbyvision') == 'true' else 1))
    params.append(('HDR', 0 if settings.get('stream.exclude.hdr') == 'true' else 1))
    if settings.get('stream.dubed') == 'true':
        params.append(('dub', 1))
    if settings.get('plugin.show.genre') == 'true':
        params.append(('gen', 1))
    params.append(('lang', 'cs'))
    params.append(('m', 15))
    if settings.get('plugin.show.old.menu') == 'true':
        params.append(('old', 1))
    params.append(('skin', 'skin.nimbus'))
    params.append(('uid', settings.get('system.uuid', '')))
    params.append(('ver', API_VERSION))
    return sorted(params, key=lambda x: x[0])

def fetch_endpoint(path, params, headers):
    url = BASE_URL + path + '?' + urlencode(params)
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f'Error ({e})')
        return None

def store_in_cache(cache_key, data):
    expires = int(time.time()) + CACHE_TTL
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
        print(f'DB error ({e})')
        return False

def main():
    print(f'[{time.strftime("%H:%M:%S")}] SC Cache Warmup')
    addon_ver = get_addon_version()
    settings = get_settings()
    params = build_params(settings)
    headers = {
        'User-Agent': 'Kodi/21.3 (Linux; LibreELEC)',
        'X-Uuid': settings.get('system.uuid', ''),
        'X-AUTH-TOKEN': settings.get('system.auth_token', ''),
    }
    cached = 0
    for ep in ENDPOINTS:
        url = BASE_URL + ep
        cache_key = f'{addon_ver}{url}{params}'
        print(f'  {ep}... ', end='', flush=True)
        data = fetch_endpoint(ep, params, headers)
        if data and store_in_cache(cache_key, data):
            print(f'OK ({len(data.get("menu", []))} items)')
            cached += 1
        elif data is None:
            pass  # error already printed
        else:
            print('DB fail')
    print(f'[{time.strftime("%H:%M:%S")}] Done: {cached}/{len(ENDPOINTS)}')

if __name__ == '__main__':
    main()
