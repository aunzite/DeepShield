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

    AI-generated faces tend to be:
    - Overly smooth (low texture/detail in skin)
    - Unnaturally symmetric
    - Consistent/perfect lighting and color
    
    Real faces tend to have:
    - Natural texture variation in skin
    - Subtle asymmetries
    - Natural lighting inconsistencies
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

    # AI faces are TOO SMOOTH (high Laplacian variance suggests texture/detail)
    # Real faces: lap_var typically 100-500+ (natural skin texture)
    # AI faces: lap_var typically much lower (over-smoothed skin)
    # Score: high lap_var = more real features present = LOWER fake score
    smoothness_score = 1.0 - min(1.0, lap_var / 300.0)  # Inverted: smoothness = fake
    
    # AI faces have very consistent edges (over-processed)
    # Real faces have varied, natural edge distribution
    # High edge density = more natural texture = LOWER fake score
    edge_consistency_score = 1.0 - min(1.0, edge_den * 3.0)
    
    # Entropy: AI images often have unnaturally uniform color distributions
    # Real skin has natural color variation (redness, blemishes, freckles, etc.)
    # Low entropy (too uniform) suggests AI generation
    entropy_score = 1.0 - min(1.0, entropy * 1.5)  # Low entropy = more artificial

    # Weighted combination: smoothness is strongest indicator
    fake_prob = 0.5 * smoothness_score + 0.3 * edge_consistency_score + 0.2 * entropy_score
    fake_prob = max(0.0, min(1.0, fake_prob))
    real_prob = 1.0 - fake_prob

    confidence = _confidence_level(real_prob, fake_prob)

    return {
        "real_probability": round(real_prob, 4),
        "fake_probability": round(fake_prob, 4),
        "confidence_level": confidence,
    }
