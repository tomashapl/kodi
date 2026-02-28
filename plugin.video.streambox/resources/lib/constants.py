"""Shared constants for StreamBox addon."""

ADDON_ID = 'plugin.video.streambox'
TAG = '[StreamBox]'

# Settings IDs (must match resources/settings.xml)
SETTING_API_URL = 'api.base_url'
SETTING_EMAIL = 'auth.email'
SETTING_PASSWORD = 'auth.password'
SETTING_LANGUAGE = 'general.language'
SETTING_ITEMS_PER_PAGE = 'general.items_per_page'
SETTING_QUALITY = 'playback.quality'

# Default values
DEFAULT_API_URL = 'https://streambox-api.onrender.com'
DEFAULT_ITEMS_PER_PAGE = 20
DEFAULT_LANGUAGE = 'cs'
DEFAULT_QUALITY = 'auto'

# Content types for xbmcplugin.setContent()
CONTENT_MOVIES = 'movies'

# Local storage filenames
FAVORITES_FILE = 'favorites.json'
HISTORY_FILE = 'history.json'
TOKENS_FILE = 'tokens.json'

# Router actions
ACTION_HUB = 'hub'
ACTION_MOVIES_MENU = 'movies_menu'
ACTION_SERIES_MENU = 'series_menu'
ACTION_LOGIN = 'login'
ACTION_LOGOUT = 'logout'
ACTION_CATEGORIES = 'categories'
ACTION_MOVIES = 'movies'
ACTION_MOVIE_DETAIL = 'movie_detail'
ACTION_STREAMS = 'streams'
ACTION_PLAY = 'play'
ACTION_SEARCH = 'search'
ACTION_SEARCH_RESULTS = 'search_results'
ACTION_FAVORITES = 'favorites'
ACTION_TOGGLE_FAVORITE = 'toggle_favorite'
ACTION_HISTORY = 'history'
ACTION_CLEAR_HISTORY = 'clear_history'
ACTION_RECOMMENDATIONS = 'recommendations'
ACTION_FILTER = 'filter'
ACTION_FILTER_SELECT = 'filter_select'
