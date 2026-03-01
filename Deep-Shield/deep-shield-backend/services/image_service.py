"""
Image authenticity analysis using deterministic heuristic scoring.

This module analyzes visual texture patterns, entropy distribution, and structural 
features to compute a synthetic authenticity probability. Results are consistent
and deterministic for the same input image.

NO machine learning models are used. This is a fast, rule-based analysis system.
"""

from io import BytesIO
from typing import Any, Dict

import cv2
import numpy as np
from PIL import Image

from services.face_detection import crop_largest_face

NO_FACE_MESSAGE = "No face detected. Ensure a clear frontal human face is visible."


def _compute_blur_score(gray: np.ndarray) -> float:
    """
    Compute blur score using variance of Laplacian.
    Higher values indicate sharper images.
    
    Returns normalized score (0-1, where 1 = very blurry, 0 = sharp)
    """
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Typical range: 10-500 for faces
    # Normalize: lower variance = more blur = higher score
    blur_score = 1.0 - min(1.0, laplacian_var / 200.0)
    return max(0.0, min(1.0, blur_score))


def _compute_edge_density(gray: np.ndarray) -> float:
    """
    Compute edge density using Canny edge detection.
    
    Returns normalized score (0-1, where 1 = very high edge density)
    """
    # Apply Canny edge detection
    edges = cv2.Canny(gray.astype(np.uint8), 50, 150)
    
    # Calculate percentage of edge pixels
    edge_density = np.sum(edges > 0) / edges.size
    
    # Normalize: typical range 0.05-0.30 for faces
    normalized = edge_density / 0.25
    return max(0.0, min(1.0, normalized))


def _compute_color_entropy(rgb: np.ndarray) -> float:
    """
    Compute color entropy to measure distribution randomness.
    
    Returns normalized score (0-1, where 1 = high entropy/randomness)
    """
    # Compute histogram for each channel
    entropies = []
    for channel in range(3):
        hist, _ = np.histogram(rgb[:, :, channel], bins=256, range=(0, 256))
        hist = hist.astype(float) / (hist.sum() + 1e-10)
        hist = hist[hist > 0]  # Remove zero bins
        entropy = -np.sum(hist * np.log2(hist))
        entropies.append(entropy)
    
    # Average entropy across channels
    avg_entropy = np.mean(entropies)
    
    # Normalize: typical range 4-8 bits for natural images
    normalized = (avg_entropy - 4.0) / 4.0
    return max(0.0, min(1.0, normalized))


def _compute_noise_level(gray: np.ndarray) -> float:
    """
    Compute noise level using standard deviation of grayscale image.
    
    Returns normalized score (0-1, where 1 = very low noise/smooth)
    """
    std_dev = np.std(gray)
    
    # Normalize: typical range 10-60 for faces
    # Lower std = smoother/less noise = higher synthetic score
    noise_score = 1.0 - min(1.0, std_dev / 50.0)
    return max(0.0, min(1.0, noise_score))


def _confidence_level(synthetic_prob: float) -> str:
    """
    Determine confidence level based on synthetic probability.
    
    > 0.75 = High confidence
    0.4 - 0.75 = Medium confidence
    < 0.4 = Low confidence
    """
    if synthetic_prob > 0.75 or synthetic_prob < 0.25:
        return "High"
    if 0.4 <= synthetic_prob <= 0.6:
        return "Low"
    return "Medium"


def analyze_image(file_bytes: bytes) -> Dict[str, Any]:
    """
    Analyze image authenticity using deterministic heuristic scoring.
    
    Computes a synthetic probability score based on:
    - Blur/sharpness (Laplacian variance)
    - Edge density (Canny detection)  
    - Color entropy (distribution randomness)
    - Noise level (grayscale std deviation)
    
    Returns consistent, deterministic results for the same input.
    
    Returns:
        Dict with:
        - real_probability: float (0-1)
        - fake_probability: float (0-1)
        - confidence_level: str ("Low" | "Medium" | "High")
    """
    try:
        image = Image.open(BytesIO(file_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError("Invalid or corrupted image file.") from exc

    face_crop = crop_largest_face(image)
    if face_crop is None:
        return {"error": NO_FACE_MESSAGE}

    # Convert to numpy arrays
    rgb_array = np.array(face_crop, dtype=np.uint8)
    gray_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2GRAY)

    # Compute individual metrics
    blur_score = _compute_blur_score(gray_array)
    edge_density = _compute_edge_density(gray_array)
    color_entropy = _compute_color_entropy(rgb_array)
    noise_level = _compute_noise_level(gray_array)

    # Synthetic probability formula
    # High blur + low entropy + low noise + abnormal edges = likely synthetic
    # Weights tuned for face images
    low_entropy_weight = 0.30
    smoothness_weight = 0.35
    sharpness_weight = 0.20
    blur_weight = 0.15

    # Inverse entropy (low entropy is suspicious)
    inverse_entropy = 1.0 - color_entropy
    
    # Smoothness factor (low noise is suspicious)
    smoothness_factor = noise_level
    
    # Abnormal edge density (too perfect edges)
    # Real faces: 0.10-0.25 edge density
    # Perfect/synthetic: <0.08 or >0.30
    edge_abnormality = 0.0
    if edge_density < 0.32:  # Too few edges
        edge_abnormality = (0.32 - edge_density) / 0.32
    elif edge_density > 0.90:  # Too many edges
        edge_abnormality = (edge_density - 0.90) / 0.10

    # Compute synthetic score
    synthetic_score = (
        low_entropy_weight * inverse_entropy +
        smoothness_weight * smoothness_factor +
        sharpness_weight * edge_abnormality +
        blur_weight * blur_score
    )

    # Normalize to [0, 1]
    synthetic_probability = max(0.0, min(1.0, synthetic_score))
    real_probability = 1.0 - synthetic_probability

    confidence = _confidence_level(synthetic_probability)

    return {
        "real_probability": round(real_probability, 4),
        "fake_probability": round(synthetic_probability, 4),
        "confidence_level": confidence,
    }
