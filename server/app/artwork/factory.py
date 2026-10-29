from pathlib import Path

from app.artwork.basic import BasicArtwork
from app.constants import ArtworkMode


def artwork_mode(conf):
    mode = conf.artwork_mode
    try:
        return ArtworkMode(mode)
    except ValueError:
        raise ValueError(f"Invalid ARTWORK_MODE {mode!r}; expected 'basic' or 'faces'")


def create_pixel_art(conf):
    if artwork_mode(conf) == ArtworkMode.BASIC:
        from app.artwork.basic_pixels import PixelArt
    else:
        from app.pixel_art import PixelArt
    return PixelArt()


def create_artwork_provider(conf, spotify, pixel_art):
    if artwork_mode(conf) == ArtworkMode.BASIC:
        return BasicArtwork(spotify)
    from app.artwork.faces import FaceArtwork

    model_path = Path(__file__).resolve().parents[2] / "models" / conf.model_name
    return FaceArtwork(spotify, pixel_art, model_path)
