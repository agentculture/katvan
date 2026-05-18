"""Fetch and parse the published ``sitemap.xml`` for the verified property.

Uses ``urllib`` from the stdlib to avoid adding an HTTP-client dependency
just for one call. Wrapped through ``_http_get`` so tests can patch a single
seam.

Handles two shapes:

* ``<urlset>`` — flat sitemap, returns its ``<loc>`` values directly.
* ``<sitemapindex>`` — index, descends one level into each child sitemap
  and concatenates their ``<loc>`` values. No deeper recursion.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen

from katvan.cli._errors import EXIT_ENV_ERROR, KatvanError

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
_USER_AGENT = "katvan-gsc/1 (+https://github.com/agentculture/katvan)"
_TIMEOUT_SECONDS = 20


@dataclass
class _Response:
    content: bytes
    status_code: int

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise URLError(f"HTTP {self.status_code}")


def _http_get(url: str) -> _Response:
    """Single seam patched in tests."""
    req = Request(url, headers={"User-Agent": _USER_AGENT})
    with urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:  # noqa: S310 - https only, see caller
        return _Response(content=resp.read(), status_code=resp.status)


def _parse_locs(body: bytes, tag: str) -> list[str]:
    root = ET.fromstring(body)
    return [
        node.text.strip()
        for node in root.findall(f"{SITEMAP_NS}{tag}/{SITEMAP_NS}loc")
        if node.text
    ]


def fetch_sitemap_urls(site_url: str) -> list[str]:
    """Return every ``<loc>`` URL referenced from ``<site_url>/sitemap.xml``.

    Descends one level for ``<sitemapindex>`` shapes. Raises
    :class:`KatvanError` (``EXIT_ENV_ERROR``) on network errors.
    """
    base = site_url.rstrip("/")
    top = f"{base}/sitemap.xml"
    try:
        resp = _http_get(top)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - normalise to KatvanError
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=f"failed to fetch {top}: {exc}",
            remediation="check the site is reachable and the URL is correct",
        ) from exc

    root = ET.fromstring(resp.content)
    local = root.tag[len(SITEMAP_NS):] if root.tag.startswith(SITEMAP_NS) else root.tag

    if local == "urlset":
        return _parse_locs(resp.content, "url")

    if local == "sitemapindex":
        child_urls: list[str] = []
        for child in _parse_locs(resp.content, "sitemap"):
            child_resp = _http_get(child)
            child_resp.raise_for_status()
            child_urls.extend(_parse_locs(child_resp.content, "url"))
        return child_urls

    raise KatvanError(
        code=EXIT_ENV_ERROR,
        message=f"unrecognised sitemap root element: {root.tag}",
        remediation="the URL must serve a <urlset> or <sitemapindex>",
    )
