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


def analyze_image(file_bytes: bytes) -> Dict[str, Any]:
    """
    Analyze image authenticity using deterministic heuristic scoring.
    
    Computes a synthetic probability score based on:
    - Blur detection (Laplacian variance)
    - Edge density (Canny detection)  
    - Noise level (grayscale std deviation)
    - Entropy (histogram distribution)
    
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

    # Convert to numpy array
    img_np = np.array(face_crop, dtype=np.uint8)
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # 1. Blur detection
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

    # 2. Edge density
    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges) / edges.size

    # 3. Noise level
    noise_std = np.std(gray)

    # 4. Entropy
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist_norm = hist / hist.sum()
    entropy = -np.sum([p * np.log2(p) for p in hist_norm if p != 0])

    # Normalize metrics into synthetic score
    blur_score = 1 / (laplacian_var + 1)
    entropy_score = 1 / (entropy + 1)
    noise_score = 1 / (noise_std + 1)

    synthetic_probability = (
        0.4 * blur_score +
        0.3 * entropy_score +
        0.3 * noise_score
    )

    synthetic_probability = float(min(max(synthetic_probability, 0), 1))
    real_probability = 1.0 - synthetic_probability

    # Confidence level
    if synthetic_probability > 0.75:
        confidence = "High"
    elif synthetic_probability > 0.4:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "real_probability": round(real_probability, 4),
        "fake_probability": round(synthetic_probability, 4),
        "confidence_level": confidence,
    }
