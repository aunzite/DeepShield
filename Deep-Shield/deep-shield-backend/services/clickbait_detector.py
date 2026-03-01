"""
Clickbait and misinformation detection for headlines.

Weighted category system with phrase dictionaries and regex/structural patterns.
Single-pass detection, precompiled regex for performance.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

# -----------------------------------------------------------------------------
# Weighted category definitions (category_name -> weight)
# Higher weight = more manipulative signal.
# -----------------------------------------------------------------------------
CATEGORY_WEIGHTS = {
    # Core manipulation categories
    "urgency_fear": 2,
    "emotional_exaggeration": 2,
    "conspiracy_framing": 3,
    "scam_financial": 4,
    "absolute_claims": 2,
    "fake_authority": 2,
}

# -----------------------------------------------------------------------------
# Centralized buzzword dictionary by category.
# Phrases matched case-insensitively; punctuation stripped for base matching.
# -----------------------------------------------------------------------------
BUZZWORD_DICT: Dict[str, List[str]] = {
    "urgency_fear": [
        "breaking",
        "urgent",
        "alert",
        "warning",
        "critical",
        "last chance",
        "act now",
        "before it's too late",
        "don't miss",
        "dont miss",
        "running out",
        "shocking",
        "terrifying",
        "horrifying",
        "nightmare",
        "exposed",
        "finally exposed",
        "secret",
        "revealed",
        "banned",
        "censored",
    ],
    "emotional_exaggeration": [
        "you won't believe",
        "you wont believe",
        "you will not believe",
        "mind blowing",
        "mind-blowing",
        "amazing",
        "incredible",
        "unbelievable",
        "astonishing",
        "stunning",
        "epic",
        "virality",
        "viral",
        "gone wrong",
        "this will shock you",
        "just revealed",
        "no one is talking about",
        "shocking",
        "unbelievable",
        "terrifying",
    ],
    "conspiracy_framing": [
        "they don't want you to know",
        "they dont want you to know",
        "they don\u2019t want you to know",
        "hidden truth",
        "the truth about",
        "what they're hiding",
        "what theyre hiding",
        "what they\u2019re hiding",
        "cover-up",
        "cover up",
        "mainstream media won't",
        "big media",
        "wake up",
        "open your eyes",
        "wake up people",
        "no one is talking about",
        "silenced",
        "banned",
        "censored",
    ],
    "scam_financial": [
        "one simple trick",
        "one weird trick",
        "doctors hate",
        "doctors don't want you to know",
        "this one trick",
        "make money fast",
        "earn cash now",
        "guaranteed results",
        "100% guaranteed",
        "100% profit",
        "risk-free",
        "risk free",
        "free money",
        "get rich",
        "lose weight fast",
        "cure that",
        "miracle",
        "guarantees",
        "guaranteed",
        "passive income",
        "overnight",
    ],
    "absolute_claims": [
        "proves",
        "100% guaranteed",
        "completely proves",
        "experts agree",
        "changes everything",
        "destroys",
        "everyone is",
        "always",
        "never",
        "all",
        "no one",
        "every single",
        "scientists prove",
        "scientists confirm",
        "proven to",
        "undeniable",
        "irrefutable",
    ],
    "fake_authority": [
        "leading expert",
        "top doctor",
        "scientists say",
        "experts reveal",
        "study shows",
        "research proves",
        "doctors recommend",
        "official",
        "authority",
        "leading",
        "top",
        "best",
        "ultimate guide",
        "definitive guide",
        "the only",
    ],
}

# -----------------------------------------------------------------------------
# Precompiled regex patterns for structural and phrase detection.
# -----------------------------------------------------------------------------
REGEX_YOU_WONT_BELIEVE = re.compile(
    r"\byou\s+wo(n['’]t|nt)\s+believe\b", re.IGNORECASE
)
REGEX_WHAT_HAPPENED_NEXT = re.compile(
    r"\bwhat\s+happened\s+next\b", re.IGNORECASE
)
REGEX_ONE_SIMPLE_TRICK = re.compile(
    r"\bone\s+(simple|weird|easy)\s+trick\b", re.IGNORECASE
)
REGEX_ALL_CAPS = re.compile(r"\b[A-Z]{4,}\b")
REGEX_MULTI_EXCLAM = re.compile(r"!{2,}")
REGEX_MULTI_QUEST = re.compile(r"\?{2,}")

# 100% plus profit / guarantee / guaranteed
REGEX_100_COMBO = re.compile(r"100%\s*(profit|guarantee|guaranteed)?", re.IGNORECASE)
REGEX_100_GUARANTEED = re.compile(r"\b100%\s+guaranteed\b", re.IGNORECASE)
REGEX_COMPLETELY_PROVES = re.compile(r"\bcompletely\s+proves\b", re.IGNORECASE)
REGEX_EXPERTS_AGREE = re.compile(r"\bexperts?\s+agree\b", re.IGNORECASE)
REGEX_CHANGES_EVERYTHING = re.compile(r"\bchanges\s+everything\b", re.IGNORECASE)
REGEX_DESTROYS = re.compile(r"\bdestroys\b", re.IGNORECASE)
REGEX_X_DESTROYS_Y = re.compile(
    r"\b(\w+)\s+destroys\s+(\w+)\b", re.IGNORECASE
)
REGEX_X_CHANGES_EVERYTHING = re.compile(
    r"\b(\w+)\s+changes\s+everything\b", re.IGNORECASE
)
REGEX_THIS_IS_WHY = re.compile(r"\bthis\s+is\s+why\b", re.IGNORECASE)
REGEX_THE_TRUTH_ABOUT = re.compile(r"\bthe\s+truth\s+about\b", re.IGNORECASE)
REGEX_THEY_DONT_WANT = re.compile(
    r"\bthey\s+(?:don['’]t|dont)\s+want\s+(?:you\s+)?to\s+know\b", re.IGNORECASE
)

# Make $100 style patterns
REGEX_MAKE_DOLLARS = re.compile(r"\bmake\s*\$\d+", re.IGNORECASE)

REGEX_MATCHES: List[Tuple[re.Pattern, str, int]] = [
    # Emotional clickbait patterns
    (REGEX_YOU_WONT_BELIEVE, "emotional_exaggeration", 2),
    (REGEX_WHAT_HAPPENED_NEXT, "emotional_exaggeration", 2),
    (REGEX_THIS_IS_WHY, "emotional_exaggeration", 2),
    (REGEX_MULTI_EXCLAM, "emotional_exaggeration", 2),
    (REGEX_MULTI_QUEST, "emotional_exaggeration", 2),
    # Scam / financial patterns
    (REGEX_ONE_SIMPLE_TRICK, "scam_financial", CATEGORY_WEIGHTS["scam_financial"]),
    (REGEX_MAKE_DOLLARS, "scam_financial", CATEGORY_WEIGHTS["scam_financial"]),
    (REGEX_100_COMBO, "scam_financial", CATEGORY_WEIGHTS["scam_financial"]),
    # Absolute claims and fake authority
    (REGEX_100_GUARANTEED, "absolute_claims", CATEGORY_WEIGHTS["absolute_claims"]),
    (REGEX_COMPLETELY_PROVES, "absolute_claims", CATEGORY_WEIGHTS["absolute_claims"]),
    (REGEX_EXPERTS_AGREE, "fake_authority", CATEGORY_WEIGHTS["fake_authority"]),
    (REGEX_CHANGES_EVERYTHING, "absolute_claims", CATEGORY_WEIGHTS["absolute_claims"]),
    (REGEX_DESTROYS, "absolute_claims", CATEGORY_WEIGHTS["absolute_claims"]),
    (REGEX_X_DESTROYS_Y, "absolute_claims", CATEGORY_WEIGHTS["absolute_claims"]),
    (REGEX_X_CHANGES_EVERYTHING, "absolute_claims", CATEGORY_WEIGHTS["absolute_claims"]),
    # Conspiracy framing
    (REGEX_THE_TRUTH_ABOUT, "conspiracy_framing", CATEGORY_WEIGHTS["conspiracy_framing"]),
    (REGEX_THEY_DONT_WANT, "conspiracy_framing", CATEGORY_WEIGHTS["conspiracy_framing"]),
    # Formatting-based patterns
    (REGEX_ALL_CAPS, "urgency_fear", CATEGORY_WEIGHTS["urgency_fear"]),
]


@dataclass
class Match:
    """A single detected phrase with category and weight."""
    phrase: str
    category: str
    weight: int
    start: int
    end: int


def _normalize_for_matching(text: str) -> str:
    """Lowercase, normalize quotes, and strip extra whitespace; used for phrase lookup."""
    text = text.lower()
    # Normalize common “smart” quotes/apostrophes to straight equivalents
    text = (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    return " ".join(text.split())


def _strip_punctuation(s: str) -> str:
    """Remove punctuation for base phrase matching."""
    return re.sub(r"[^\w\s]", "", s)


def _normalize_apostrophe(s: str) -> str:
    """Normalize apostrophe variants for matching (including smart quotes)."""
    return (
        s.replace("\u2019", "")
        .replace("\u2018", "")
        .replace("'", "")
        .replace("`", "")
    )


def _find_phrase_matches(normalized: str, original: str) -> List[Match]:
    """
    Find all buzzword phrase matches (case-insensitive, punctuation ignored).
    Returns matches with the phrase as it appears in the original headline.
    """
    matches: List[Match] = []
    # Normalize for substring check: no punctuation, no apostrophes
    normalized_no_punct = _strip_punctuation(_normalize_apostrophe(normalized))
    lower_original = original.lower()

    for category, phrases in BUZZWORD_DICT.items():
        weight = CATEGORY_WEIGHTS.get(category, 2)
        for phrase in phrases:
            phrase_clean = _strip_punctuation(_normalize_apostrophe(phrase.lower()))
            if phrase_clean not in normalized_no_punct:
                continue
            # Find in original (case-insensitive) and capture exact span
            search_term = phrase.lower()
            idx = lower_original.find(search_term)
            if idx == -1:
                # Fallback: try apostrophe-normalized variant
                search_term = _normalize_apostrophe(phrase.lower())
                idx = lower_original.find(search_term)
                if idx == -1:
                    continue
            end = idx + len(search_term)
            if end > len(original):
                end = len(original)
            exact_phrase = original[idx:end].strip()
            if not exact_phrase:
                continue
            matches.append(
                Match(
                    phrase=exact_phrase,
                    category=category,
                    weight=weight,
                    start=idx,
                    end=end,
                )
            )

    return matches


def _find_regex_matches(original: str) -> List[Match]:
    """Run precompiled regex patterns and return matches."""
    matches: List[Match] = []
    for pattern, category, weight in REGEX_MATCHES:
        for m in pattern.finditer(original):
            phrase = m.group(0)
            matches.append(
                Match(
                    phrase=phrase,
                    category=category,
                    weight=weight,
                    start=m.start(),
                    end=m.end(),
                )
            )
    return matches


def _merge_matches(phrase_matches: List[Match], regex_matches: List[Match]) -> List[Match]:
    """
    Merge and lightly deduplicate matches while preserving exact positions.

    We deduplicate only identical (phrase, category, start, end) tuples to avoid
    double-counting the same span from different detection passes.
    """
    seen: set = set()
    out: List[Match] = []
    for m in phrase_matches + regex_matches:
        key = (m.phrase.lower().strip(), m.category, m.start, m.end)
        if key in seen:
            continue
        seen.add(key)
        out.append(m)
    return out


def detect_clickbait(headline: str) -> dict:
    """
    Run full clickbait detection on a headline.
    Normalizes (lowercase, strip whitespace), runs phrase + regex detection,
    merges matches, computes score and risk level.
    """
    normalized = _normalize_for_matching(headline)
    original_stripped = " ".join(headline.split())

    phrase_matches = _find_phrase_matches(normalized, original_stripped)
    regex_matches = _find_regex_matches(original_stripped)
    all_matches = _merge_matches(phrase_matches, regex_matches)

    # Base score from individual matches
    total_score = sum(m.weight for m in all_matches)

    # ------------------------------------------------------------------
    # Non-linear compound amplification rules
    # ------------------------------------------------------------------
    has_conspiracy = any(m.category == "conspiracy_framing" for m in all_matches)
    has_financial = any(m.category == "scam_financial" for m in all_matches)
    conspiracy_count = sum(1 for m in all_matches if m.category == "conspiracy_framing")

    has_all_caps = REGEX_ALL_CAPS.search(original_stripped) is not None
    has_multi_excl = REGEX_MULTI_EXCLAM.search(original_stripped) is not None

    has_100 = "100%" in original_stripped
    has_guarantee_word = bool(
        re.search(r"\bguarantee(?:d|s)?\b", original_stripped, flags=re.IGNORECASE)
    )

    # Conspiracy AND Financial -> strong bonus
    if has_conspiracy and has_financial:
        total_score += 4

    # 2+ distinct conspiracy phrases
    if conspiracy_count >= 2:
        total_score += 3

    # ALL CAPS + multiple exclamation marks
    if has_all_caps and has_multi_excl:
        total_score += 2

    # 100% + guarantees/guaranteed
    if has_100 and has_guarantee_word:
        total_score += 3

    # Updated risk thresholds:
    # 0–2 = Low, 3–6 = Moderate, 7–11 = High, 12+ = Extreme
    if total_score <= 2:
        risk_level = "Low"
    elif total_score <= 6:
        risk_level = "Moderate"
    elif total_score <= 11:
        risk_level = "High"
    else:
        risk_level = "Extreme"

    category_breakdown: Dict[str, int] = {}
    category_display_names = {
        "urgency_fear": "Urgency / Fear",
        "emotional_exaggeration": "Emotional exaggeration",
        "conspiracy_framing": "Conspiracy framing",
        "scam_financial": "Scam / Financial",
        "absolute_claims": "Absolute claims",
        "fake_authority": "Fake authority",
    }
    for m in all_matches:
        display_name = category_display_names.get(m.category, m.category)
        category_breakdown[display_name] = category_breakdown.get(display_name, 0) + m.weight

    return {
        "score": total_score,
        "risk_level": risk_level,
        "matches": [
            {
                "phrase": m.phrase,
                "category": m.category,
                "weight": m.weight,
                "start": m.start,
                "end": m.end,
            }
            for m in all_matches
        ],
        "category_breakdown": category_breakdown,
    }
