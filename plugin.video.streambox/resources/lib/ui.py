"""UI helpers: build ListItems, sort methods, notifications."""
import xbmcgui
import xbmcplugin

from resources.lib.storage import is_favorite
from resources.lib.utils import build_url


def create_movie_list_item(movie, base_url, is_playable=False):
    """Create a ListItem for a movie (MovieSummary or MovieDetail).

    Returns (url, list_item, is_folder) tuple for addDirectoryItem.
    """
    li = xbmcgui.ListItem(label=movie.title, offscreen=True)
    li.setInfo('video', {'title': movie.title, 'mediatype': 'movie'})

    # Context menu
    fav_label = 'Odebrat z oblibenych' if is_favorite(movie.id) else 'Pridat do oblibenych'
    li.addContextMenuItems([(
        fav_label,
        f'RunPlugin({build_url(base_url, action="toggle_favorite", movie_id=movie.id)})',
    )])

    if is_playable:
        url = build_url(base_url, action='play', movie_id=movie.id)
        li.setProperty('IsPlayable', 'true')
        return url, li, False
    else:
        url = build_url(base_url, action='movie_detail', movie_id=movie.id)
        return url, li, True


def add_movie_sort_methods(handle):
    """Register sort methods for movie listings."""
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)


def create_directory_item(label, base_url, icon=None, **params):
    """Create a folder ListItem for navigation (categories, menus)."""
    li = xbmcgui.ListItem(label=label, offscreen=True)
    if icon:
        li.setArt({'icon': icon, 'thumb': icon})
    url = build_url(base_url, **params)
    return url, li, True


def add_next_page_item(handle, base_url, current_page, total_pages, **extra_params):
    """Add a 'Next page >>' item if there are more pages."""
    if current_page < total_pages:
        li = xbmcgui.ListItem(
            label=f'Dalsi strana ({current_page + 1}/{total_pages}) >>',
            offscreen=True,
        )
        url = build_url(base_url, page=current_page + 1, **extra_params)
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=True)


def notify(title, message, icon=xbmcgui.NOTIFICATION_INFO, time_ms=3000):
    """Show a Kodi notification."""
    xbmcgui.Dialog().notification(title, message, icon, time_ms)
