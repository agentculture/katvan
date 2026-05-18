"""``katvan gsc inspect <url>`` — per-URL indexing inspection."""
from __future__ import annotations

from typing import Any

from katvan._errors import EXIT_USER_ERROR, KatvanError


def inspect_url(client: Any, *, url: str, site_url: str) -> dict[str, Any]:
    """Inspect ``url`` against ``site_url``; return a normalised result.

    Raises :class:`KatvanError` if ``url`` is not under ``site_url`` — that's
    a cheap pre-flight failure for typos.
    """
    if not url.startswith(site_url):
        raise KatvanError(
            code=EXIT_USER_ERROR,
            message=f"URL '{url}' is outside the verified property '{site_url}'",
            remediation="pass a URL that starts with the verified site URL",
        )

    resp = (
        client.urlInspection()
        .index()
        .inspect(body={"inspectionUrl": url, "siteUrl": site_url})
        # num_retries: googleapiclient retries with exponential backoff on
        # 5xx and 429 responses. Three attempts matches the spec.
        .execute(num_retries=3)
    )
    result = resp.get("inspectionResult", {}) or {}
    idx = result.get("indexStatusResult", {}) or {}
    mob = result.get("mobileUsabilityResult", {}) or {}
    rich = result.get("richResultsResult", {}) or {}

    return {
        "url": url,
        "verdict": idx.get("verdict", ""),
        "coverage_state": idx.get("coverageState", ""),
        "last_crawl_time": idx.get("lastCrawlTime", ""),
        "robots_txt_state": idx.get("robotsTxtState", ""),
        "page_fetch_state": idx.get("pageFetchState", ""),
        "google_canonical": idx.get("googleCanonical", ""),
        "user_canonical": idx.get("userCanonical", ""),
        "mobile_usability": mob.get("verdict", ""),
        "rich_results": rich.get("verdict", ""),
    }
