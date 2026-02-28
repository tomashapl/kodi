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
class StreamItem:
    """Available stream from /movie/{id}/stream."""
    id: str
    video_codec: str = ''
    video_quality: str = ''
    audio_codec: str = ''
    audio_channels: int = 0
    audio_language: str = ''

    @property
    def label(self):
        """Human-readable label for stream selection dialog.

        Example: '1080p | H264 | AAC 2ch | cs'
        """
        parts = []
        if self.video_quality:
            parts.append(self.video_quality)
        if self.video_codec:
            parts.append(self.video_codec)
        if self.audio_codec:
            audio = self.audio_codec
            if self.audio_channels:
                audio += f' {self.audio_channels}ch'
            parts.append(audio)
        if self.audio_language:
            parts.append(self.audio_language)
        return ' | '.join(parts) if parts else self.id


@dataclass
class UserInfo:
    """Logged-in user info from /user/me."""
    id: str
    first_name: str
    last_name: str
    email: str
