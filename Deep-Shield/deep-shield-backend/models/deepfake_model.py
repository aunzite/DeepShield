"""
Deepfake detection model.

Loads a pretrained classifier trained on real vs fake (deepfake) face images.
Input: face crop, resized and normalized to model requirements (e.g. 224x224).
Output: real_probability, fake_probability.
"""

from functools import lru_cache
from typing import Tuple

import torch
from PIL import Image

# HuggingFace model trained for deepfake vs real image classification.
# Uses ViT 224x224; trained on real/fake face datasets.
DEEPFAKE_MODEL_NAME = "dima806/deepfake_vs_real_image_detection"


class DeepfakeModel:
    """
    Wrapper around a pretrained deepfake detection classifier.

    Expects a cropped face image. Runs on CPU for production safety.
    """

    def __init__(self) -> None:
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        self.device = torch.device("cpu")
        self.processor = AutoImageProcessor.from_pretrained(DEEPFAKE_MODEL_NAME)
        self.model = AutoModelForImageClassification.from_pretrained(DEEPFAKE_MODEL_NAME)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, face_image: Image.Image) -> Tuple[float, float]:
        """
        Run inference on a single face crop (PIL Image, any size; will be resized by processor).

        Returns:
            (real_probability, fake_probability) summing to 1.0.
        """
        inputs = self.processor(images=face_image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).squeeze(0).cpu()

        # Map label indices to real / fake
        id2label = self.model.config.id2label
        real_prob = 0.0
        fake_prob = 0.0
        for idx, p in enumerate(probs.tolist()):
            label = id2label.get(idx, "").lower()
            if "real" in label or label == "realism":
                real_prob += p
            else:
                fake_prob += p
        # If we only have two classes, ensure they sum to 1
        if real_prob == 0.0 and fake_prob == 0.0:
            real_prob = float(probs[0].item())
            fake_prob = float(probs[1].item()) if probs.shape[0] > 1 else 1.0 - real_prob
        total = real_prob + fake_prob
        if total > 0:
            real_prob /= total
            fake_prob /= total
        real_prob = max(0.0, min(1.0, real_prob))
        fake_prob = max(0.0, min(1.0, fake_prob))
        return real_prob, fake_prob


@lru_cache(maxsize=1)
def get_deepfake_model() -> DeepfakeModel:
    """Lazily load and cache the deepfake model once per process."""
    return DeepfakeModel()
