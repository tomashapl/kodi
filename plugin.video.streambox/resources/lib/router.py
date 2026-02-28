"""URL routing for StreamBox addon."""
import xbmc
import xbmcgui
import xbmcplugin

from resources.lib.constants import (
    ACTION_HUB, ACTION_MOVIES_MENU, ACTION_SERIES_MENU,
    ACTION_LOGIN, ACTION_LOGOUT,
    ACTION_CATEGORIES, ACTION_MOVIES, ACTION_MOVIE_DETAIL,
    ACTION_SEARCH, ACTION_SEARCH_RESULTS, ACTION_FAVORITES,
    ACTION_TOGGLE_FAVORITE, ACTION_HISTORY, ACTION_CLEAR_HISTORY,
    ACTION_RECOMMENDATIONS, ACTION_FILTER, ACTION_FILTER_SELECT,
    CONTENT_MOVIES,
)
from resources.lib.api_client import ApiClient, AuthError
from resources.lib.auth import is_logged_in, login, clear_tokens
from resources.lib.models import MovieSummary
from resources.lib.storage import (
    get_favorites, toggle_favorite, get_history, add_to_history, clear_history,
)
from resources.lib.ui import (
    create_movie_list_item, create_directory_item, add_movie_sort_methods,
    add_next_page_item, notify,
)
from resources.lib.utils import build_url, parse_params, log


class Router:
    """Dispatches plugin:// URLs to handler methods."""

    def __init__(self, argv):
        self._base_url = argv[0]
        self._handle = int(argv[1])
        self._params = parse_params(argv[2]) if len(argv) > 2 else {}
        self._api = ApiClient()

    def dispatch(self):
        """Route to the appropriate handler based on 'action' parameter."""
        action = self._params.get('action', ACTION_HUB)

        handlers = {
            ACTION_HUB: self._hub,
            ACTION_LOGIN: self._login,
            ACTION_LOGOUT: self._logout,
            ACTION_MOVIES_MENU: self._movies_menu,
            ACTION_SERIES_MENU: self._series_menu,
            ACTION_CATEGORIES: self._categories,
            ACTION_MOVIES: self._movies,
            ACTION_MOVIE_DETAIL: self._movie_detail,
            ACTION_SEARCH: self._search,
            ACTION_SEARCH_RESULTS: self._search_results,
            ACTION_FAVORITES: self._favorites,
            ACTION_TOGGLE_FAVORITE: self._toggle_favorite,
            ACTION_HISTORY: self._history,
            ACTION_CLEAR_HISTORY: self._clear_history,
            ACTION_RECOMMENDATIONS: self._recommendations,
            ACTION_FILTER: self._filter_menu,
            ACTION_FILTER_SELECT: self._filter_select,
        }

        handler = handlers.get(action)
        if handler:
            try:
                handler()
            except AuthError as e:
                notify('StreamBox', str(e), xbmcgui.NOTIFICATION_ERROR)
                xbmcplugin.endOfDirectory(self._handle, succeeded=False)
        else:
            log(f'Unknown action: {action}', xbmc.LOGWARNING)

    # ---- Hub ----

    def _hub(self):
        items = []

        if is_logged_in():
            items.append(create_directory_item('Filmy', self._base_url,
                                               action=ACTION_MOVIES_MENU))
            items.append(create_directory_item('Serialy', self._base_url,
                                               action=ACTION_SERIES_MENU))
            items.append(create_directory_item('Hledat', self._base_url,
                                               action=ACTION_SEARCH))
            items.append(create_directory_item('Odhlasit se', self._base_url,
                                               action=ACTION_LOGOUT))
        else:
            items.append(create_directory_item('Prihlasit se', self._base_url,
                                               action=ACTION_LOGIN))

        for url, li, is_folder in items:
            xbmcplugin.addDirectoryItem(self._handle, url, li, isFolder=is_folder)
        xbmcplugin.endOfDirectory(self._handle)

    # ---- Auth ----

    def _login(self):
        success, msg = login()
        if success:
            notify('StreamBox', msg)
        else:
            notify('StreamBox', msg, xbmcgui.NOTIFICATION_ERROR)
        xbmc.executebuiltin('Container.Refresh')

    def _logout(self):
        clear_tokens()
        notify('StreamBox', 'Odhlaseno')
        xbmc.executebuiltin('Container.Refresh')

    # ---- Menus ----

    def _movies_menu(self):
        items = [
            create_directory_item('Vsechny filmy', self._base_url,
                                  action=ACTION_MOVIES),
            create_directory_item('Oblibene', self._base_url,
                                  action=ACTION_FAVORITES),
            create_directory_item('Historie', self._base_url,
                                  action=ACTION_HISTORY),
        ]
        for url, li, is_folder in items:
            xbmcplugin.addDirectoryItem(self._handle, url, li, isFolder=is_folder)
        xbmcplugin.endOfDirectory(self._handle)

    def _series_menu(self):
        notify('StreamBox', 'Serialy budou brzy k dispozici')
        xbmcplugin.endOfDirectory(self._handle, succeeded=False)

    # ---- Movies ----

    def _movies(self):
        page = int(self._params.get('page', 1))
        movies, total, current_page, total_pages = self._api.search_movies(page=page)

        xbmcplugin.setContent(self._handle, CONTENT_MOVIES)
        add_movie_sort_methods(self._handle)

        for movie in movies:
            url, li, is_folder = create_movie_list_item(movie, self._base_url)
            xbmcplugin.addDirectoryItem(self._handle, url, li, isFolder=is_folder)

        add_next_page_item(self._handle, self._base_url, current_page, total_pages,
                           action=ACTION_MOVIES)
        xbmcplugin.endOfDirectory(self._handle)

    def _categories(self):
        # TODO: implement when backend has categories endpoint
        notify('StreamBox', 'Kategorie zatim nejsou k dispozici')
        xbmcplugin.endOfDirectory(self._handle, succeeded=False)

    def _movie_detail(self):
        """Fetch streams, show select dialog, and play chosen stream."""
        movie_id = self._params['movie_id']
        streams = self._api.get_movie_streams(movie_id)

        if not streams:
            notify('StreamBox', 'Zadny stream nenalezen',
                   xbmcgui.NOTIFICATION_ERROR)
            return

        # Single stream – play directly, no dialog
        if len(streams) == 1:
            selected = 0
        else:
            labels = [s.title for s in streams]
            selected = xbmcgui.Dialog().select('Vybrat stream', labels)

        if selected < 0:
            return

        stream = streams[selected]
        link = self._api.get_stream_play(stream.id)

        if not link:
            notify('StreamBox', 'Stream neni dostupny',
                   xbmcgui.NOTIFICATION_ERROR)
            return

        # Record in history
        try:
            movie = self._api.get_movie(movie_id)
            add_to_history({'id': movie.id, 'title': movie.title})
        except Exception:
            pass

        # Play
        li = xbmcgui.ListItem(path=link)
        xbmc.Player().play(link, li)

    # ---- Search ----

    def _search(self):
        kb = xbmc.Keyboard('', 'Hledat')
        kb.doModal()
        if kb.isConfirmed() and kb.getText():
            self._params['query'] = kb.getText()
            self._params['page'] = '1'
            self._search_results()
        else:
            xbmcplugin.endOfDirectory(self._handle, succeeded=False)

    def _search_results(self):
        query = self._params['query']
        page = int(self._params.get('page', 1))

        # Use the general search endpoint
        movies, total, current_page, total_pages = self._api.search_movies(page=page)

        xbmcplugin.setContent(self._handle, CONTENT_MOVIES)
        xbmcplugin.setPluginCategory(self._handle, f'Hledani: {query}')
        add_movie_sort_methods(self._handle)

        for movie in movies:
            url, li, is_folder = create_movie_list_item(movie, self._base_url)
            xbmcplugin.addDirectoryItem(self._handle, url, li, isFolder=is_folder)

        add_next_page_item(self._handle, self._base_url, current_page, total_pages,
                           action=ACTION_SEARCH_RESULTS, query=query)
        xbmcplugin.endOfDirectory(self._handle)

    # ---- Favorites ----

    def _favorites(self):
        favorites = get_favorites()
        xbmcplugin.setContent(self._handle, CONTENT_MOVIES)
        add_movie_sort_methods(self._handle)

        for fav in favorites:
            movie = MovieSummary(id=fav['id'], title=fav['title'])
            url, li, is_folder = create_movie_list_item(movie, self._base_url)
            xbmcplugin.addDirectoryItem(self._handle, url, li, isFolder=is_folder)

        xbmcplugin.endOfDirectory(self._handle)

    def _toggle_favorite(self):
        movie_id = self._params['movie_id']
        movie = self._api.get_movie(movie_id)
        movie_data = {'id': movie.id, 'title': movie.title}
        added = toggle_favorite(movie_data)
        msg = 'Pridano do oblibenych' if added else 'Odebrano z oblibenych'
        notify('StreamBox', msg)
        xbmc.executebuiltin('Container.Refresh')

    # ---- History ----

    def _history(self):
        history = get_history()
        xbmcplugin.setContent(self._handle, CONTENT_MOVIES)

        for entry in history:
            movie = MovieSummary(id=entry['id'], title=entry['title'])
            url, li, is_folder = create_movie_list_item(movie, self._base_url)
            xbmcplugin.addDirectoryItem(self._handle, url, li, isFolder=is_folder)

        if history:
            url, li, _ = create_directory_item(
                '[Vymazat historii]', self._base_url,
                action=ACTION_CLEAR_HISTORY)
            xbmcplugin.addDirectoryItem(self._handle, url, li, isFolder=False)

        xbmcplugin.endOfDirectory(self._handle)

    def _clear_history(self):
        clear_history()
        notify('StreamBox', 'Historie vymazana')
        xbmc.executebuiltin('Container.Refresh')

    # ---- Recommendations (TODO) ----

    def _recommendations(self):
        notify('StreamBox', 'Doporuceni zatim nejsou k dispozici')
        xbmcplugin.endOfDirectory(self._handle, succeeded=False)

    # ---- Filter (TODO) ----

    def _filter_menu(self):
        notify('StreamBox', 'Filtr zatim neni k dispozici')
        xbmcplugin.endOfDirectory(self._handle, succeeded=False)

    def _filter_select(self):
        xbmcplugin.endOfDirectory(self._handle, succeeded=False)
