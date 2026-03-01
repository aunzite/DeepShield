"""
Image analysis: face detection + heuristic scoring (demo / hackathon MVP).

- MediaPipe face detection; if no face -> error.
- Heuristics: blur (Laplacian variance), edge density, color entropy.
- Normalize into fake_probability. No ML models, no downloads, pure CPU.
"""

from io import BytesIO
from typing import Any, Dict

import numpy as np
from PIL import Image

from services.face_detection import crop_largest_face

NO_FACE_MESSAGE = "No face detected. Ensure a clear frontal human face is visible."


def _laplacian_variance(gray: np.ndarray) -> float:
    """Approximate Laplacian (3x3) and return variance. Numpy only."""
    g = np.asarray(gray, dtype=np.float64)
    lap = np.zeros_like(g)
    lap[1:-1, 1:-1] = (
        g[2:, 1:-1] + g[:-2, 1:-1] + g[1:-1, 2:] + g[1:-1, :-2]
        - 4.0 * g[1:-1, 1:-1]
    )
    return float(np.var(lap))


def _edge_density(gray: np.ndarray, threshold: float = 15.0) -> float:
    """Fraction of pixels with strong Laplacian response (edges)."""
    g = np.asarray(gray, dtype=np.float64)
    lap = np.zeros_like(g)
    lap[1:-1, 1:-1] = (
        g[2:, 1:-1] + g[:-2, 1:-1] + g[1:-1, 2:] + g[1:-1, :-2]
        - 4.0 * g[1:-1, 1:-1]
    )
    total = lap.size
    if total == 0:
        return 0.0
    strong = np.sum(np.abs(lap) > threshold)
    return float(strong) / float(total)


def _color_entropy(rgb: np.ndarray, bins: int = 32) -> float:
    """Normalized entropy of color distribution (single channel histogram)."""
    flat = rgb.reshape(-1, 3).mean(axis=1)
    hist, _ = np.histogram(flat, bins=bins, range=(0, 256))
    hist = hist.astype(np.float64) + 1e-10
    hist /= hist.sum()
    ent = -np.sum(hist * np.log2(hist))
    max_ent = np.log2(bins)
    return float(ent / max_ent) if max_ent > 0 else 0.0


def _confidence_level(real_prob: float, fake_prob: float) -> str:
    max_prob = max(real_prob, fake_prob)
    if max_prob > 0.8:
        return "High"
    if max_prob >= 0.5:
        return "Medium"
    return "Low"


def analyze_image(file_bytes: bytes) -> Dict[str, Any]:
    """
    Run lightweight pipeline: face detection -> heuristics -> fake probability.

    No model loading, no downloads. Returns real_probability, fake_probability,
    confidence_level, or error if no face.
    """
    try:
        image = Image.open(BytesIO(file_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError("Invalid or corrupted image file.") from exc

    face_crop = crop_largest_face(image)
    if face_crop is None:
        return {"error": NO_FACE_MESSAGE}

    arr = np.array(face_crop, dtype=np.uint8)
    gray = arr.mean(axis=2)

    lap_var = _laplacian_variance(gray)
    edge_den = _edge_density(gray)
    entropy = _color_entropy(arr)

    # Normalize blur: low Laplacian variance -> more blur -> higher fake score
    # Typical sharp face: lap_var in hundreds to thousands; blur: low tens
    blur_score = 1.0 - min(1.0, lap_var / 800.0)
    # Low edge density -> smoother/faker looking
    edge_score = 1.0 - min(1.0, edge_den * 4.0)
    # Entropy: very low or very high can look "off"; center around 0.5
    entropy_score = 0.5 + 0.3 * (entropy - 0.5)

    fake_prob = 0.4 * blur_score + 0.35 * edge_score + 0.25 * max(0, min(1, entropy_score))
    fake_prob = max(0.0, min(1.0, fake_prob))
    real_prob = 1.0 - fake_prob

    confidence = _confidence_level(real_prob, fake_prob)

    return {
        "real_probability": round(real_prob, 4),
        "fake_probability": round(fake_prob, 4),
        "confidence_level": confidence,
    }
