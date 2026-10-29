from logging import getLogger

from app.face_extractor import FaceExtractor
from domain.spotify import SpotifyPlaybackState

logger = getLogger(__name__)


class FaceArtwork:
    def __init__(self, spotify, pixel_art, model_path):
        self.spotify = spotify
        self.pixel_art = pixel_art
        self.extractor = FaceExtractor(model_path)

    async def resolve(self, playback: SpotifyPlaybackState):
        current_artist = playback.item.artists[0]
        logger.info(f"New artist detected: {current_artist.name}")

        artist_images = await self.spotify.fetch_artist_images(current_artist.id)
        track_image = await self.spotify.fetch_track_image(playback.item.id)

        if not artist_images:
            logger.warning("No artist images found, falling back to track image")
            return track_image

        image = await self.pixel_art.load_image_from_url(artist_images[0])
        faces = self.extractor.extract_faces(image)

        if faces:
            logger.info(f"Detected {len(faces)} face(s)")
            return faces[0]

        logger.warning("No faces detected in artist image, falling back to track image")
        return track_image
