from domain.spotify import SpotifyPlaybackState


class BasicArtwork:
    def __init__(self, spotify):
        self.spotify = spotify

    async def resolve(self, playback: SpotifyPlaybackState):
        return await self.spotify.fetch_track_image(playback.item.id)
