from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, cast

import httpx
import llm

logger = logging.getLogger(__name__)

DEFAULT_CACHE_TIMEOUT = 3600


def fetch_cached_json(
    url: str,
    path: str | Path,
    cache_timeout: float = DEFAULT_CACHE_TIMEOUT,
    **kwargs: Any,
) -> dict[str, Any]:
    """Fetch JSON from *url* and cache it at *path* for *cache_timeout* seconds.

    If the cached file exists and is younger than *cache_timeout*, its contents
    are returned directly. Otherwise a fresh request is attempted. When the
    request fails, a stale cache is used as a fallback. If no cache exists,
    an empty ``{"data": []}`` payload is returned.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.is_file() and (time.time() - path.stat().st_mtime) < cache_timeout:
        logger.debug("Cache hit for %s (%s)", url, path)
        try:
            with path.open(encoding="utf-8") as f:
                return cast(dict[str, Any], json.load(f))
        except json.JSONDecodeError as exc:
            logger.warning("Corrupt cache file %s: %s", path, exc)

    key = llm.get_key("", "moonshot", "MOONSHOT_KEY")
    if not key:
        logger.debug("No Moonshot API key configured; returning fallback catalog")
        return _fallback_or_stale(path)

    headers = {"Authorization": f"Bearer {key}"}

    try:
        response = httpx.get(
            url, headers=headers, follow_redirects=True, timeout=1.5, **kwargs
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("Moonshot API returned %s for %s", exc.response.status_code, url)
        return _fallback_or_stale(path)
    except httpx.RequestError as exc:
        logger.warning("Moonshot API request failed for %s: %s", url, exc)
        return _fallback_or_stale(path)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON from Moonshot API: %s", exc)
        return _fallback_or_stale(path)

    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError as exc:
        logger.warning("Could not write cache file %s: %s", path, exc)

    return cast(dict[str, Any], data)


def _fallback_or_stale(path: Path) -> dict[str, Any]:
    """Return stale cache contents or an empty data payload."""
    if path.is_file():
        try:
            with path.open(encoding="utf-8") as f:
                return cast(dict[str, Any], json.load(f))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read stale cache %s: %s", path, exc)
    return {"data": []}
