"""Data models for StreamBox addon."""
from dataclasses import dataclass


@dataclass
class MovieSummary:
    """Movie from list endpoints (search, category)."""
    id: int
    title: str


@dataclass
class MovieDetail:
    """Full movie detail."""
    id: int
    title: str


@dataclass
class UserInfo:
    """Logged-in user info from /user/me."""
    id: str
    first_name: str
    last_name: str
    email: str
