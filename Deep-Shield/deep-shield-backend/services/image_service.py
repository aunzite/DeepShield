"""
Image authenticity analysis using deterministic heuristic scoring.

This module computes deterministic manipulation risk from visual signals
commonly seen in synthetic or heavily composited thumbnails.

NO machine learning models are used. This is a fast, rule-based analysis system.
"""

from io import BytesIO
from typing import Any, Dict

import cv2
import numpy as np
from PIL import Image

def analyze_image(file_bytes: bytes) -> Dict[str, Any]:
    """
    Analyze image authenticity using deterministic heuristic scoring.
    
    Computes synthetic manipulation probability from normalized metrics:
    - Edge density (Canny)
    - Saturation mean (HSV)
    - Contrast (grayscale std)
    - White text ratio (bright low-saturation overlay proxy)
    - Blur inverse (from Laplacian variance)
    
    Returns consistent, deterministic results for the same input.
    
    Returns:
        Dict with:
        - synthetic_probability: float (0-1)
        - confidence_level: str ("Low" | "Medium" | "High")
        - explanation: str
    """
    try:
        image = Image.open(BytesIO(file_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError("Invalid or corrupted image file.") from exc

    img_np = np.array(image, dtype=np.uint8)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)

    # 1) Edge density (poster/compositing spikes this)
    edges = cv2.Canny(gray, 80, 160)
    edge_density_raw = float(np.count_nonzero(edges) / edges.size)
    normalized_edge_density = min(1.0, max(0.0, edge_density_raw * 6.0))

    # 2) Saturation mean (oversaturated thumbnails score higher)
    saturation_mean_raw = float(np.mean(hsv[:, :, 1]) / 255.0)
    normalized_saturation = min(1.0, max(0.0, saturation_mean_raw * 2.0))

    # 3) Contrast (extreme contrast stylization)
    contrast_raw = float(np.std(gray) / 255.0)
    normalized_contrast = min(1.0, max(0.0, contrast_raw * 1.5))

    # 4) White text ratio (bright, low-saturation blocks common in clickbait overlays)
    white_mask = (hsv[:, :, 2] >= 220) & (hsv[:, :, 1] <= 60)
    white_text_ratio_raw = float(np.count_nonzero(white_mask) / white_mask.size)
    normalized_white_text_ratio = min(1.0, max(0.0, white_text_ratio_raw * 6.0))

    # 5) Blur inverse (synthetic/poster pipelines often over-smooth regions)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    normalized_blur_inverse = min(1.0, max(0.0, (1.0 / (laplacian_var + 1.0)) * 5.0))

    # Weighted synthetic probability (deterministic)
    synthetic_probability = (
        0.35 * normalized_edge_density +
        0.30 * normalized_saturation +
        0.20 * normalized_white_text_ratio +
        0.10 * normalized_contrast +
        0.05 * normalized_blur_inverse
    )

    synthetic_probability = float(min(max(synthetic_probability, 0.0), 1.0))

    # Confidence level
    if synthetic_probability > 0.75:
        confidence = "High"
    elif synthetic_probability >= 0.40:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "synthetic_probability": round(synthetic_probability, 4),
        "fake_probability": round(synthetic_probability, 4),
        "real_probability": round(1.0 - synthetic_probability, 4),
        "confidence_level": confidence,
        "explanation": (
            "This score reflects exaggerated saturation, contrast, edge density, "
            "and heavy text compositing commonly associated with synthetic or "
            "manipulated media."
        ),
    }
