"""
Lightweight deepfake classifier (PLACEHOLDER).

Small PyTorch CNN with randomly initialized weights.
Replace with real deepfake weights when available.
Runs on CPU only. Instantiate ONCE at app startup.
"""

import torch
import torch.nn as nn
from typing import Optional

# Input size for the placeholder model
INPUT_SIZE = 128
NUM_CLASSES = 2  # real, fake


class DeepfakeCNN(nn.Module):
    """
    Placeholder: 3 conv layers + ReLU + MaxPool + FC -> 2 logits (real vs fake).
    Weights are randomly initialized. Replace with real deepfake weights later.
    """

    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=5, stride=2, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )
        # 128->64->32->16->8->4; 4*4*64 = 1024
        self.classifier = nn.Linear(4 * 4 * 64, NUM_CLASSES)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


_model: Optional[DeepfakeCNN] = None


def init_model() -> DeepfakeCNN:
    """Instantiate model once at startup. CPU only, eval mode."""
    global _model
    if _model is not None:
        return _model
    _model = DeepfakeCNN()
    _model.to("cpu")
    _model.eval()
    return _model


def get_model() -> DeepfakeCNN:
    """Return the globally loaded model. Call init_model() at startup first."""
    global _model
    if _model is None:
        init_model()
    assert _model is not None
    return _model
