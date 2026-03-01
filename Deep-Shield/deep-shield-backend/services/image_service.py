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

def analyze_image(file_bytes: bytes) -> Dict[str, Any]:
    """
    Detect AI-generated faces using multiple complementary features:
    1. Texture variance (Laplacian) - AI faces are too smooth
    2. Frequency analysis - AI has reduced high-frequency
    3. Color gradient smoothness - AI has too uniform gradients
    
    Real faces have natural texture, color variation, and detail.
    AI faces are overly smooth and artificially perfect.
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

    # Feature 1: Texture variance (Laplacian)
    # Real faces: lap_var typically 80-400+ (natural skin texture)
    # AI faces: lap_var typically 20-80 (too smooth, plastic-looking)
    lap_var = _laplacian_variance(gray)
    
    # Normalize: higher texture = more real
    # Range: assume lap_var between 10 and 300 for meaningful spread
    texture_indicator = min(1.0, max(0.0, (lap_var - 25.0) / 200.0))
    
    # Feature 2: Frequency analysis
    low_ratio, mid_ratio, high_ratio = _fft_analysis(gray)
    
    # Real faces: good distribution across frequencies, particularly high-freq (0.20-0.40)
    # AI faces: dominated by low/mid freq, very little high-freq (<0.12)
    # Look for balanced distribution
    balance_indicator = 1.0 - abs(low_ratio - 0.35)  # Ideal is around 0.35
    
    # High-frequency is a good indicator of real detail
    high_freq_indicator = min(1.0, max(0.0, (high_ratio - 0.10) / 0.25))
    
    # Feature 3: Local contrast (variation in small patches)
    # AI faces have uniform skin, real faces have texture variation
    # Compute gradient magnitude
    gy, gx = np.gradient(gray.astype(float))
    gradient_mag = np.sqrt(gx**2 + gy**2)
    gradient_variance = np.var(gradient_mag)
    
    # Normalize gradient variance
    gradient_indicator = min(1.0, max(0.0, (gradient_variance - 5.0) / 50.0))
    
    # Combine indicators
    # Weight: texture (40%), frequency balance (30%), gradient (20%), high-freq (10%)
    real_score = (
        0.40 * texture_indicator +
        0.20 * balance_indicator +
        0.25 * gradient_indicator +
        0.15 * high_freq_indicator
    )
    
    # Clamp to [0, 1]
    real_score = max(0.0, min(1.0, real_score))
    
    # Convert to probabilities
    real_probability = real_score
    fake_probability = 1.0 - real_score

    confidence = _confidence_level(real_probability, fake_probability)

    return {
        "real_probability": round(real_probability, 4),
        "fake_probability": round(fake_probability, 4),
        "confidence_level": confidence,
    }
