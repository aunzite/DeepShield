"""
Deepfake inference pipeline.

1. Load image, convert to RGB.
2. Face detection (MediaPipe) on original resolution.
3. Crop largest face with 10% padding.
4. Resize to 128x128, normalize, tensor, forward pass, softmax.
5. Return real_probability, fake_probability, confidence_level.
"""

import time
from io import BytesIO
from typing import Any, Dict

import numpy as np
import torch
from PIL import Image

from services.face_detection import crop_largest_face
from services.model import INPUT_SIZE, get_model

NO_FACE_MESSAGE = "No clear frontal human face detected."

# Normalization for ImageNet-style input (placeholder model)
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def _confidence_level(real_prob: float, fake_prob: float) -> str:
    """Confidence: > 0.8 High, 0.5–0.8 Medium, < 0.5 Low."""
    max_prob = max(real_prob, fake_prob)
    if max_prob > 0.8:
        return "High"
    if max_prob >= 0.5:
        return "Medium"
    return "Low"


def _preprocess(face_crop: Image.Image) -> torch.Tensor:
    """Resize to INPUT_SIZE, normalize, convert to tensor (1, 3, H, W)."""
    img = face_crop.resize((INPUT_SIZE, INPUT_SIZE), Image.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0
    for c in range(3):
        arr[:, :, c] = (arr[:, :, c] - MEAN[c]) / STD[c]
    tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
    return tensor


def run_pipeline(file_bytes: bytes) -> Dict[str, Any]:
    """
    Full pipeline: load image -> detect face -> crop -> preprocess -> model.

    Uses the globally loaded model (no loading inside this function).
    Returns success dict or error dict with "error" key.
    """
    t0 = time.perf_counter()

    try:
        image = Image.open(BytesIO(file_bytes)).convert("RGB")
    except Exception as exc:
        raise ValueError("Invalid or corrupted image file.") from exc

    face_crop = crop_largest_face(image)
    if face_crop is None:
        return {"error": NO_FACE_MESSAGE}
    print("Face detected", flush=True)

    model = get_model()
    x = _preprocess(face_crop)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=-1).squeeze(0).cpu()
    real_prob = float(probs[0].item())
    fake_prob = float(probs[1].item())
    confidence_level = _confidence_level(real_prob, fake_prob)
    elapsed = time.perf_counter() - t0
    print("Inference complete", flush=True)

    return {
        "real_probability": round(real_prob, 4),
        "fake_probability": round(fake_prob, 4),
        "confidence_level": confidence_level,
        "_timing": round(elapsed, 3),
    }
