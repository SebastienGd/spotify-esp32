import asyncio
from logging import getLogger
from pathlib import Path

from fastapi import WebSocket
import numpy as np
from omegaconf import DictConfig

from app.constants import PollDelay, SpotifyEvent
from app.display_drawer import DisplayDrawer
from app.face_extractor import FaceExtractor
from app.pixel_art import PixelArt
from app.spotify import Spotify
from domain.spotify import SpotifyPlaybackState


logger = getLogger(__name__)


class Orchestrator:
    def __init__(self, conf: DictConfig):
        self._model_path = Path(__file__).parents[1] / "models" / conf.model_name

        self.conf = conf
        self._spotify = Spotify(conf)
        self._pixel_art = PixelArt()
        self._face_extractor = FaceExtractor(self._model_path)
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
        current_artist = playback_state.item.artists[0]
        logger.info(f"New artist detected: {current_artist.name}")

        artist_images = await self._spotify.fetch_artist_images(current_artist.id)

        track_image = await self._spotify.fetch_track_image(playback_state.item.id)

        if not artist_images:
            logger.warning("No artist images found, falling back to track image")
            return track_image

        image = await self._pixel_art.load_image_from_url(artist_images[0])

        faces = self._face_extractor.extract_faces(image)

        if faces:
            logger.info(f"Detected {len(faces)} face(s)")
            return faces[0]

        logger.warning("No faces detected in artist image, falling back to track image")

        return track_image

    async def _generate_pixel_art(self, image: str | np.ndarray | None) -> None:
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
