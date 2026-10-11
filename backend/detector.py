"""
Runs the trained YOLO model on uploaded images.

Two interchangeable model formats:

- .pt   -- PyTorch weights, run with Ultralytics (local development)
- .onnx -- exported weights, run with onnxruntime (deployment). Needs no
           PyTorch, so it fits in small servers such as Render's free tier.

Export a new ONNX model after retraining with:
    yolo export model=runs/<run>/weights/best.pt format=onnx imgsz=640 opset=17 simplify=True
"""

from __future__ import annotations

import ast
import io
import os
import threading
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
PT_MODEL_PATH = ROOT / "runs" / "yolov8s_100e-3" / "weights" / "best.pt"
ONNX_MODEL_PATH = ROOT / "backend" / "models" / "best.onnx"


class InvalidImageError(ValueError):
    pass


def resolve_model_path(model_path: Path | str | None = None) -> Path:
    """MODEL_PATH env > local training weights > bundled ONNX model."""
    chosen = model_path or os.getenv("MODEL_PATH")
    if chosen:
        path = Path(chosen)
        return path if path.is_absolute() else ROOT / path
    return PT_MODEL_PATH if PT_MODEL_PATH.exists() else ONNX_MODEL_PATH


class _UltralyticsModel:

    def __init__(self, path: Path):
        from ultralytics import YOLO  # imported lazily: not installed in deployment

        self.model = YOLO(str(path))
        self.names = self.model.names

    def predict(self, image: Image.Image, conf: float) -> list[tuple[int, float, list[float]]]:
        result = self.model.predict(image, conf=conf, verbose=False)[0]
        return [
            (int(box.cls), float(box.conf), box.xyxy[0].tolist())
            for box in result.boxes
        ]


class _OnnxModel:
    """
    Re-implements Ultralytics' pre/post-processing for an exported YOLOv8
    model: letterbox to 640x640, then confidence filter + per-class NMS.
    """

    IOU_THRESHOLD = 0.7   # Ultralytics default
    MAX_DETECTIONS = 300
    PAD_COLOR = (114, 114, 114)

    def __init__(self, path: Path):
        import onnxruntime as ort

        self.session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        model_input = self.session.get_inputs()[0]
        self.input_name = model_input.name
        self.input_h, self.input_w = model_input.shape[2], model_input.shape[3]

        # Ultralytics stores the class names in the ONNX metadata
        metadata = self.session.get_modelmeta().custom_metadata_map
        self.names = {int(k): v for k, v in ast.literal_eval(metadata["names"]).items()}

    def _letterbox(self, image: Image.Image) -> tuple[np.ndarray, float, int, int]:
        w, h = image.size
        scale = min(self.input_w / w, self.input_h / h)
        new_w, new_h = round(w * scale), round(h * scale)
        left = round((self.input_w - new_w) / 2 - 0.1)
        top = round((self.input_h - new_h) / 2 - 0.1)

        canvas = Image.new("RGB", (self.input_w, self.input_h), self.PAD_COLOR)
        canvas.paste(image.resize((new_w, new_h), Image.BILINEAR), (left, top))

        array = np.asarray(canvas, dtype=np.float32) / 255.0
        return array.transpose(2, 0, 1)[None], scale, left, top

    @staticmethod
    def _nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> list[int]:
        x1, y1, x2, y2 = boxes.T
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        keep = []
        while order.size:
            i = order[0]
            keep.append(int(i))
            rest = order[1:]
            inter_w = np.clip(np.minimum(x2[i], x2[rest]) - np.maximum(x1[i], x1[rest]), 0, None)
            inter_h = np.clip(np.minimum(y2[i], y2[rest]) - np.maximum(y1[i], y1[rest]), 0, None)
            inter = inter_w * inter_h
            iou = inter / (areas[i] + areas[rest] - inter + 1e-9)
            order = rest[iou <= iou_threshold]
        return keep

    def predict(self, image: Image.Image, conf: float) -> list[tuple[int, float, list[float]]]:
        tensor, scale, left, top = self._letterbox(image)
        output = self.session.run(None, {self.input_name: tensor})[0]

        # (1, 4 + num_classes, anchors) -> (anchors, 4 + num_classes)
        predictions = output[0].T
        class_scores = predictions[:, 4:]
        class_ids = class_scores.argmax(axis=1)
        confidences = class_scores[np.arange(len(class_ids)), class_ids]

        mask = confidences > conf
        if not mask.any():
            return []
        cx, cy, bw, bh = predictions[mask, :4].T
        boxes = np.stack([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], axis=1)
        confidences, class_ids = confidences[mask], class_ids[mask]

        # Offset boxes per class so NMS never suppresses across classes
        keep = self._nms(boxes + class_ids[:, None] * 7680, confidences, self.IOU_THRESHOLD)
        keep = keep[: self.MAX_DETECTIONS]

        # Undo the letterbox: back to original image pixels
        img_w, img_h = image.size
        boxes = boxes[keep]
        boxes[:, [0, 2]] = ((boxes[:, [0, 2]] - left) / scale).clip(0, img_w)
        boxes[:, [1, 3]] = ((boxes[:, [1, 3]] - top) / scale).clip(0, img_h)

        return [
            (int(class_ids[i]), float(confidences[i]), box.tolist())
            for i, box in zip(keep, boxes)
        ]


class Detector:

    def __init__(self, model_path: Path | str | None = None):
        self.model_path = resolve_model_path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model weights not found: {self.model_path}")

        if self.model_path.suffix.lower() == ".onnx":
            self.model = _OnnxModel(self.model_path)
        else:
            self.model = _UltralyticsModel(self.model_path)

        # Neither backend is guaranteed thread-safe; FastAPI runs sync
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
            raw = self.model.predict(image, conf=min_confidence)

        detections = [
            {
                "class_id": class_id,
                "class_name": self.class_names[class_id],
                "confidence": round(confidence, 4),
                "bbox": [round(v, 1) for v in bbox],
            }
            for class_id, confidence, bbox in raw
        ]
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections
