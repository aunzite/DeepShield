"""
Headline analysis: clickbait/misinformation detection + sentiment.

Extends the weighted clickbait detector with sentiment from the text model
and returns a unified response for the API.
"""

from typing import Any, Dict, List

from models.text_model import get_text_model
from services.clickbait_detector import detect_clickbait


def _risk_level_from_manipulation_score(score: float) -> str:
    """Map 0-1 manipulation score to risk level (for backward compatibility)."""
    if score >= 0.75:
        return "High"
    if score >= 0.45:
        return "Moderate"
    if score >= 0.2:
        return "Low"
    return "Low"


def analyze_headline(headline: str) -> Dict[str, Any]:
    """
    Analyze a news or social media headline for clickbait and manipulation.

    - Runs weighted clickbait detection (categories, regex, structural patterns).
    - Optionally uses sentiment model for tone in summary.
    - Returns score, risk level, matches, category breakdown, and summary.
    """
    # Normalize input: strip extra whitespace
    headline_clean = " ".join(headline.strip().split())
    if not headline_clean:
        return {
            "clickbait_score": 0,
            "risk_level": "Low",
            "manipulation_score": 0.0,
            "flagged_phrases": [],
            "matches": [],
            "category_breakdown": {},
            "summary": "No headline provided.",
        }

    # Run clickbait detection (single pass, precompiled patterns)
    detection = detect_clickbait(headline_clean)
    score = detection["score"]
    risk_level = detection["risk_level"]
    matches = detection["matches"]
    category_breakdown = detection["category_breakdown"]

    # Backward compatibility: manipulation_score 0-1 from clickbait score (cap at 10 for scale)
    manipulation_score = min(1.0, score / 10.0)
    flagged_phrases = [m["phrase"] for m in matches]

    # Optional: sentiment for summary tone (keep existing behavior)
    try:
        text_model = get_text_model()
        sentiment = text_model.analyze(headline_clean)
        tone = "neutral"
        if sentiment["label"].upper() == "POSITIVE":
            tone = "positive"
        elif sentiment["label"].upper() == "NEGATIVE":
            tone = "negative"
    except Exception:
        tone = "neutral"

    # Build summary
    parts = [f"The headline has a {tone} emotional tone."]
    if matches:
        parts.append(
            f"Clickbait score: {score} ({risk_level} risk). "
            "Matched phrases are often used to drive clicks or exaggerate."
        )
        if category_breakdown:
            breakdown_str = ", ".join(f"{k}: {v}" for k, v in sorted(category_breakdown.items()))
            parts.append(f"Breakdown: {breakdown_str}.")
    else:
        parts.append(
            "No clickbait patterns detected. That doesn't mean the headline is "
            "trustworthy—always verify the source and read beyond the title."
        )
    if risk_level == "Extreme":
        parts.append(
            "Extreme risk: multiple manipulative patterns. Fact-check before sharing."
        )
    elif risk_level == "High":
        parts.append(
            "High manipulation risk: language designed to trigger curiosity or emotion."
        )
    elif risk_level == "Moderate":
        parts.append(
            "Moderate risk: some attention-grabbing elements. Read the full article."
        )
    else:
        parts.append("Low risk: no obvious clickbait patterns. Verify sources when it matters.")

    summary = " ".join(parts)

    return {
        "clickbait_score": score,
        "risk_level": risk_level,
        "manipulation_score": manipulation_score,
        "flagged_phrases": flagged_phrases,
        "matches": matches,
        "category_breakdown": category_breakdown,
        "summary": summary,
    }
