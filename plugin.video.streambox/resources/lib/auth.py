"""Authentication module – login, token storage, refresh."""
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import xbmcaddon
import xbmcvfs

from resources.lib.constants import (
    ADDON_ID, SETTING_API_URL, SETTING_EMAIL, SETTING_PASSWORD,
    DEFAULT_API_URL, TOKENS_FILE,
)
from resources.lib.utils import log


def _get_data_dir():
    addon = xbmcaddon.Addon(ADDON_ID)
    profile = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
    if not xbmcvfs.exists(profile):
        xbmcvfs.mkdirs(profile)
    return profile


def _tokens_path():
    return os.path.join(_get_data_dir(), TOKENS_FILE)


def load_tokens():
    """Load stored tokens from disk. Returns dict with accessToken/refreshToken or empty dict."""
    path = _tokens_path()
    if not xbmcvfs.exists(path):
        return {}
    try:
        with xbmcvfs.File(path) as f:
            content = f.read()
        return json.loads(content) if content else {}
    except Exception as e:
        log(f'Error loading tokens: {e}')
        return {}


def save_tokens(access_token, refresh_token):
    """Persist tokens to disk."""
    path = _tokens_path()
    data = {'accessToken': access_token, 'refreshToken': refresh_token}
    try:
        with xbmcvfs.File(path, 'w') as f:
            f.write(json.dumps(data))
    except Exception as e:
        log(f'Error saving tokens: {e}')


def clear_tokens():
    """Remove stored tokens (logout)."""
    path = _tokens_path()
    if xbmcvfs.exists(path):
        xbmcvfs.delete(path)


def is_logged_in():
    """Check if we have stored tokens."""
    tokens = load_tokens()
    return bool(tokens.get('accessToken'))


def _get_base_url():
    addon = xbmcaddon.Addon(ADDON_ID)
    return (addon.getSetting(SETTING_API_URL) or DEFAULT_API_URL).rstrip('/')


def _post_json(url, data=None, headers=None):
    """POST JSON and return parsed response."""
    body = json.dumps(data).encode() if data else b''
    hdrs = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if headers:
        hdrs.update(headers)
    req = Request(url, data=body, headers=hdrs, method='POST')
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def login(email=None, password=None):
    """Login with email/password. Returns (success, message) tuple.

    If email/password not provided, reads from addon settings.
    """
    addon = xbmcaddon.Addon(ADDON_ID)
    email = email or addon.getSetting(SETTING_EMAIL)
    password = password or addon.getSetting(SETTING_PASSWORD)

    if not email or not password:
        return False, 'Vyplnte email a heslo v nastaveni'

    base_url = _get_base_url()
    try:
        data = _post_json(f'{base_url}/auth/login', {'email': email, 'password': password})
        save_tokens(data['accessToken'], data['refreshToken'])
        log('Login successful')
        return True, 'Prihlaseni uspesne'
    except HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            msg = err.get('message', str(e))
        except Exception:
            msg = str(e)
        log(f'Login failed: {msg}')
        return False, msg
    except Exception as e:
        log(f'Login error: {e}')
        return False, str(e)


def refresh_tokens():
    """Use refresh token to get new access/refresh tokens. Returns True on success."""
    tokens = load_tokens()
    refresh_token = tokens.get('refreshToken')
    if not refresh_token:
        return False

    base_url = _get_base_url()
    try:
        data = _post_json(
            f'{base_url}/auth/refresh',
            headers={'Authorization': f'Bearer {refresh_token}'},
        )
        save_tokens(data['accessToken'], data['refreshToken'])
        log('Token refresh successful')
        return True
    except Exception as e:
        log(f'Token refresh failed: {e}')
        clear_tokens()
        return False
