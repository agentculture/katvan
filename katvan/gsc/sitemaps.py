"""``katvan gsc sitemaps`` — list submitted sitemaps and their status."""
from __future__ import annotations

from typing import Any


def _to_int(value: Any) -> int:
    """GSC returns numeric fields as strings; coerce defensively."""
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalise_contents(raw: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in raw or []:
        out.append({
            "type": item.get("type", ""),
            "submitted": _to_int(item.get("submitted")),
            "indexed": _to_int(item.get("indexed")),
        })
    return out


def list_sitemaps(client: Any, *, site_url: str) -> list[dict[str, Any]]:
    """Return a normalised list of submitted sitemaps for ``site_url``.

    Each row contains: ``path``, ``last_submitted``, ``last_downloaded``,
    ``is_pending``, ``is_sitemaps_index``, ``type``, ``errors``, ``warnings``,
    ``contents``.
    """
    # num_retries: googleapiclient retries with exponential backoff on
    # 5xx and 429 responses. Three attempts matches the spec.
    resp = client.sitemaps().list(siteUrl=site_url).execute(num_retries=3)
    rows: list[dict[str, Any]] = []
    for item in resp.get("sitemap", []) or []:
        rows.append({
            "path": item.get("path", ""),
            "last_submitted": item.get("lastSubmitted", ""),
            "last_downloaded": item.get("lastDownloaded", ""),
            "is_pending": bool(item.get("isPending", False)),
            "is_sitemaps_index": bool(item.get("isSitemapsIndex", False)),
            "type": item.get("type", ""),
            "errors": _to_int(item.get("errors")),
            "warnings": _to_int(item.get("warnings")),
            "contents": _normalise_contents(item.get("contents")),
        })
    return rows
