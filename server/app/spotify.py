import base64
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar
from urllib.parse import urlencode

import fastapi
import httpx
from omegaconf import DictConfig

from app.constants import (
    HttpTimeout,
    PollDelay,
    SpotifyUrl,
)
from domain.spotify import SpotifyAlbum, SpotifyArtist, SpotifyArtistTrackItem, SpotifyPlaybackState, SpotifyToken

T = TypeVar("T")


class Spotify:
    playback_state: SpotifyPlaybackState | None = None
    last_fetch_timestamp: float | None = None

    def __init__(self, conf: DictConfig):
        self._client_id = conf.spotify.client_id
        self._api_key = conf.spotify.api_key
        self.conf = conf

    def build_auth_url(self) -> str:
        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "redirect_uri": self.conf.callback_url,
            "scope": " ".join(self.conf.spotify.scopes),
            "show_dialog": "true",
        }
        return f"{SpotifyUrl.AUTH.value}?{urlencode(params)}"

    async def fetch_spotify_token(self, code: str) -> SpotifyToken:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                SpotifyUrl.TOKEN.value,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.conf.callback_url,
                    "client_id": self._client_id,
                    "client_secret": self._api_key,
                },
                timeout=HttpTimeout.REQUEST.value,
            )
            r.raise_for_status()

        return SpotifyToken(**r.json())

    async def _refresh_access_token(self) -> SpotifyToken:
        refresh_token = self.conf.spotify.refresh_token
        if not refresh_token:
            raise RuntimeError("SPOTIFY_REFRESH_TOKEN is not configured")

        credentials = f"{self._client_id}:{self._api_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                SpotifyUrl.TOKEN.value,
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )

            response.raise_for_status()

        data = response.json()
        return SpotifyToken(**data)

    async def _refresh_and_store_access_token(self) -> None:
        refreshed_token = await self._refresh_access_token()
        self.conf.spotify.access_token = refreshed_token.access_token
        if refreshed_token.refresh_token:
            self.conf.spotify.refresh_token = refreshed_token.refresh_token

    async def fetch_spotify_playback_state(self) -> SpotifyPlaybackState | None:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                SpotifyUrl.PLAYBACK.value,
                headers={"Authorization": f"Bearer {self.conf.spotify.access_token}"},
                timeout=HttpTimeout.REQUEST.value,
            )

            if r.status_code == fastapi.status.HTTP_401_UNAUTHORIZED:
                await self._refresh_and_store_access_token()
                return await self.fetch_spotify_playback_state()

            r.raise_for_status()

            if r.status_code == fastapi.status.HTTP_204_NO_CONTENT:
                return None

        return SpotifyPlaybackState(**r.json())

    async def try_fetch_spotify_playback_state(self) -> SpotifyPlaybackState | None:
        current_time = time.monotonic()

        if self.last_fetch_timestamp is not None and current_time - self.last_fetch_timestamp < PollDelay.WS.value:
            # Continue rendering the cached state between Spotify polls. Returning
            # None here makes the orchestrator sleep for the polling interval.
            return self.playback_state

        playback_state = await self.safe_fetch(self.fetch_spotify_playback_state)
        self.last_fetch_timestamp = time.monotonic()

        return playback_state

    async def fetch_spotify_artist(self, artist_id: str) -> SpotifyArtist:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{SpotifyUrl.ARTIST.value}{artist_id}",
                headers={"Authorization": f"Bearer {self.conf.spotify.access_token}"},
                timeout=HttpTimeout.REQUEST.value,
            )
            r.raise_for_status()

        return SpotifyArtist(**r.json())

    async def fetch_artist_images(self, artist_id: str) -> list[str]:
        artist = await self.fetch_spotify_artist(artist_id)
        return [image.url for image in artist.images]

    async def fetch_track_image(self, track_id: str) -> str | None:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{SpotifyUrl.TRACK.value}{track_id}",
                headers={"Authorization": f"Bearer {self.conf.spotify.access_token}"},
                timeout=HttpTimeout.REQUEST.value,
            )
            r.raise_for_status()

        album = SpotifyAlbum(**r.json()["album"])
        return album.images[0].url if album.images else None

    async def _send_player_command(self, method: str, url: str) -> None:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method,
                url,
                headers={"Authorization": f"Bearer {self.conf.spotify.access_token}"},
            )

            if response.status_code == fastapi.status.HTTP_401_UNAUTHORIZED:
                await self._refresh_and_store_access_token()
                response = await client.request(
                    method,
                    url,
                    headers={"Authorization": f"Bearer {self.conf.spotify.access_token}"},
                )

            response.raise_for_status()

    async def next_track(self) -> None:
        await self._send_player_command("POST", SpotifyUrl.NEXT_TRACK.value)

    async def previous_track(self) -> None:
        await self._send_player_command("POST", SpotifyUrl.PREVIOUS_TRACK.value)

    async def pause(self) -> None:
        await self._send_player_command("PUT", SpotifyUrl.PAUSE.value)

    async def play(self) -> None:
        await self._send_player_command("PUT", SpotifyUrl.PLAY.value)

    @property
    def artist(self) -> SpotifyArtistTrackItem | None:
        if self.playback_state and self.playback_state.item:
            # we always take the first artist since the display is big enough to show only for one artist at a time
            return self.playback_state.item.artists[0]
        return None

    def is_same_artist(self, playback_state: SpotifyPlaybackState) -> bool:
        if not self.playback_state or not self.playback_state.item:
            return False
        return playback_state.item.artists[0].id == self.playback_state.item.artists[0].id

    def is_same_song(self, playback_state: SpotifyPlaybackState) -> bool:
        if not self.playback_state or not self.playback_state.item:
            return False
        return playback_state.item.id == self.playback_state.item.id

    def update_playback_state(self, playback_state: SpotifyPlaybackState) -> None:
        self.playback_state = playback_state

    def interpolate_progress_ms(self) -> int:
        if not self.playback_state or not self.playback_state.item or not self.last_fetch_timestamp:
            return 0

        if not self.playback_state.is_playing:
            return self.playback_state.progress_ms or 0

        # Calculate elapsed time since last fetch
        elapsed_ms = int((time.monotonic() - self.last_fetch_timestamp) * 1000)

        # Calculate interpolated progress
        interpolated_progress = (self.playback_state.progress_ms or 0) + elapsed_ms

        # Ensure it doesn't exceed duration
        duration_ms = self.playback_state.item.duration_ms or 1

        return min(interpolated_progress, duration_ms)

    @staticmethod
    async def safe_fetch(fn: Callable[..., Awaitable[T]], *args, **kwargs) -> T | None:
        try:
            return await fn(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"An error occurred: {e}")

        return None
