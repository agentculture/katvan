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

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.error import URLError
from urllib.request import Request, urlopen

from defusedxml import ElementTree as ET

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element  # nosec B405 - typing only; runtime parsing uses defusedxml

from katvan._errors import EXIT_ENV_ERROR, KatvanError

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
    with urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:  # nosec B310 - scheme guarded in fetch_sitemap_urls
        return _Response(content=resp.read(), status_code=resp.status)


def _fetch_or_raise(url: str) -> bytes:
    """Fetch URL with KatvanError translation on any failure."""
    try:
        resp = _http_get(url)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - normalise to KatvanError
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=f"failed to fetch {url}: {exc}",
            remediation="check the URL is reachable",
        ) from exc
    return resp.content


def _fetch_and_parse(url: str) -> Element:
    body = _fetch_or_raise(url)
    try:
        return ET.fromstring(body)
    except ET.ParseError as exc:
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=f"failed to parse sitemap XML from {url}: {exc}",
            remediation="check the URL serves a well-formed sitemap",
        ) from exc


def _parse_locs(root: Element, tag: str) -> list[str]:
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
    if not top.startswith(("http://", "https://")):
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=f"site URL must use http or https: {top}",
            remediation="set KATVAN_GSC_SITE to a valid http(s) URL",
        )

    root = _fetch_and_parse(top)
    local = root.tag[len(SITEMAP_NS):] if root.tag.startswith(SITEMAP_NS) else root.tag

    if local == "urlset":
        return _parse_locs(root, "url")

    if local == "sitemapindex":
        child_urls: list[str] = []
        for child in _parse_locs(root, "sitemap"):
            child_root = _fetch_and_parse(child)
            child_urls.extend(_parse_locs(child_root, "url"))
        return child_urls

    raise KatvanError(
        code=EXIT_ENV_ERROR,
        message=f"unrecognised sitemap root element: {root.tag}",
        remediation="the URL must serve a <urlset> or <sitemapindex>",
    )
