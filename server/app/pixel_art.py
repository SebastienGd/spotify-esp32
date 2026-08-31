from pathlib import Path

import cv2
import httpx
import numpy as np


class PixelArt:
    bitmap: np.ndarray | None = None

    @staticmethod
    async def load_image_from_url(url: str) -> np.ndarray:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

        image_bytes = np.frombuffer(response.content, dtype=np.uint8)

        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Could not decode image")

        return image

    @staticmethod
    def prepare_image(image: np.ndarray, width: int = 64, height: int = 64) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        gray = cv2.resize(gray, (width, height), interpolation=cv2.INTER_AREA)

        return gray

    @classmethod
    def to_bitmap(cls, image: np.ndarray) -> np.ndarray:
        img = image.astype(np.float32).copy()

        height, width = img.shape

        for y in range(height):
            for x in range(width):
                old = img[y, x]

                new = 255 if old >= 128 else 0
                img[y, x] = new

                error = old - new

                if x + 1 < width:
                    img[y, x + 1] += error * 7 / 16

                if y + 1 < height:
                    if x > 0:
                        img[y + 1, x - 1] += error * 3 / 16

                    img[y + 1, x] += error * 5 / 16

                    if x + 1 < width:
                        img[y + 1, x + 1] += error * 1 / 16

        cls.bitmap = np.clip(img, 0, 255).astype(np.uint8)

        return cls.bitmap

    @staticmethod
    def write_bitmap_preview(bitmap: np.ndarray, path: Path, scale: int = 8) -> None:
        preview = cv2.resize(bitmap, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)

        if not cv2.imwrite(str(path), preview):
            raise RuntimeError(f"Failed to write bitmap preview to {path}")
