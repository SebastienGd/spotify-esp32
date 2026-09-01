from __future__ import annotations

from pydantic import BaseModel

class SpotifyToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
    scope: str | None = None


class SpotifyPlaybackState(BaseModel):
    device: dict
    shuffle_state: bool
    repeat_state: str
    timestamp: int
    context: dict | None = None
    progress_ms: int | None = None
    is_playing: bool
    item: SpotifyTrackItem | None = None
    currently_playing_type: str
    actions: dict


class SpotifyTrackItem(BaseModel):
    album: SpotifyAlbum
    artists: list[SpotifyArtistTrackItem]
    available_markets: list[str] | None = None
    disc_number: int
    duration_ms: int
    explicit: bool
    external_ids: dict | None = None
    external_urls: dict
    href: str
    id: str
    is_local: bool
    name: str
    popularity: int | None = None
    preview_url: str | None = None
    track_number: int
    type: str
    uri: str


class SpotifyAlbum(BaseModel):
    album_type: str
    total_tracks: int
    available_markets: list[str] = []
    external_urls: dict
    href: str
    id: str
    images: list[SpotifyImage]
    name: str
    release_date: str
    release_date_precision: str | None = None
    type: str
    uri: str
    artists: list[SpotifyArtistTrackItem]


class SpotifyArtistTrackItem(BaseModel):
    external_urls: dict
    href: str
    id: str
    name: str
    type: str
    uri: str


class SpotifyImage(BaseModel):
    url: str
    height: int | None = None
    width: int | None = None


class SpotifyArtist(BaseModel):
    id: str
    name: str
    images: list[SpotifyImage] = []
