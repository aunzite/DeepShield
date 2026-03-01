"""
Image analysis: face detection + frequency domain AI detection.

AI-generated faces have characteristic frequency patterns:
- Different FFT magnitude distribution than real faces
- Reduced high-frequency components (overly smooth)
- Anomalous phase patterns

This uses frequency analysis which is effective for detecting AI-generated content.
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


def _fft_analysis(gray: np.ndarray) -> tuple:
    """
    Frequency domain analysis for AI detection.
    
    AI faces typically show:
    - Lower high-frequency energy (over-smoothed)
    - Different frequency distribution pattern
    """
    # Compute FFT
    fft = np.fft.fft2(gray)
    fft_shift = np.fft.fftshift(fft)
    magnitude = np.abs(fft_shift)
    
    # Normalize
    magnitude = magnitude / (magnitude.max() + 1e-10)
    
    h, w = gray.shape
    cy, cx = h // 2, w // 2
    
    # Divide into frequency bands
    # Low frequency (center): natural image content
    # Mid frequency: edges and textures  
    # High frequency: noise and fine details
    
    # Create frequency masks
    y, x = np.ogrid[:h, :w]
    distance = np.sqrt((x - cx)**2 + (y - cy)**2)
    
    # Radius thresholds
    low_r = min(h, w) / 8
    mid_r = min(h, w) / 4
    
    low_freq = distance <= low_r
    mid_freq = (distance > low_r) & (distance <= mid_r)
    high_freq = distance > mid_r
    
    low_energy = np.sum(magnitude[low_freq])
    mid_energy = np.sum(magnitude[mid_freq])
    high_energy = np.sum(magnitude[high_freq])
    
    total_energy = low_energy + mid_energy + high_energy + 1e-10
    
    low_ratio = low_energy / total_energy
    mid_ratio = mid_energy / total_energy
    high_ratio = high_energy / total_energy
    
    return low_ratio, mid_ratio, high_ratio


def _confidence_level(real_prob: float, fake_prob: float) -> str:
    max_prob = max(real_prob, fake_prob)
    if max_prob > 0.8:
        return "High"
    if max_prob >= 0.6:
        return "Medium"
    return "Low"


def analyze_image(file_bytes: bytes) -> Dict[str, Any]:
    """
    Detect AI-generated faces using:
    1. Frequency domain analysis (FFT patterns)
    2. Texture variance (Laplacian)
    
    AI faces show characteristic frequency patterns with reduced high-frequency content.
    Real faces have natural texture and detail distribution.
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

    # Feature 1: Texture variance (high for real, low for AI)
    lap_var = _laplacian_variance(gray)
    # Real faces typically have lap_var 100-600+
    # AI faces often have lap_var 10-80 (too smooth)
    # Stricter: require lap_var > 80 for decent score
    texture_score = min(1.0, max(0.0, (lap_var - 50.0) / 120.0))
    
    # Feature 2: Frequency analysis
    low_ratio, mid_ratio, high_ratio = _fft_analysis(gray)
    
    # Real faces should have high-frequency content (0.20-0.40)
    # AI faces typically have very low high-frequency (<0.12)
    # Much stricter: penalize anything below 0.18
    high_freq_score = min(1.0, max(0.0, (high_ratio - 0.12) / 0.20))
    
    # Mid-frequency being very high (>0.45) is suspicious of AI over-smoothing
    mid_freq_penalty = max(0.0, min(1.0, (mid_ratio - 0.40) / 0.15))
    
    # Low frequency being dominant (>0.55) suggests lack of detail (AI)
    low_freq_penalty = max(0.0, min(1.0, (low_ratio - 0.50) / 0.15))
    
    # Final scoring: real faces need BOTH good texture AND high-frequency
    # Much stricter weighting
    real_score = 0.6 * texture_score + 0.4 * high_freq_score
    
    # Apply AI penalties more aggressively
    ai_indicators = max(mid_freq_penalty, low_freq_penalty)
    
    fake_probability = (1.0 - real_score) * (1.0 + ai_indicators * 2.0)
    fake_probability = max(0.0, min(1.0, fake_probability))
    real_probability = 1.0 - fake_probability

    confidence = _confidence_level(real_probability, fake_probability)

    return {
        "real_probability": round(real_probability, 4),
        "fake_probability": round(fake_probability, 4),
        "confidence_level": confidence,
    }
