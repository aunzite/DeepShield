from functools import lru_cache
from typing import Dict, Any

from transformers import pipeline


TEXT_MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"


class HeadlineAnalysisModel:
    """
    Wrapper around a sentiment analysis transformer.

    We use sentiment intensity as a proxy for emotional tone and combine it
    with simple keyword heuristics to estimate manipulation risk.
    """

    def __init__(self) -> None:
        self.classifier = pipeline(
            "text-classification",
            model=TEXT_MODEL_NAME,
        )

    def analyze(self, text: str) -> Dict[str, Any]:
        result = self.classifier(text, truncation=True)[0]
        return {
            "label": result["label"],
            "score": float(result["score"]),
        }


@lru_cache(maxsize=1)
def get_text_model() -> HeadlineAnalysisModel:
    """
    Lazily load and cache the text model so it is only loaded once.
    """

    return HeadlineAnalysisModel()

