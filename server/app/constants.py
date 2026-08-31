from enum import Enum


class SpotifyUrl(str, Enum):
    AUTH = "https://accounts.spotify.com/authorize"
    TOKEN = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"
    PLAYBACK = f"{API_BASE}/me/player"
    ARTIST = f"{API_BASE}/artists/"
    TRACK = f"{API_BASE}/tracks/"
    NEXT_TRACK = f"{API_BASE}/me/player/next"
    PREVIOUS_TRACK = f"{API_BASE}/me/player/previous"
    PAUSE = f"{API_BASE}/me/player/pause"
    PLAY = f"{API_BASE}/me/player/play"


class HttpTimeout(int, Enum):
    REQUEST = 5


class PollDelay(int, Enum):
    WS = 5


class FacePadding(float, Enum):
    TOP = 0.3
    BOTTOM = 0.1
    LEFT = 0.2
    RIGHT = 0.2
