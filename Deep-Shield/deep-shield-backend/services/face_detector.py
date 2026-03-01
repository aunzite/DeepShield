"""
Face detection for deepfake pipeline.

Uses RetinaFace for robust detection of frontal and in-the-wild faces.
Runs on full-resolution image; crops largest face with padding; no resize here
(resize to model input size is done in the deepfake model processor).
"""

import logging
from functools import lru_cache
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

# Debug logging: number of faces, bbox, confidence
logger = logging.getLogger(__name__)

# Padding around face bbox as fraction of box size (e.g. 0.1 = 10% on each side)
FACE_PADDING = 0.1

# RetinaFace detection confidence threshold (lower = more recall, may get more false positives)
DETECT_THRESHOLD = 0.5


def _get_retinaface_model():
    """Lazy import and build RetinaFace model (TensorFlow) to avoid loading at import time."""
    from retinaface import RetinaFace
    return RetinaFace


@lru_cache(maxsize=1)
def _retinaface_class():
    return _get_retinaface_model()


def _pil_to_detector_array(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to BGR numpy array (H, W, 3) uint8 for RetinaFace (OpenCV convention)."""
    img = image.convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    return arr[:, :, ::-1].copy()


def detect_faces(image: Image.Image) -> Tuple[Optional[List[Tuple[int, int, int, int]]], Optional[List[float]]]:
    """
    Detect face bounding boxes in a PIL Image using RetinaFace.

    Image is used at full resolution. Expects RGB.

    Returns:
        (boxes, scores) or (None, None) if no faces.
        boxes: list of (x1, y1, x2, y2) in image coordinates.
        scores: list of confidence scores per box.
    """
    width, height = image.size
    print(f"[DEBUG] Input image resolution: width={width}, height={height}", flush=True)
    arr = _pil_to_detector_array(image)
    try:
        RetinaFace = _retinaface_class()
        resp = RetinaFace.detect_faces(arr, threshold=DETECT_THRESHOLD)
    except Exception as e:
        logger.warning("RetinaFace.detect_faces failed: %s", e)
        return None, None
    if not isinstance(resp, dict) or len(resp) == 0:
        print("[DEBUG] Face detection: 0 faces detected", flush=True)
        return None, None

    boxes: List[Tuple[int, int, int, int]] = []
    scores: List[float] = []
    for key, face in resp.items():
        if not isinstance(face, dict):
            continue
        fa = face.get("facial_area")
        score = face.get("score", 0.0)
        if fa is None or len(fa) < 4:
            continue
        x1, y1, x2, y2 = int(fa[0]), int(fa[1]), int(fa[2]), int(fa[3])
        boxes.append((x1, y1, x2, y2))
        scores.append(float(score))

    # Debug: number of faces, bbox, confidence (always printed)
    print(f"[DEBUG] Face detection: {len(boxes)} face(s) detected", flush=True)
    for i, (box, score) in enumerate(zip(boxes, scores)):
        print(f"[DEBUG]   face_{i + 1}: bbox=(x1={box[0]}, y1={box[1]}, x2={box[2]}, y2={box[3]}), confidence={score:.4f}", flush=True)

    if not boxes:
        return None, None
    return boxes, scores


def preload_face_detector() -> None:
    """Build RetinaFace model so first request is fast. Call at startup."""
    import numpy as np
    RetinaFace = _retinaface_class()
    dummy = np.zeros((100, 100, 3), dtype=np.uint8)  # BGR
    RetinaFace.detect_faces(dummy, threshold=0.99)  # no faces; just loads model
    print("[DEBUG] RetinaFace model preloaded", flush=True)


def _expand_box_with_padding(
    x1: int, y1: int, x2: int, y2: int,
    img_width: int, img_height: int,
    padding_frac: float = FACE_PADDING,
) -> Tuple[int, int, int, int]:
    """Expand bbox by padding_frac of box size on each side; clamp to image."""
    w = x2 - x1
    h = y2 - y1
    pad_w = int(w * padding_frac)
    pad_h = int(h * padding_frac)
    x1 = max(0, x1 - pad_w)
    y1 = max(0, y1 - pad_h)
    x2 = min(img_width, x2 + pad_w)
    y2 = min(img_height, y2 + pad_h)
    return x1, y1, x2, y2


def crop_largest_face(image: Image.Image) -> Optional[Image.Image]:
    """
    Detect faces with RetinaFace on full-resolution image, select largest bbox,
    add small padding, crop, and return RGB PIL Image.

    Returns:
        Cropped RGB PIL Image, or None if no face detected.
    """
    boxes, scores = detect_faces(image)
    if not boxes:
        return None

    # Select largest face by area
    areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in boxes]
    idx = max(range(len(areas)), key=lambda i: areas[i])
    x1, y1, x2, y2 = boxes[idx]
    w_img, h_img = image.size

    x1, y1, x2, y2 = _expand_box_with_padding(x1, y1, x2, y2, w_img, h_img)
    if x2 <= x1 or y2 <= y1:
        return None

    crop = image.crop((x1, y1, x2, y2)).convert("RGB")
    return crop
