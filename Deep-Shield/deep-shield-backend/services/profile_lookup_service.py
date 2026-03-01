"""
Profile URL lookup: fetch public page and extract Open Graph + location hints.
"""
import re
from typing import Any, Dict, List

import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None  # type: ignore

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
)
TIMEOUT = 15


def lookup_profile(url: str) -> Dict[str, Any]:
    """
    Fetch profile URL and extract og:title, og:description, og:image,
    and any location-like hints from the page.
    """
    if not url.strip().startswith(("http://", "https://")):
        url = "https://" + url.strip()

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        resp.raise_for_status()
        html = resp.text
        final_url = resp.url
    except requests.RequestException as e:
        return {
            "profile_url": url,
            "display_name": None,
            "description": None,
            "location_hints": [],
            "profile_image_url": None,
            "error": str(e),
            "disclaimer": "This tool only uses publicly visible data. Some sites block automated access.",
        }

    display_name = None
    description = None
    profile_image_url = None
    location_hints: List[str] = []

    # Open Graph
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        for meta in soup.find_all("meta", property=re.compile(r"^og:")):
            prop = meta.get("property", "")
            content = meta.get("content", "").strip()
            if prop == "og:title" and content:
                display_name = content
            elif prop == "og:description" and content:
                description = content
            elif prop == "og:image" and content:
                profile_image_url = content if content.startswith("http") else None

        # Try to find location in meta or common selectors
        for meta in soup.find_all("meta", attrs={"name": re.compile(r"location|place|geo", re.I)}):
            content = (meta.get("content") or "").strip()
            if content and content not in location_hints:
                location_hints.append(content)

        # Common bio/location patterns in JSON-LD or meta
        if description and _looks_like_location(description):
            # Don't add full description as location; look for snippets
            pass
        # Simple heuristic: "Location: X" or "📍 X" in description
        if description:
            loc_match = re.search(r"(?:location|from|based in|📍|🏠)\s*[:\-]?\s*([^.,\n]+)", description, re.I)
            if loc_match:
                hint = loc_match.group(1).strip()
                if hint and len(hint) < 100 and hint not in location_hints:
                    location_hints.append(hint)

    # Fallback: regex on raw HTML for og tags if no BeautifulSoup
    if display_name is None or description is None:
        og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        og_desc = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        og_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if og_title and display_name is None:
            display_name = og_title.group(1).strip()
        if og_desc and description is None:
            description = og_desc.group(1).strip()
        if og_img and profile_image_url is None:
            profile_image_url = og_img.group(1).strip()
            if not profile_image_url.startswith("http"):
                profile_image_url = None

    return {
        "profile_url": final_url,
        "display_name": display_name,
        "description": description,
        "location_hints": location_hints[:10],
        "profile_image_url": profile_image_url,
        "disclaimer": "This tool only uses publicly visible data. Some sites block automated access.",
    }


def _looks_like_location(text: str) -> bool:
    """Simple heuristic: text looks like a place name (short, no URL)."""
    if len(text) > 150 or "http" in text.lower():
        return False
    return bool(re.search(r"\b(?:city|state|country|location|from|based)\b", text, re.I))
