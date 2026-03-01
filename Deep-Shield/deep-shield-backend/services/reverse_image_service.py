"""
Reverse image search: find where an image appears on the web.
When TINEYE_API_KEY is set, uses TinEye API. Otherwise returns manual links.
"""
import os
from typing import Any, Dict, List

# Optional: use TinEye when API key is set
TINEYE_API_KEY = os.getenv("TINEYE_API_KEY")


def reverse_search(file_bytes: bytes) -> Dict[str, Any]:
    """
    Run reverse image search. Returns either API results or manual-link stub.
    """
    if TINEYE_API_KEY:
        return _search_tineye(file_bytes)
    return _manual_links_response()


def _manual_links_response() -> Dict[str, Any]:
    return {
        "configured": False,
        "message": (
            "Reverse image search is not configured. Use the links below to "
            "check the image manually by uploading it on each site."
        ),
        "manual_links": {
            "tineye": "https://tineye.com",
            "google_images": "https://images.google.com",
        },
        "results": [],
    }


def _search_tineye(file_bytes: bytes) -> Dict[str, Any]:
    """Call TinEye REST API with image data."""
    try:
        import requests
    except ImportError:
        return _manual_links_response()

    url = "https://api.tineye.com/rest/search"
    headers = {"X-TinEye-API-Key": TINEYE_API_KEY}
    files = {"image": ("image", file_bytes, "application/octet-stream")}

    try:
        r = requests.post(url, headers=headers, files=files, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return {
            "configured": True,
            "message": "TinEye request failed. Try the manual links below.",
            "manual_links": {
                "tineye": "https://tineye.com",
                "google_images": "https://images.google.com",
            },
            "results": [],
        }

    # TinEye response: {"matches": [{"backlinks": [...], "image_url": ..., ...}], ...}
    matches = data.get("matches") or []
    results: List[Dict[str, Any]] = []
    for m in matches[:20]:
        results.append({
            "url": m.get("backlink") or m.get("url") or "",
            "title": m.get("domain", ""),
            "image_url": m.get("image_url"),
        })

    return {
        "configured": True,
        "message": f"Found {len(matches)} match(es).",
        "results": results,
        "manual_links": {
            "tineye": "https://tineye.com",
            "google_images": "https://images.google.com",
        },
    }
