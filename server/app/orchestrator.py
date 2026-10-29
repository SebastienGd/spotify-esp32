import asyncio
from logging import getLogger
from pathlib import Path

from fastapi import WebSocket
from omegaconf import DictConfig

from app.constants import PollDelay, SpotifyEvent
from app.display_drawer import DisplayDrawer
from app.artwork.factory import create_artwork_provider, create_pixel_art
from app.spotify import Spotify
from domain.spotify import SpotifyPlaybackState


logger = getLogger(__name__)


class Orchestrator:
    def __init__(self, conf: DictConfig):
        self.conf = conf
        self._spotify = Spotify(conf)
        self._pixel_art = create_pixel_art(conf)
        self._artwork = create_artwork_provider(conf, self._spotify, self._pixel_art)
        self._display_drawer = DisplayDrawer(self._spotify, self._pixel_art, conf.display)

    async def register_event_listeners(self, websocket: WebSocket) -> None:
        while True:
            event_data = await websocket.receive_json()
            await self._handle_websocket_event(event_data["event"])

    async def _handle_websocket_event(self, event_data: str) -> None:
        """Dispatch every client WebSocket event from one place."""
        match SpotifyEvent(event_data):
            case SpotifyEvent.NEXT_SONG:
                logger.info("Next song event received")
                await self._spotify.next_track()
            case SpotifyEvent.PREVIOUS_SONG:
                logger.info("Previous song event received")
                await self._spotify.previous_track()
            case SpotifyEvent.PAUSE_SONG:
                logger.info("Pause song event received")
                await self._spotify.pause()
            case SpotifyEvent.PLAY_SONG:
                logger.info("Play song event received")
                await self._spotify.play()

    async def run(self, websocket) -> None:
        while True:
            playback_state = await self._spotify.try_fetch_spotify_playback_state()

            if not playback_state or not playback_state.item:
                await asyncio.sleep(PollDelay.WS.value)
                continue

            if not playback_state.is_playing or self._spotify.is_same_artist(playback_state):
                self._spotify.update_playback_state(playback_state)
                await self._render_display(websocket)
                continue

            image = await self._resolve_playback_art_image(playback_state)
            await self._generate_pixel_art(image)

            if not self._spotify.is_same_song(playback_state):
                self._display_drawer.reset_scroll_offset()

            self._spotify.update_playback_state(playback_state)
            await self._render_display(websocket)

    async def _resolve_playback_art_image(self, playback_state: SpotifyPlaybackState):
        return await self._artwork.resolve(playback_state)

    async def _generate_pixel_art(self, image) -> None:
        if image is None:
            return

        if isinstance(image, str):
            image_bytes = await self._pixel_art.load_image_from_url(image)
        else:
            image_bytes = image

        prepared_image = self._pixel_art.prepare_image(image_bytes)
        self._pixel_art.to_bitmap(prepared_image)

    async def _render_display(self, websocket):
        if not self._spotify.playback_state:
            return

        image = self._display_drawer.draw_display()
        self._display_drawer.advance_scroll()
        logger.info("Display rendered")

        # live preview of the display for debugging purposes
        output_path = Path(__file__).parents[1] / "playback_state.jpeg"
        image.save(output_path)

        await websocket.send_bytes(self._display_drawer.to_bytes(image))
        await asyncio.sleep(0.5)
