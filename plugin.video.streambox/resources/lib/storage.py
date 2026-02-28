"""Local JSON storage for favorites and watch history."""
import json
import os
import time

import xbmcaddon
import xbmcvfs

from resources.lib.constants import ADDON_ID, FAVORITES_FILE, HISTORY_FILE
from resources.lib.utils import log


def _get_data_dir():
    """Return the addon's userdata directory, creating it if needed."""
    addon = xbmcaddon.Addon(ADDON_ID)
    profile = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
    if not xbmcvfs.exists(profile):
        xbmcvfs.mkdirs(profile)
    return profile


def _read_json(filename):
    """Read a JSON file from userdata, returning empty list on error."""
    path = os.path.join(_get_data_dir(), filename)
    if not xbmcvfs.exists(path):
        return []
    try:
        with xbmcvfs.File(path) as f:
            content = f.read()
        return json.loads(content) if content else []
    except Exception as e:
        log(f'Error reading {filename}: {e}')
        return []


def _write_json(filename, data):
    """Write data to a JSON file in userdata."""
    path = os.path.join(_get_data_dir(), filename)
    try:
        with xbmcvfs.File(path, 'w') as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        log(f'Error writing {filename}: {e}')


# --- Favorites ---

def get_favorites():
    """Return list of favorite movie dicts."""
    return _read_json(FAVORITES_FILE)


def is_favorite(movie_id):
    """Check if a movie is in favorites."""
    # Compare as int to handle both string and int IDs
    try:
        mid = int(movie_id)
    except (ValueError, TypeError):
        mid = movie_id
    return any(m['id'] == mid for m in get_favorites())


def toggle_favorite(movie_data):
    """Add or remove a movie from favorites.

    movie_data is a dict with at minimum {id, title, year, poster, rating, genre}.
    Returns True if added, False if removed.
    """
    favorites = get_favorites()
    existing = [i for i, m in enumerate(favorites) if m['id'] == movie_data['id']]
    if existing:
        favorites.pop(existing[0])
        _write_json(FAVORITES_FILE, favorites)
        return False
    movie_data['added_at'] = time.time()
    favorites.insert(0, movie_data)
    _write_json(FAVORITES_FILE, favorites)
    return True


# --- Watch History ---

def get_history():
    """Return list of history entries (most recent first)."""
    return _read_json(HISTORY_FILE)


def add_to_history(movie_data, max_items=100):
    """Add a movie to watch history. Deduplicates by id and caps at max_items."""
    history = get_history()
    history = [m for m in history if m['id'] != movie_data['id']]
    movie_data['watched_at'] = time.time()
    history.insert(0, movie_data)
    history = history[:max_items]
    _write_json(HISTORY_FILE, history)


def clear_history():
    """Remove all watch history."""
    _write_json(HISTORY_FILE, [])
