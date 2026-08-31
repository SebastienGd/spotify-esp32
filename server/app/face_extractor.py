from logging import getLogger
from pathlib import Path

import insightface
import numpy as np

from app.constants import FacePadding

logger = getLogger(__name__)


class FaceExtractor:
    def __init__(self, model_path: Path):
        self.extractor = insightface.model_zoo.get_model(str(model_path))
        if not self.extractor:
            raise RuntimeError(f"Failed to load face detection model from {model_path}")
        if not isinstance(self.extractor, insightface.model_zoo.SCRFD):
            raise RuntimeError(f"Model loaded from {model_path} is not a SCRFD model")
        self.extractor.prepare(ctx_id=-1)

    def extract_faces(self, image_bytes: np.ndarray) -> list[np.ndarray]:
        faces = []
        if not isinstance(self.extractor, insightface.model_zoo.SCRFD):
            raise RuntimeError("Model is not a SCRFD model")

        boxes, _ = self.extractor.detect(image_bytes, input_size=(640, 640))
        if boxes is None:
            logger.warning("No faces detected")
            return faces

        for box in boxes:
            x1, y1, x2, y2 = self.add_padding_to_faces(box, image_bytes)
            face = image_bytes[y1:y2, x1:x2]
            faces.append(face)

        return faces

    def add_padding_to_faces(self, box, image: np.ndarray) -> tuple[int, int, int, int]:
        x1, y1, x2, y2, _ = box
        image_h, image_w = image.shape[:2]

        face_width = x2 - x1
        face_height = y2 - y1

        x1 -= face_width * FacePadding.LEFT
        x2 += face_width * FacePadding.RIGHT

        y1 -= face_height * FacePadding.TOP
        y2 += face_height * FacePadding.BOTTOM

        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(image_w, int(x2))
        y2 = min(image_h, int(y2))

        return x1, y1, x2, y2
