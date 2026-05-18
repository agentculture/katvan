"""``katvan gsc doctor`` — composite indexing-health audit.

Walks every ``<loc>`` in the published sitemap.xml, inspects each URL,
groups failures into problem classes, returns a structured report.

Problem classes:

* ``not_indexed``        — ``indexStatusResult.verdict`` is not ``PASS``.
* ``crawl_errors``       — ``pageFetchState`` is not ``SUCCESSFUL``.
* ``mobile_issues``      — ``mobileUsabilityResult.verdict`` is not ``PASS``
                           (only when the field is present in the response).
* ``canonical_mismatch`` — ``googleCanonical`` and ``userCanonical`` are
                           both non-empty and differ.

The exit-code convention (``0`` for clean, ``1`` for any problem) is enforced
by the CLI wrapper in :mod:`katvan.cli._commands.gsc`, not here.
"""
from __future__ import annotations

from typing import Any

from katvan.gsc._sitemap_fetch import fetch_sitemap_urls
from katvan.gsc.inspect import inspect_url


def _classify(result: dict[str, Any]) -> list[str]:
    classes: list[str] = []
    if result.get("verdict") != "PASS":
        classes.append("not_indexed")
    if result.get("page_fetch_state") and result.get("page_fetch_state") != "SUCCESSFUL":
        classes.append("crawl_errors")
    mobile = result.get("mobile_usability")
    if mobile and mobile != "PASS":
        classes.append("mobile_issues")
    g = result.get("google_canonical") or ""
    u = result.get("user_canonical") or ""
    if g and u and g != u:
        classes.append("canonical_mismatch")
    return classes


def run_doctor(client: Any, *, site_url: str) -> dict[str, Any]:
    """Inspect every sitemap URL; return a problem report keyed by URL.

    The report shape::

        {
          "site": "<site_url>",
          "summary": {"total": N, "problems": M, "errors": E, "by_class": {...}},
          "problems": [
            {"url": "...", "classes": [...], "inspection": {<full inspect_url result>}},
            ...
          ],
          "errors": [
            {"url": "...", "error": "<ExceptionType: message>"},
            ...
          ],
        }
    """
    urls = fetch_sitemap_urls(site_url)
    by_class_counts: dict[str, int] = {}
    problems: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for url in urls:
        try:
            result = inspect_url(client, url=url, site_url=site_url)
        except Exception as exc:  # noqa: BLE001 — partial-report resilience
            # Quota exhaustion or transient errors mid-walk shouldn't lose
            # what we've already collected. Stash the failure and continue;
            # the CLI wrapper exits non-zero whenever ``errors`` is non-empty.
            errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
            continue
        classes = _classify(result)
        if not classes:
            continue
        for c in classes:
            by_class_counts[c] = by_class_counts.get(c, 0) + 1
        problems.append({"url": url, "classes": classes, "inspection": result})
    return {
        "site": site_url,
        "summary": {
            "total": len(urls),
            "problems": len(problems),
            "errors": len(errors),
            "by_class": by_class_counts,
        },
        "problems": problems,
        "errors": errors,
    }
