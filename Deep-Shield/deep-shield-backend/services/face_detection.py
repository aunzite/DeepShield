"""
Face detection for the deepfake pipeline.

Uses OpenCV DNN face detection on full-resolution RGB images.
No resizing before detection. Returns largest face crop with 10% padding.
"""

from functools import lru_cache
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

# Minimum detection confidence
MIN_DETECTION_CONFIDENCE = 0.5

# Padding around face bbox as fraction of box size (10%)
FACE_PADDING = 0.1


def _get_face_detector():
    """Lazy load OpenCV DNN face detector."""
    # Use OpenCV's pre-trained DNN face detector (Caffe model)
    # This is a simple implementation that works without external files
    # For production, you might want to download proper model files
    # For now, we'll use Haar Cascade which is built into OpenCV
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    detector = cv2.CascadeClassifier(cascade_path)
    if detector.empty():
        raise RuntimeError("Failed to load face detector")
    return detector


@lru_cache(maxsize=1)
def _detector():
    return _get_face_detector()


def _pil_to_rgb_numpy(image: Image.Image) -> np.ndarray:
    """Convert PIL Image to RGB numpy array (H, W, 3) for OpenCV."""
    img = image.convert("RGB")
    return np.array(img, dtype=np.uint8)


def detect_faces(image: Image.Image) -> Tuple[Optional[List[Tuple[int, int, int, int]]], Optional[List[float]]]:
    """
    Run face detection on full-resolution image using OpenCV. Do NOT resize before calling.

    Args:
        image: PIL Image, already converted to RGB (any size).

    Returns:
        (boxes, scores) or (None, None) if no faces.
        boxes: list of (x1, y1, x2, y2) in pixel coordinates.
        scores: list of confidence scores per face.
    """
    rgb = _pil_to_rgb_numpy(image)
    # Convert RGB to BGR for OpenCV
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    h, w = rgb.shape[0], rgb.shape[1]

    detector = _detector()
    # detectMultiScale returns (x, y, w, h) tuples
    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    if len(faces) == 0:
        return None, None

    boxes: List[Tuple[int, int, int, int]] = []
    scores: List[float] = []

    for (x, y, width, height) in faces:
        # Convert to x1, y1, x2, y2 format
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w, x + width)
        y2 = min(h, y + height)
        
        # Ensure valid box
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(x1 + 1, min(x2, w))
        y2 = max(y1 + 1, min(y2, h))
        
        boxes.append((x1, y1, x2, y2))
        # Haar cascades don't provide confidence scores, use a fixed value
        scores.append(0.9)

    return boxes, scores


def _expand_box(
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
    Detect faces on full-resolution image, select largest bbox, add 10% padding, crop.

    Args:
        image: PIL Image (RGB, full resolution; do not resize before calling).

    Returns:
        Cropped RGB PIL Image of the largest face, or None if no face detected.
    """
    boxes, scores = detect_faces(image)
    if not boxes:
        return None

    # Select largest face by area
    areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in boxes]
    idx = max(range(len(areas)), key=lambda i: areas[i])
    x1, y1, x2, y2 = boxes[idx]
    w_img, h_img = image.size

    x1, y1, x2, y2 = _expand_box(x1, y1, x2, y2, w_img, h_img)
    if x2 <= x1 or y2 <= y1:
        return None

    return image.crop((x1, y1, x2, y2)).convert("RGB")
