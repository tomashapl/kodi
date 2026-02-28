"""StreamBox API client with JWT authentication."""
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError

import xbmcaddon

from resources.lib.constants import (
    ADDON_ID, SETTING_API_URL, SETTING_ITEMS_PER_PAGE,
    DEFAULT_API_URL, DEFAULT_ITEMS_PER_PAGE,
)
from resources.lib.auth import load_tokens, refresh_tokens, login
from resources.lib.models import MovieSummary, MovieDetail, StreamItem
from resources.lib.utils import log


class AuthError(Exception):
    """Raised when authentication fails and cannot be recovered."""
    pass


class ApiClient:
    """HTTP client for the StreamBox REST API."""

    def __init__(self):
        addon = xbmcaddon.Addon(ADDON_ID)
        self._base_url = (addon.getSetting(SETTING_API_URL) or DEFAULT_API_URL).rstrip('/')
        self._per_page = int(addon.getSetting(SETTING_ITEMS_PER_PAGE) or DEFAULT_ITEMS_PER_PAGE)

    def _get_access_token(self):
        tokens = load_tokens()
        return tokens.get('accessToken', '')

    def _request(self, method, path, params=None, body=None, retry=True):
        """Make an authenticated request. Auto-refreshes token on 401."""
        url = self._base_url + path
        if params:
            url += '?' + urlencode(params)

        log(f'API {method} {url}')

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._get_access_token()}',
        }

        data = json.dumps(body).encode() if body else None
        req = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            if e.code == 401 and retry:
                log('Got 401, attempting token refresh')
                if refresh_tokens():
                    return self._request(method, path, params, body, retry=False)
                # Refresh failed, try full re-login
                log('Refresh failed, attempting re-login')
                success, _ = login()
                if success:
                    return self._request(method, path, params, body, retry=False)
                raise AuthError('Prihlaseni vyprselo, prihlaste se znovu')
            raise

    def _get(self, path, params=None):
        return self._request('GET', path, params=params)

    def _post(self, path, params=None, body=None):
        return self._request('POST', path, params=params, body=body)

    # --- Movie endpoints ---

    def search_movies(self, query=None, page=1):
        """POST /movie/search -> paginated MovieGetResponse"""
        params = {'page': page, 'size': self._per_page}
        if query:
            params['query'] = query
        data = self._post('/movie/search', params=params)
        movies = [MovieSummary(id=m['id'], title=m['title']) for m in data['items']]
        return movies, data['total'], data['page'], data['pageCount']

    def get_movie(self, movie_id):
        """GET /movie/{id} -> MovieDetail"""
        data = self._get(f'/movie/{movie_id}')
        return MovieDetail(id=data['id'], title=data['title'])

    def get_movies_by_category(self, category, page=1):
        """POST /movie/category/{category} -> paginated MovieGetResponse"""
        params = {'page': page, 'size': self._per_page}
        data = self._post(f'/movie/category/{category}', params=params)
        movies = [MovieSummary(id=m['id'], title=m['title']) for m in data['items']]
        return movies, data['total'], data['page'], data['pageCount']

    def get_movie_streams(self, movie_id):
        """POST /movie/{id}/stream -> plain list of available streams.

        Response: [{id, video: {codec, quality}, audio: {codec, channels, language}}, ...]
        """
        data = self._post(f'/movie/{movie_id}/stream')
        return [
            StreamItem(
                id=str(s['id']),
                video_codec=(s.get('video') or {}).get('codec') or '',
                video_quality=(s.get('video') or {}).get('quality') or '',
                audio_codec=(s.get('audio') or {}).get('codec') or '',
                audio_channels=(s.get('audio') or {}).get('channels') or 0,
                audio_language=(s.get('audio') or {}).get('language') or '',
            )
            for s in data
        ]

    def get_stream_play(self, stream_id):
        """GET /stream/{id}/play -> StreamPlayResponse {link: str|null}"""
        data = self._get(f'/stream/{stream_id}/play')
        return data.get('link')

    # --- User endpoints ---

    def get_me(self):
        """GET /user/me -> user info dict"""
        return self._get('/user/me')
