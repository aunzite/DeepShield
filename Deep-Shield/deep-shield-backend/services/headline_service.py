"""
Headline analysis: rule-based manipulation/clickbait scoring (demo / hackathon MVP).

- Trigger words, caps ratio, punctuation intensity, emotional keywords.
- No transformers, no model downloads. Pure rules + lightweight logic.
"""

import re
from typing import Any, Dict, List

# Trigger words (case-insensitive)
TRIGGER_WORDS = [
    "breaking", "shocking", "secret", "exposed", "revealed", "urgent",
    "you won't believe", "mind blowing", "doctors hate", "one simple trick",
    "they don't want you to know", "the truth about", "what happened next",
]

# Emotional / sensational
EMOTIONAL_WORDS = [
    "shocking", "terrifying", "unbelievable", "astonishing", "stunning",
    "horrifying", "incredible", "epic", "viral", "gone wrong",
]

# Precompiled for speed
REGEX_ALL_CAPS = re.compile(r"\b[A-Z]{4,}\b")
REGEX_EXCLAM = re.compile(r"!+")
REGEX_MULTI_EXCLAM = re.compile(r"!{2,}")


def _caps_ratio(text: str) -> float:
    """Proportion of letters that are uppercase."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters)


def _punctuation_intensity(text: str) -> float:
    """Exclamation marks per character (normalized)."""
    if not text:
        return 0.0
    exclam = text.count("!")
    return min(1.0, exclam / max(1, len(text) * 0.1))


def _count_trigger_matches(text: str) -> List[str]:
    """Return list of matched trigger phrases (lowercase for display)."""
    lower = text.lower()
    found = []
    for phrase in TRIGGER_WORDS:
        if phrase in lower:
            found.append(phrase)
    return found


def _count_emotional_matches(text: str) -> List[str]:
    """Return list of matched emotional words."""
    lower = text.lower()
    words = set(re.findall(r"\b\w+\b", lower))
    return [w for w in EMOTIONAL_WORDS if w in words]


def analyze_headline(headline: str) -> Dict[str, Any]:
    """
    Rule-based headline manipulation score.

    Returns: manipulation_score (0-1), risk_level, flagged_phrases, summary.
    Also returns clickbait_score (int), matches, category_breakdown for API compatibility.
    """
    text = " ".join(headline.strip().split())
    if not text:
        return {
            "manipulation_score": 0.0,
            "risk_level": "Low",
            "flagged_phrases": [],
            "summary": "No headline provided.",
            "clickbait_score": 0,
            "matches": [],
            "category_breakdown": {},
        }

    triggers = _count_trigger_matches(text)
    emotional = _count_emotional_matches(text)
    caps = _caps_ratio(text)
    punct = _punctuation_intensity(text)
    all_caps_words = REGEX_ALL_CAPS.findall(text)
    multi_exclam = REGEX_MULTI_EXCLAM.search(text) is not None

    # Score components (0-1 each, then combine)
    trigger_score = min(1.0, len(triggers) * 0.25)
    emotional_score = min(1.0, len(emotional) * 0.2)
    caps_score = min(1.0, caps * 2.0)
    punct_score = min(1.0, punct * 2.0)
    all_caps_bonus = 0.2 if all_caps_words else 0.0
    exclam_bonus = 0.15 if multi_exclam else 0.0

    manipulation_score = (
        0.30 * trigger_score
        + 0.25 * emotional_score
        + 0.15 * caps_score
        + 0.15 * punct_score
        + all_caps_bonus
        + exclam_bonus
    )
    manipulation_score = max(0.0, min(1.0, manipulation_score))

    if manipulation_score >= 0.7:
        risk_level = "High"
    elif manipulation_score >= 0.4:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    flagged_phrases = list(dict.fromkeys(triggers + emotional + all_caps_words[:5]))

    # Summary (rule-based only)
    parts = []
    if triggers:
        parts.append(f"Matched trigger phrases: {', '.join(triggers[:5])}.")
    if emotional:
        parts.append(f"Emotional language: {', '.join(emotional[:5])}.")
    if caps > 0.3:
        parts.append("High proportion of capital letters.")
    if multi_exclam or text.count("!") >= 2:
        parts.append("Excessive exclamation marks.")
    if risk_level == "High":
        parts.append("High manipulation risk: attention-grabbing or sensational language.")
    elif risk_level == "Medium":
        parts.append("Moderate risk: some clickbait-style elements.")
    else:
        parts.append("Low risk: no strong manipulation signals. Always verify sources.")
    summary = " ".join(parts) if parts else "Headline analyzed with rule-based scanner."

    # Matches for API compatibility (list of dicts with phrase, category)
    matches = []
    for p in triggers:
        matches.append({"phrase": p, "category": "trigger"})
    for p in emotional:
        if p not in triggers:
            matches.append({"phrase": p, "category": "emotional"})
    for p in all_caps_words[:5]:
        matches.append({"phrase": p, "category": "all_caps"})

    category_breakdown = {}
    if triggers:
        category_breakdown["Trigger phrases"] = len(triggers)
    if emotional:
        category_breakdown["Emotional"] = len(emotional)
    if all_caps_words:
        category_breakdown["All caps"] = len(all_caps_words)

    clickbait_score = int(manipulation_score * 10)

    return {
        "manipulation_score": round(manipulation_score, 4),
        "risk_level": risk_level,
        "flagged_phrases": flagged_phrases,
        "summary": summary,
        "clickbait_score": min(10, clickbait_score),
        "matches": matches,
        "category_breakdown": category_breakdown,
    }
