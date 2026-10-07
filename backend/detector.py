"""
Runs the trained YOLO model on uploaded images.
"""

from __future__ import annotations

import io
import os
import threading
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = ROOT / "runs" / "yolov8s_100e-3" / "weights" / "best.pt"


class InvalidImageError(ValueError):
    pass


class Detector:

    def __init__(self, model_path: Path | None = None):
        # MODEL_PATH in .env lets you swap in iteration 2 weights without code changes
        self.model_path = Path(model_path or os.getenv("MODEL_PATH") or DEFAULT_MODEL_PATH)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model weights not found: {self.model_path}")

        self.model = YOLO(str(self.model_path))

        # Ultralytics predictors are not thread-safe; FastAPI runs sync
        # endpoints in a thread pool, so serialise inference.
        self._lock = threading.Lock()

    @property
    def class_names(self) -> dict[int, str]:
        return self.model.names

    def detect(self, image_bytes: bytes, min_confidence: float = 0.4) -> list[dict]:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Phone photos store rotation in EXIF; apply it so the model sees
            # the image upright and boxes line up with what the browser shows
            image = ImageOps.exif_transpose(image).convert("RGB")
        except (UnidentifiedImageError, OSError) as e:
            raise InvalidImageError("File is not a readable image") from e

        with self._lock:
            result = self.model.predict(image, conf=min_confidence, verbose=False)[0]

        detections = []
        for box in result.boxes:
            class_id = int(box.cls)
            detections.append({
                "class_id": class_id,
                "class_name": self.class_names[class_id],
                "confidence": round(float(box.conf), 4),
                "bbox": [round(v, 1) for v in box.xyxy[0].tolist()],
            })

        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections
