from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageOps
from server.app.constants import ArtworkSize


class PixelArt:
    def __init__(self):
        self.bitmap: Image.Image | None = None

    @staticmethod
    async def load_image_from_url(url: str) -> Image.Image:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

        with Image.open(BytesIO(response.content)) as image:
            return image.convert("RGB")

    @staticmethod
    def prepare_image(image: Image.Image, width: int = ArtworkSize.WIDTH, height: int = ArtworkSize.HEIGHT) -> Image.Image:
        gray = ImageOps.autocontrast(image.convert("L"))
        return gray.resize((width, height), Image.Resampling.LANCZOS)

    def to_bitmap(self, image: Image.Image) -> Image.Image:
        self.bitmap = image.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        return self.bitmap

    @staticmethod
    def write_bitmap_preview(bitmap: Image.Image, path: Path, scale: int = 8) -> None:
        bitmap.resize((bitmap.width * scale, bitmap.height * scale), Image.Resampling.NEAREST).save(path)
