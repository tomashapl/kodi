"""Utility functions for StreamBox addon."""
from urllib.parse import urlencode, parse_qs

import xbmc
import xbmcaddon

from resources.lib.constants import TAG, ADDON_ID


def log(msg, level=xbmc.LOGINFO):
    """Log a message with the addon tag."""
    xbmc.log(f'{TAG} {msg}', level)


def get_addon():
    """Return the Addon instance."""
    return xbmcaddon.Addon(ADDON_ID)


def get_setting(setting_id):
    """Read a setting value as string."""
    return get_addon().getSetting(setting_id)


def build_url(base_url, **params):
    """Build a plugin:// URL with query parameters."""
    filtered = {k: v for k, v in params.items() if v is not None}
    return f'{base_url}?{urlencode(filtered)}'


def parse_params(argv2):
    """Parse query string from sys.argv[2] into a dict with string values."""
    params = parse_qs(argv2.lstrip('?'))
    return {k: v[0] for k, v in params.items()}
