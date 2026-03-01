"""
Link checker: resolve redirects and return final URL, domain, status.
"""
from typing import Any, Dict
from urllib.parse import urlparse

import requests

USER_AGENT = "Mozilla/5.0 (compatible; DeepShield/1.0)"
MAX_REDIRECTS = 5
TIMEOUT = 10


def check_link(url: str) -> Dict[str, Any]:
    """
    Resolve redirects (up to MAX_REDIRECTS), return final URL, domain, status code,
    and a simple safety note (safe / unknown / suspicious based on status and HTTPS).
    """
    if not url.strip().startswith(("http://", "https://")):
        url = "https://" + url.strip()

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
            allow_redirects=True,
            max_redirects=MAX_REDIRECTS,
        )
        final_url = resp.url
        status = resp.status_code
    except requests.TooManyRedirects:
        return {
            "original_url": url,
            "final_url": None,
            "domain": None,
            "status_code": None,
            "redirect_count": MAX_REDIRECTS,
            "safety_note": "suspicious",
            "message": "Too many redirects; link may be suspicious.",
        }
    except requests.RequestException as e:
        return {
            "original_url": url,
            "final_url": None,
            "domain": None,
            "status_code": None,
            "safety_note": "unknown",
            "message": str(e),
        }

    try:
        parsed = urlparse(final_url)
        domain = parsed.netloc or None
    except Exception:
        domain = None

    if status >= 400:
        safety_note = "suspicious"
        message = f"HTTP {status}; page may be unavailable or blocked."
    elif not final_url.startswith("https://"):
        safety_note = "unknown"
        message = "Final URL is not HTTPS; consider caution."
    else:
        safety_note = "safe"
        message = "Link resolved successfully; final URL uses HTTPS."

    return {
        "original_url": url,
        "final_url": final_url,
        "domain": domain,
        "status_code": status,
        "safety_note": safety_note,
        "message": message,
    }
