# Google Search Console integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify `culture.dev` with Google Search Console and ship a read-only `katvan gsc` CLI verb (subcommands: `sitemaps`, `inspect`, `doctor`) that surfaces indexing-health data so agents can read GSC issues without going through the web UI.

**Architecture:** New `katvan/gsc/` package holds API client + subcommand logic + formatters. CLI wiring follows the existing `katvan/cli/_commands/*.py` pattern with one file per verb; `gsc.py` uses argparse subparsers to expose three subcommands. Service-account auth via `KATVAN_GSC_CREDENTIALS` env var, scoped read-only.

**Tech Stack:** Python 3.12, argparse, `google-api-python-client`, `google-auth`, pytest with mocks (no live API calls in tests), `uv` for dep management.

**Spec:** [`docs/superpowers/specs/2026-05-18-gsc-integration-design.md`](../specs/2026-05-18-gsc-integration-design.md)

**Issue:** [agentculture/katvan#26](https://github.com/agentculture/katvan/issues/26)

**Working branch:** `feat/gsc-integration-spec` (spec already committed there — continue on it, or rebase into a new feature branch if preferred).

---

## Task 1: Add dependencies and scaffold gsc package

**Files:**
- Modify: `pyproject.toml`
- Create: `katvan/gsc/__init__.py`
- Create: `tests/unit/test_gsc_scaffold.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/test_gsc_scaffold.py`:

```python
"""Scaffold sanity: the gsc package imports and exposes its public surface."""
from __future__ import annotations


def test_gsc_package_imports() -> None:
    import katvan.gsc  # noqa: F401


def test_googleapiclient_dependency_available() -> None:
    import googleapiclient.discovery  # noqa: F401
    from google.oauth2 import service_account  # noqa: F401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_gsc_scaffold.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'katvan.gsc'` and/or `googleapiclient` import error.

- [ ] **Step 3: Add runtime dependencies via uv**

Run: `uv add google-api-python-client google-auth`

Expected: `pyproject.toml` `dependencies` list now contains both packages with version constraints; `uv.lock` updates.

- [ ] **Step 4: Create the package directory**

Create `katvan/gsc/__init__.py`:

```python
"""Google Search Console integration: read-only indexing-health verbs.

Submodules:
    client     — service-account auth + thin GSC API wrapper.
    sitemaps   — ``katvan gsc sitemaps`` logic.
    inspect    — ``katvan gsc inspect <url>`` logic.
    doctor     — ``katvan gsc doctor`` composite.
    formatters — text + JSON output helpers shared across subcommands.
"""

from __future__ import annotations
```

- [ ] **Step 5: Run tests to verify pass**

Run: `uv run pytest tests/unit/test_gsc_scaffold.py -v`
Expected: 2 PASSED.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock katvan/gsc/__init__.py tests/unit/test_gsc_scaffold.py
git commit -m "feat(gsc): scaffold package and add google-api-python-client dep"
```

---

## Task 2: Service-account client wrapper

**Files:**
- Create: `katvan/gsc/client.py`
- Create: `tests/unit/test_gsc_client.py`

The client wrapper owns auth, exposes one builder function returning a `googleapiclient` `Resource`, and centralises error translation (missing env var, 401/403 → `KatvanError`).

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_gsc_client.py`:

```python
"""Tests for :mod:`katvan.gsc.client`."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from katvan.cli._errors import EXIT_ENV_ERROR, KatvanError
from katvan.gsc.client import (
    DEFAULT_SITE_URL,
    SCOPE,
    build_client,
    site_url,
)


def test_default_site_url_is_culture_dev() -> None:
    assert DEFAULT_SITE_URL == "https://culture.dev/"


def test_scope_is_readonly() -> None:
    assert SCOPE == "https://www.googleapis.com/auth/webmasters.readonly"


def test_site_url_uses_env_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KATVAN_GSC_SITE", "https://staging.example.com/")
    assert site_url() == "https://staging.example.com/"


def test_site_url_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KATVAN_GSC_SITE", raising=False)
    assert site_url() == DEFAULT_SITE_URL


def test_build_client_raises_when_credentials_env_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("KATVAN_GSC_CREDENTIALS", raising=False)
    with pytest.raises(KatvanError) as exc:
        build_client()
    assert exc.value.code == EXIT_ENV_ERROR
    assert "KATVAN_GSC_CREDENTIALS" in exc.value.message
    assert "docs/gsc-setup.md" in exc.value.remediation


def test_build_client_raises_when_credentials_file_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bogus = tmp_path / "nope.json"
    monkeypatch.setenv("KATVAN_GSC_CREDENTIALS", str(bogus))
    with pytest.raises(KatvanError) as exc:
        build_client()
    assert exc.value.code == EXIT_ENV_ERROR
    assert str(bogus) in exc.value.message


def test_build_client_loads_credentials_and_builds_resource(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    creds_path = tmp_path / "sa.json"
    creds_path.write_text("{}")  # contents don't matter — we mock the loader
    monkeypatch.setenv("KATVAN_GSC_CREDENTIALS", str(creds_path))

    sentinel_creds = object()
    sentinel_resource = object()
    with patch(
        "katvan.gsc.client.service_account.Credentials.from_service_account_file",
        return_value=sentinel_creds,
    ) as load, patch(
        "katvan.gsc.client.discovery.build", return_value=sentinel_resource
    ) as build:
        result = build_client()

    assert result is sentinel_resource
    load.assert_called_once_with(str(creds_path), scopes=[SCOPE])
    build.assert_called_once()
    args, kwargs = build.call_args
    assert args[:2] == ("searchconsole", "v1")
    assert kwargs.get("credentials") is sentinel_creds
    assert kwargs.get("cache_discovery") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_gsc_client.py -v`
Expected: All FAIL — `katvan.gsc.client` does not exist yet.

- [ ] **Step 3: Implement the client wrapper**

Create `katvan/gsc/client.py`:

```python
"""Service-account auth and thin GSC API client wrapper.

Single source of truth for:

* The OAuth scope (read-only).
* Credentials loading from ``$KATVAN_GSC_CREDENTIALS``.
* The verified-property URL (``$KATVAN_GSC_SITE`` or the culture.dev default).
* Building the ``searchconsole v1`` discovery client.

All env-var problems raise :class:`KatvanError` with ``EXIT_ENV_ERROR`` so the
top-level dispatcher prints a clean ``error: … / hint: …`` pair instead of a
Python traceback.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient import discovery

from katvan.cli._errors import EXIT_ENV_ERROR, KatvanError

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
DEFAULT_SITE_URL = "https://culture.dev/"
_SETUP_HINT = "see docs/gsc-setup.md for the one-time setup steps"


def site_url() -> str:
    """Return the verified-property URL (env override or default)."""
    return os.environ.get("KATVAN_GSC_SITE", DEFAULT_SITE_URL)


def build_client() -> Any:
    """Return a ``googleapiclient`` Resource for the Search Console v1 API.

    Raises :class:`KatvanError` (``EXIT_ENV_ERROR``) when the credentials env
    var is unset or the file is unreadable.
    """
    path_str = os.environ.get("KATVAN_GSC_CREDENTIALS")
    if not path_str:
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message="KATVAN_GSC_CREDENTIALS env var is not set",
            remediation=_SETUP_HINT,
        )
    if not Path(path_str).is_file():
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=f"KATVAN_GSC_CREDENTIALS file not found: {path_str}",
            remediation=_SETUP_HINT,
        )
    creds = service_account.Credentials.from_service_account_file(
        path_str, scopes=[SCOPE]
    )
    return discovery.build(
        "searchconsole",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_gsc_client.py -v`
Expected: 7 PASSED.

- [ ] **Step 5: Commit**

```bash
git add katvan/gsc/client.py tests/unit/test_gsc_client.py
git commit -m "feat(gsc): service-account client wrapper with env-var auth"
```

---

## Task 3: Sitemap fetcher with index-descent

**Files:**
- Create: `katvan/gsc/_sitemap_fetch.py`
- Create: `tests/unit/test_gsc_sitemap_fetch.py`
- Create: `tests/fixtures/gsc/sitemap-flat.xml`
- Create: `tests/fixtures/gsc/sitemap-index.xml`
- Create: `tests/fixtures/gsc/sitemap-leaf-a.xml`

The fetcher pulls the published `sitemap.xml`, descends one level if it's a sitemap index, and returns a flat list of URLs. Used by `doctor`.

- [ ] **Step 1: Create fixtures**

Create `tests/fixtures/gsc/sitemap-flat.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://culture.dev/</loc></url>
  <url><loc>https://culture.dev/agex/</loc></url>
  <url><loc>https://culture.dev/docs/intro/</loc></url>
</urlset>
```

Create `tests/fixtures/gsc/sitemap-index.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://culture.dev/sitemap-leaf-a.xml</loc></sitemap>
</sitemapindex>
```

Create `tests/fixtures/gsc/sitemap-leaf-a.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://culture.dev/leaf-a-one/</loc></url>
  <url><loc>https://culture.dev/leaf-a-two/</loc></url>
</urlset>
```

- [ ] **Step 2: Write the failing tests**

Create `tests/unit/test_gsc_sitemap_fetch.py`:

```python
"""Tests for :mod:`katvan.gsc._sitemap_fetch`."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from katvan.cli._errors import KatvanError
from katvan.gsc._sitemap_fetch import fetch_sitemap_urls

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "gsc"


class _FakeResponse:
    def __init__(self, content: bytes, status: int = 200) -> None:
        self.content = content
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _flat_bytes() -> bytes:
    return (FIX / "sitemap-flat.xml").read_bytes()


def _index_bytes() -> bytes:
    return (FIX / "sitemap-index.xml").read_bytes()


def _leaf_bytes() -> bytes:
    return (FIX / "sitemap-leaf-a.xml").read_bytes()


def test_flat_sitemap_returns_urls() -> None:
    with patch(
        "katvan.gsc._sitemap_fetch._http_get",
        return_value=_FakeResponse(_flat_bytes()),
    ):
        urls = fetch_sitemap_urls("https://culture.dev/")
    assert urls == [
        "https://culture.dev/",
        "https://culture.dev/agex/",
        "https://culture.dev/docs/intro/",
    ]


def test_sitemap_index_descends_one_level() -> None:
    def fake_get(url: str) -> _FakeResponse:
        if url.endswith("sitemap.xml"):
            return _FakeResponse(_index_bytes())
        if url.endswith("sitemap-leaf-a.xml"):
            return _FakeResponse(_leaf_bytes())
        raise AssertionError(f"unexpected url: {url}")

    with patch("katvan.gsc._sitemap_fetch._http_get", side_effect=fake_get):
        urls = fetch_sitemap_urls("https://culture.dev/")
    assert urls == [
        "https://culture.dev/leaf-a-one/",
        "https://culture.dev/leaf-a-two/",
    ]


def test_http_error_raises_katvan_error() -> None:
    def fake_get(url: str) -> _FakeResponse:
        return _FakeResponse(b"", status=503)

    with patch("katvan.gsc._sitemap_fetch._http_get", side_effect=fake_get):
        with pytest.raises(KatvanError) as exc:
            fetch_sitemap_urls("https://culture.dev/")
    assert "sitemap.xml" in exc.value.message


def test_strips_trailing_slash_when_building_url() -> None:
    captured: list[str] = []

    def fake_get(url: str) -> _FakeResponse:
        captured.append(url)
        return _FakeResponse(_flat_bytes())

    with patch("katvan.gsc._sitemap_fetch._http_get", side_effect=fake_get):
        fetch_sitemap_urls("https://culture.dev/")
    assert captured == ["https://culture.dev/sitemap.xml"]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_gsc_sitemap_fetch.py -v`
Expected: All FAIL — module does not exist.

- [ ] **Step 4: Implement the fetcher**

Create `katvan/gsc/_sitemap_fetch.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_gsc_sitemap_fetch.py -v`
Expected: 4 PASSED.

- [ ] **Step 6: Commit**

```bash
git add katvan/gsc/_sitemap_fetch.py tests/unit/test_gsc_sitemap_fetch.py tests/fixtures/gsc/
git commit -m "feat(gsc): sitemap fetcher with one-level index descent"
```

---

## Task 4: `sitemaps` subcommand logic

**Files:**
- Create: `katvan/gsc/sitemaps.py`
- Create: `tests/unit/test_gsc_sitemaps.py`
- Create: `tests/fixtures/gsc/sitemaps-list.json`

Pure logic, no CLI yet. Returns a normalized list of dicts; the verb wires it up in Task 5.

- [ ] **Step 1: Create fixture**

Create `tests/fixtures/gsc/sitemaps-list.json`:

```json
{
  "sitemap": [
    {
      "path": "https://culture.dev/sitemap.xml",
      "lastSubmitted": "2026-05-01T08:30:00.000Z",
      "lastDownloaded": "2026-05-17T14:22:00.000Z",
      "isPending": false,
      "isSitemapsIndex": false,
      "type": "sitemap",
      "errors": "0",
      "warnings": "1",
      "contents": [
        {"type": "web", "submitted": "94", "indexed": "91"}
      ]
    }
  ]
}
```

- [ ] **Step 2: Write the failing tests**

Create `tests/unit/test_gsc_sitemaps.py`:

```python
"""Tests for :mod:`katvan.gsc.sitemaps`."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from katvan.gsc.sitemaps import list_sitemaps

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "gsc"


def _fake_client_returning(payload: dict) -> MagicMock:
    """Build a MagicMock chain mimicking ``client.sitemaps().list(...).execute()``."""
    client = MagicMock()
    client.sitemaps.return_value.list.return_value.execute.return_value = payload
    return client


def test_list_sitemaps_normalises_response() -> None:
    payload = json.loads((FIX / "sitemaps-list.json").read_text())
    client = _fake_client_returning(payload)

    rows = list_sitemaps(client, site_url="https://culture.dev/")

    assert len(rows) == 1
    row = rows[0]
    assert row["path"] == "https://culture.dev/sitemap.xml"
    assert row["last_submitted"] == "2026-05-01T08:30:00.000Z"
    assert row["last_downloaded"] == "2026-05-17T14:22:00.000Z"
    assert row["is_pending"] is False
    assert row["errors"] == 0
    assert row["warnings"] == 1
    assert row["contents"] == [{"type": "web", "submitted": 94, "indexed": 91}]


def test_list_sitemaps_handles_empty_response() -> None:
    client = _fake_client_returning({})
    assert list_sitemaps(client, site_url="https://culture.dev/") == []


def test_list_sitemaps_passes_site_url_to_api() -> None:
    payload = {"sitemap": []}
    client = _fake_client_returning(payload)
    list_sitemaps(client, site_url="https://culture.dev/")
    client.sitemaps.return_value.list.assert_called_once_with(siteUrl="https://culture.dev/")
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_gsc_sitemaps.py -v`
Expected: All FAIL — module not found.

- [ ] **Step 4: Implement `sitemaps.py`**

Create `katvan/gsc/sitemaps.py`:

```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_gsc_sitemaps.py -v`
Expected: 3 PASSED.

- [ ] **Step 6: Commit**

```bash
git add katvan/gsc/sitemaps.py tests/unit/test_gsc_sitemaps.py tests/fixtures/gsc/sitemaps-list.json
git commit -m "feat(gsc): sitemaps subcommand logic with response normalisation"
```

---

## Task 5: CLI wiring for the `gsc` verb (sitemaps only first)

**Files:**
- Create: `katvan/cli/_commands/gsc.py`
- Modify: `katvan/cli/__init__.py`
- Create: `tests/cli/test_gsc_sitemaps.py`

Wires up the verb at the CLI level with only the `sitemaps` subcommand registered. `inspect` and `doctor` are added in later tasks. Output: a tiny text table by default, JSON with `--json`.

- [ ] **Step 1: Write the failing tests**

Create `tests/cli/test_gsc_sitemaps.py`:

```python
"""End-to-end tests for ``katvan gsc sitemaps`` (mocked at the client layer)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from katvan.cli import main


@pytest.fixture
def gsc_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Set the env vars build_client expects (no real auth needed — patched)."""
    creds = tmp_path / "sa.json"
    creds.write_text("{}")
    monkeypatch.setenv("KATVAN_GSC_CREDENTIALS", str(creds))
    monkeypatch.setenv("KATVAN_GSC_SITE", "https://culture.dev/")


def _fake_client_with_sitemaps(payload: dict) -> MagicMock:
    client = MagicMock()
    client.sitemaps.return_value.list.return_value.execute.return_value = payload
    return client


def test_gsc_sitemaps_json_output(
    capsys: pytest.CaptureFixture[str], gsc_env: None
) -> None:
    payload = {
        "sitemap": [
            {
                "path": "https://culture.dev/sitemap.xml",
                "lastSubmitted": "2026-05-01T08:30:00.000Z",
                "lastDownloaded": "2026-05-17T14:22:00.000Z",
                "isPending": False,
                "errors": "0",
                "warnings": "1",
                "contents": [{"type": "web", "submitted": "94", "indexed": "91"}],
            }
        ]
    }
    with patch(
        "katvan.cli._commands.gsc.build_client",
        return_value=_fake_client_with_sitemaps(payload),
    ):
        rc = main(["gsc", "sitemaps", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["sitemaps"][0]["path"] == "https://culture.dev/sitemap.xml"
    assert out["sitemaps"][0]["errors"] == 0


def test_gsc_sitemaps_text_output_lists_paths(
    capsys: pytest.CaptureFixture[str], gsc_env: None
) -> None:
    payload = {
        "sitemap": [
            {
                "path": "https://culture.dev/sitemap.xml",
                "lastDownloaded": "2026-05-17T14:22:00.000Z",
                "errors": "0",
                "warnings": "1",
            }
        ]
    }
    with patch(
        "katvan.cli._commands.gsc.build_client",
        return_value=_fake_client_with_sitemaps(payload),
    ):
        rc = main(["gsc", "sitemaps"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "https://culture.dev/sitemap.xml" in out
    assert "errors=0" in out
    assert "warnings=1" in out


def test_gsc_sitemaps_missing_credentials_exits_with_hint(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("KATVAN_GSC_CREDENTIALS", raising=False)
    rc = main(["gsc", "sitemaps"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "error:" in err
    assert "hint:" in err
    assert "KATVAN_GSC_CREDENTIALS" in err


def test_gsc_help_lists_sitemaps_subcommand(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        main(["gsc", "--help"])
    out = capsys.readouterr().out
    assert "sitemaps" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/cli/test_gsc_sitemaps.py -v`
Expected: All FAIL — `gsc` verb not registered.

- [ ] **Step 3: Create the CLI verb module**

Create `katvan/cli/_commands/gsc.py`:

```python
"""``katvan gsc`` — Google Search Console read-only verbs.

Subcommands:

* ``sitemaps`` — list submitted sitemaps and status.
* ``inspect <url>`` — single-URL inspection (Task 7).
* ``doctor`` — composite indexing-health audit (Task 9).

Wiring follows the existing one-file-per-verb pattern in this directory.
Subcommands dispatch through ``args.gsc_func``; the top-level ``cmd_gsc``
delegates to that handler, or prints the verb help when no subcommand is given.
"""
from __future__ import annotations

import argparse

from katvan.cli._errors import EXIT_USER_ERROR, KatvanError
from katvan.cli._output import emit_result
from katvan.gsc.client import build_client, site_url
from katvan.gsc.sitemaps import list_sitemaps


# ----- subcommand handlers -----------------------------------------------------

def _cmd_sitemaps(args: argparse.Namespace) -> int:
    client = build_client()
    rows = list_sitemaps(client, site_url=site_url())
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        emit_result({"site": site_url(), "sitemaps": rows}, json_mode=True)
    else:
        if not rows:
            emit_result("(no sitemaps submitted)", json_mode=False)
        else:
            lines = []
            for row in rows:
                lines.append(
                    f"{row['path']}\t"
                    f"last_downloaded={row['last_downloaded'] or '-'}\t"
                    f"errors={row['errors']}\twarnings={row['warnings']}"
                )
            emit_result("\n".join(lines), json_mode=False)
    return 0


# ----- top-level verb dispatch -------------------------------------------------

def cmd_gsc(args: argparse.Namespace) -> int:
    handler = getattr(args, "gsc_func", None)
    if handler is None:
        # No subcommand given. Argparse alone won't catch this because the
        # subparsers are optional (so `--help` works without crashing); we
        # raise a KatvanError instead of printing help to keep error
        # contract uniform.
        raise KatvanError(
            code=EXIT_USER_ERROR,
            message="missing gsc subcommand",
            remediation="run 'katvan gsc --help' to see subcommands",
        )
    return handler(args)


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "gsc",
        help="Google Search Console read-only verbs (sitemaps, inspect, doctor).",
    )
    p.set_defaults(func=cmd_gsc)
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")

    gsub = p.add_subparsers(dest="gsc_command")

    # `sitemaps` subcommand.
    s = gsub.add_parser("sitemaps", help="List submitted sitemaps and status.")
    s.add_argument("--json", action="store_true", help="Emit structured JSON.")
    s.set_defaults(gsc_func=_cmd_sitemaps)
```

- [ ] **Step 4: Register the verb in the CLI**

Modify `katvan/cli/__init__.py`:

After the existing import line `from katvan.cli._commands import doctor as _doctor_cmd`, add:

```python
from katvan.cli._commands import gsc as _gsc_cmd
```

In `_build_parser`, after the existing `_doctor_cmd.register(sub)` line, add:

```python
    _gsc_cmd.register(sub)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/cli/test_gsc_sitemaps.py -v`
Expected: 4 PASSED.

- [ ] **Step 6: Run the full unit + cli suite to confirm no regressions**

Run: `uv run pytest tests/unit/ tests/cli/ -v`
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add katvan/cli/_commands/gsc.py katvan/cli/__init__.py tests/cli/test_gsc_sitemaps.py
git commit -m "feat(gsc): wire 'katvan gsc sitemaps' subcommand"
```

---

## Task 6: `inspect` subcommand logic + wiring

**Files:**
- Create: `katvan/gsc/inspect.py`
- Modify: `katvan/cli/_commands/gsc.py`
- Create: `tests/unit/test_gsc_inspect.py`
- Create: `tests/cli/test_gsc_inspect.py`
- Create: `tests/fixtures/gsc/url-inspection-pass.json`
- Create: `tests/fixtures/gsc/url-inspection-not-indexed.json`

- [ ] **Step 1: Create fixtures**

Create `tests/fixtures/gsc/url-inspection-pass.json`:

```json
{
  "inspectionResult": {
    "indexStatusResult": {
      "verdict": "PASS",
      "coverageState": "Submitted and indexed",
      "lastCrawlTime": "2026-05-15T10:00:00Z",
      "robotsTxtState": "ALLOWED",
      "pageFetchState": "SUCCESSFUL",
      "googleCanonical": "https://culture.dev/",
      "userCanonical": "https://culture.dev/"
    },
    "mobileUsabilityResult": {"verdict": "PASS"},
    "richResultsResult": {"verdict": "PASS"}
  }
}
```

Create `tests/fixtures/gsc/url-inspection-not-indexed.json`:

```json
{
  "inspectionResult": {
    "indexStatusResult": {
      "verdict": "NEUTRAL",
      "coverageState": "URL is not on Google",
      "lastCrawlTime": "2026-05-10T08:00:00Z",
      "robotsTxtState": "ALLOWED",
      "pageFetchState": "SUCCESSFUL",
      "googleCanonical": "",
      "userCanonical": "https://culture.dev/missing/"
    }
  }
}
```

- [ ] **Step 2: Write the failing unit tests**

Create `tests/unit/test_gsc_inspect.py`:

```python
"""Tests for :mod:`katvan.gsc.inspect`."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from katvan.cli._errors import KatvanError
from katvan.gsc.inspect import inspect_url

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "gsc"


def _fake_client(payload: dict) -> MagicMock:
    client = MagicMock()
    chain = client.urlInspection.return_value.index.return_value.inspect
    chain.return_value.execute.return_value = payload
    return client


def test_inspect_url_pass_extracts_fields() -> None:
    payload = json.loads((FIX / "url-inspection-pass.json").read_text())
    client = _fake_client(payload)
    result = inspect_url(client, url="https://culture.dev/", site_url="https://culture.dev/")
    assert result["url"] == "https://culture.dev/"
    assert result["verdict"] == "PASS"
    assert result["coverage_state"] == "Submitted and indexed"
    assert result["robots_txt_state"] == "ALLOWED"
    assert result["page_fetch_state"] == "SUCCESSFUL"
    assert result["google_canonical"] == "https://culture.dev/"
    assert result["user_canonical"] == "https://culture.dev/"
    assert result["mobile_usability"] == "PASS"
    assert result["rich_results"] == "PASS"


def test_inspect_url_not_indexed_returns_neutral_verdict() -> None:
    payload = json.loads((FIX / "url-inspection-not-indexed.json").read_text())
    client = _fake_client(payload)
    result = inspect_url(
        client, url="https://culture.dev/missing/", site_url="https://culture.dev/"
    )
    assert result["verdict"] == "NEUTRAL"
    assert result["coverage_state"] == "URL is not on Google"
    assert result["mobile_usability"] == ""
    assert result["rich_results"] == ""


def test_inspect_url_rejects_url_outside_site() -> None:
    client = MagicMock()
    with pytest.raises(KatvanError) as exc:
        inspect_url(
            client, url="https://example.com/", site_url="https://culture.dev/"
        )
    assert "outside the verified property" in exc.value.message
    client.urlInspection.assert_not_called()


def test_inspect_url_passes_correct_args_to_api() -> None:
    payload = json.loads((FIX / "url-inspection-pass.json").read_text())
    client = _fake_client(payload)
    inspect_url(client, url="https://culture.dev/", site_url="https://culture.dev/")
    chain = client.urlInspection.return_value.index.return_value.inspect
    chain.assert_called_once_with(
        body={"inspectionUrl": "https://culture.dev/", "siteUrl": "https://culture.dev/"}
    )
```

- [ ] **Step 3: Write the failing CLI tests**

Create `tests/cli/test_gsc_inspect.py`:

```python
"""End-to-end tests for ``katvan gsc inspect <url>``."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from katvan.cli import main

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "gsc"


@pytest.fixture
def gsc_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    creds = tmp_path / "sa.json"
    creds.write_text("{}")
    monkeypatch.setenv("KATVAN_GSC_CREDENTIALS", str(creds))
    monkeypatch.setenv("KATVAN_GSC_SITE", "https://culture.dev/")


def _fake_client(payload: dict) -> MagicMock:
    client = MagicMock()
    chain = client.urlInspection.return_value.index.return_value.inspect
    chain.return_value.execute.return_value = payload
    return client


def test_inspect_json_output(
    capsys: pytest.CaptureFixture[str], gsc_env: None
) -> None:
    payload = json.loads((FIX / "url-inspection-pass.json").read_text())
    with patch(
        "katvan.cli._commands.gsc.build_client", return_value=_fake_client(payload)
    ):
        rc = main(["gsc", "inspect", "https://culture.dev/", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["verdict"] == "PASS"


def test_inspect_text_output(
    capsys: pytest.CaptureFixture[str], gsc_env: None
) -> None:
    payload = json.loads((FIX / "url-inspection-pass.json").read_text())
    with patch(
        "katvan.cli._commands.gsc.build_client", return_value=_fake_client(payload)
    ):
        rc = main(["gsc", "inspect", "https://culture.dev/"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "verdict: PASS" in out
    assert "https://culture.dev/" in out
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_gsc_inspect.py tests/cli/test_gsc_inspect.py -v`
Expected: All FAIL — `katvan.gsc.inspect` does not exist and the subcommand is not registered.

- [ ] **Step 5: Implement the logic**

Create `katvan/gsc/inspect.py`:

```python
"""``katvan gsc inspect <url>`` — per-URL indexing inspection."""
from __future__ import annotations

from typing import Any

from katvan.cli._errors import EXIT_USER_ERROR, KatvanError


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
```

- [ ] **Step 6: Wire the subcommand into `cli/_commands/gsc.py`**

Modify `katvan/cli/_commands/gsc.py`. Add the import:

```python
from katvan.gsc.inspect import inspect_url
```

Add the handler after `_cmd_sitemaps`:

```python
def _cmd_inspect(args: argparse.Namespace) -> int:
    client = build_client()
    result = inspect_url(client, url=args.url, site_url=site_url())
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        emit_result(result, json_mode=True)
    else:
        lines = [
            f"url: {result['url']}",
            f"verdict: {result['verdict']}",
            f"coverage_state: {result['coverage_state']}",
            f"last_crawl_time: {result['last_crawl_time'] or '-'}",
            f"robots_txt_state: {result['robots_txt_state']}",
            f"page_fetch_state: {result['page_fetch_state']}",
            f"google_canonical: {result['google_canonical'] or '-'}",
            f"user_canonical: {result['user_canonical'] or '-'}",
            f"mobile_usability: {result['mobile_usability'] or '-'}",
            f"rich_results: {result['rich_results'] or '-'}",
        ]
        emit_result("\n".join(lines), json_mode=False)
    return 0
```

In `register`, add a subparser registration after the `sitemaps` block:

```python
    i = gsub.add_parser("inspect", help="Inspect a single URL's indexing status.")
    i.add_argument("url", help="The URL to inspect (must be under the verified property).")
    i.add_argument("--json", action="store_true", help="Emit structured JSON.")
    i.set_defaults(gsc_func=_cmd_inspect)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_gsc_inspect.py tests/cli/test_gsc_inspect.py -v`
Expected: 6 PASSED total.

- [ ] **Step 8: Commit**

```bash
git add katvan/gsc/inspect.py katvan/cli/_commands/gsc.py tests/unit/test_gsc_inspect.py tests/cli/test_gsc_inspect.py tests/fixtures/gsc/url-inspection-*.json
git commit -m "feat(gsc): add 'inspect <url>' subcommand"
```

---

## Task 7: `doctor` subcommand logic + wiring

**Files:**
- Create: `katvan/gsc/doctor.py`
- Modify: `katvan/cli/_commands/gsc.py`
- Create: `tests/unit/test_gsc_doctor.py`
- Create: `tests/cli/test_gsc_doctor.py`
- Create: `tests/fixtures/gsc/url-inspection-crawl-error.json`

`doctor` composes the sitemap fetcher + per-URL inspect to surface problems.

- [ ] **Step 1: Create the crawl-error fixture**

Create `tests/fixtures/gsc/url-inspection-crawl-error.json`:

```json
{
  "inspectionResult": {
    "indexStatusResult": {
      "verdict": "FAIL",
      "coverageState": "Crawl error",
      "lastCrawlTime": "2026-05-12T03:11:00Z",
      "robotsTxtState": "ALLOWED",
      "pageFetchState": "SERVER_ERROR",
      "googleCanonical": "",
      "userCanonical": "https://culture.dev/broken/"
    }
  }
}
```

- [ ] **Step 2: Write the failing unit tests**

Create `tests/unit/test_gsc_doctor.py`:

```python
"""Tests for :mod:`katvan.gsc.doctor`."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from katvan.gsc.doctor import run_doctor

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "gsc"


def _client_with_inspect_responses(by_url: dict[str, dict]) -> MagicMock:
    """Return a MagicMock whose .urlInspection().index().inspect(...).execute()
    returns the payload keyed by the inspectionUrl in the request body."""
    client = MagicMock()
    chain = client.urlInspection.return_value.index.return_value.inspect

    def fake_inspect(body: dict) -> MagicMock:
        execute = MagicMock()
        execute.execute.return_value = by_url[body["inspectionUrl"]]
        return execute

    chain.side_effect = fake_inspect
    return client


def test_run_doctor_all_pass_returns_empty_problems() -> None:
    passes = json.loads((FIX / "url-inspection-pass.json").read_text())
    urls = ["https://culture.dev/", "https://culture.dev/agex/"]
    client = _client_with_inspect_responses({u: passes for u in urls})
    with patch(
        "katvan.gsc.doctor.fetch_sitemap_urls", return_value=urls
    ):
        report = run_doctor(client, site_url="https://culture.dev/")
    assert report["summary"]["total"] == 2
    assert report["summary"]["problems"] == 0
    assert report["summary"]["errors"] == 0
    assert report["problems"] == []
    assert report["errors"] == []


def test_run_doctor_records_inspection_failures_in_errors_list() -> None:
    """One URL's inspect call raises — partial report still returns."""
    passes = json.loads((FIX / "url-inspection-pass.json").read_text())
    urls = ["https://culture.dev/", "https://culture.dev/boom/"]

    client = MagicMock()
    chain = client.urlInspection.return_value.index.return_value.inspect

    def fake_inspect(body: dict) -> MagicMock:
        execute = MagicMock()
        if body["inspectionUrl"] == urls[1]:
            execute.execute.side_effect = RuntimeError("quota exceeded")
        else:
            execute.execute.return_value = passes
        return execute

    chain.side_effect = fake_inspect

    with patch("katvan.gsc.doctor.fetch_sitemap_urls", return_value=urls):
        report = run_doctor(client, site_url="https://culture.dev/")

    assert report["summary"]["total"] == 2
    assert report["summary"]["problems"] == 0
    assert report["summary"]["errors"] == 1
    assert report["errors"][0]["url"] == urls[1]
    assert "quota exceeded" in report["errors"][0]["error"]


def test_run_doctor_groups_problems_by_class() -> None:
    passes = json.loads((FIX / "url-inspection-pass.json").read_text())
    not_indexed = json.loads((FIX / "url-inspection-not-indexed.json").read_text())
    crawl_err = json.loads((FIX / "url-inspection-crawl-error.json").read_text())
    urls = [
        "https://culture.dev/",
        "https://culture.dev/missing/",
        "https://culture.dev/broken/",
    ]
    responses = {
        urls[0]: passes,
        urls[1]: not_indexed,
        urls[2]: crawl_err,
    }
    client = _client_with_inspect_responses(responses)
    with patch("katvan.gsc.doctor.fetch_sitemap_urls", return_value=urls):
        report = run_doctor(client, site_url="https://culture.dev/")

    assert report["summary"]["total"] == 3
    assert report["summary"]["problems"] == 2
    problem_urls = {p["url"] for p in report["problems"]}
    assert urls[1] in problem_urls
    assert urls[2] in problem_urls
    # not_indexed: verdict != PASS → tagged not_indexed.
    # crawl_err:  verdict != PASS AND pageFetchState != SUCCESSFUL → tagged both.
    crawl_problem = next(p for p in report["problems"] if p["url"] == urls[2])
    assert "not_indexed" in crawl_problem["classes"]
    assert "crawl_errors" in crawl_problem["classes"]
```

- [ ] **Step 3: Write the failing CLI tests**

Create `tests/cli/test_gsc_doctor.py`:

```python
"""End-to-end tests for ``katvan gsc doctor``."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from katvan.cli import main

FIX = Path(__file__).resolve().parent.parent / "fixtures" / "gsc"


@pytest.fixture
def gsc_env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    creds = tmp_path / "sa.json"
    creds.write_text("{}")
    monkeypatch.setenv("KATVAN_GSC_CREDENTIALS", str(creds))
    monkeypatch.setenv("KATVAN_GSC_SITE", "https://culture.dev/")


def _client_with_inspect(by_url: dict[str, dict]) -> MagicMock:
    client = MagicMock()
    chain = client.urlInspection.return_value.index.return_value.inspect

    def fake_inspect(body: dict) -> MagicMock:
        execute = MagicMock()
        execute.execute.return_value = by_url[body["inspectionUrl"]]
        return execute

    chain.side_effect = fake_inspect
    return client


def test_doctor_exits_zero_when_all_urls_pass(
    capsys: pytest.CaptureFixture[str], gsc_env: None
) -> None:
    passes = json.loads((FIX / "url-inspection-pass.json").read_text())
    urls = ["https://culture.dev/", "https://culture.dev/agex/"]
    client = _client_with_inspect({u: passes for u in urls})
    with patch(
        "katvan.cli._commands.gsc.build_client", return_value=client
    ), patch("katvan.gsc.doctor.fetch_sitemap_urls", return_value=urls):
        rc = main(["gsc", "doctor", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["summary"]["problems"] == 0


def test_doctor_exits_one_when_problems_present(
    capsys: pytest.CaptureFixture[str], gsc_env: None
) -> None:
    passes = json.loads((FIX / "url-inspection-pass.json").read_text())
    crawl_err = json.loads((FIX / "url-inspection-crawl-error.json").read_text())
    urls = ["https://culture.dev/", "https://culture.dev/broken/"]
    client = _client_with_inspect({urls[0]: passes, urls[1]: crawl_err})
    with patch(
        "katvan.cli._commands.gsc.build_client", return_value=client
    ), patch("katvan.gsc.doctor.fetch_sitemap_urls", return_value=urls):
        rc = main(["gsc", "doctor"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "https://culture.dev/broken/" in out
    assert "crawl_errors" in out or "not_indexed" in out
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `uv run pytest tests/unit/test_gsc_doctor.py tests/cli/test_gsc_doctor.py -v`
Expected: All FAIL — module and subcommand do not exist.

- [ ] **Step 5: Implement the logic**

Create `katvan/gsc/doctor.py`:

```python
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
          "summary": {"total": N, "problems": M, "by_class": {...}},
          "problems": [
            {"url": "...", "classes": [...], "inspection": {<full inspect_url result>}},
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
```

- [ ] **Step 6: Wire the subcommand into `cli/_commands/gsc.py`**

Modify `katvan/cli/_commands/gsc.py`. Add import:

```python
from katvan.gsc.doctor import run_doctor
```

Add the handler:

```python
def _cmd_doctor(args: argparse.Namespace) -> int:
    client = build_client()
    report = run_doctor(client, site_url=site_url())
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        emit_result(report, json_mode=True)
    else:
        lines = [
            f"# GSC doctor report: {report['site']}",
            "",
            f"Total URLs: {report['summary']['total']}",
            f"Problems:   {report['summary']['problems']}",
        ]
        if report["summary"]["by_class"]:
            lines.append("")
            lines.append("## By class")
            for cls, count in sorted(report["summary"]["by_class"].items()):
                lines.append(f"- {cls}: {count}")
        if report["problems"]:
            lines.append("")
            lines.append("## Problem URLs")
            for p in report["problems"]:
                lines.append(f"- {p['url']}  ({', '.join(p['classes'])})")
        if report["errors"]:
            lines.append("")
            lines.append("## Errors (inspection failed)")
            for e in report["errors"]:
                lines.append(f"- {e['url']}  ({e['error']})")
        emit_result("\n".join(lines), json_mode=False)
    # Exit non-zero if ANY problems found OR if some URLs failed inspection.
    has_problems = report["summary"]["problems"] > 0
    has_errors = report["summary"]["errors"] > 0
    return 0 if not (has_problems or has_errors) else 1
```

In `register`, add the subparser:

```python
    d = gsub.add_parser(
        "doctor",
        help="Audit every sitemap URL; exit 1 if any problems are found.",
    )
    d.add_argument("--json", action="store_true", help="Emit structured JSON.")
    d.set_defaults(gsc_func=_cmd_doctor)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest tests/unit/test_gsc_doctor.py tests/cli/test_gsc_doctor.py -v`
Expected: 4 PASSED.

- [ ] **Step 8: Run the full test suite**

Run: `uv run pytest -v`
Expected: all green.

- [ ] **Step 9: Commit**

```bash
git add katvan/gsc/doctor.py katvan/cli/_commands/gsc.py tests/unit/test_gsc_doctor.py tests/cli/test_gsc_doctor.py tests/fixtures/gsc/url-inspection-crawl-error.json
git commit -m "feat(gsc): add 'doctor' composite audit subcommand"
```

---

## Task 8: Jekyll site verification meta tag

**Files:**
- Modify: `site/_config.culture.yml`
- Modify: `site/_includes/head_custom.html`

The `just-the-docs` theme does NOT auto-emit a `google-site-verification` meta tag from the config key, so we wire it manually in `head_custom.html`. The verification code itself is acquired by the human operator from the GSC UI; this task installs the plumbing and leaves the operator to substitute the real code.

- [ ] **Step 1: Edit the site config**

Modify `site/_config.culture.yml`. Replace the existing block at line ~30:

```yaml
# Uncomment after registering at https://search.google.com/search-console
# google_site_verification: "YOUR_CODE_HERE"
# webmaster_verifications:
#   bing: "YOUR_CODE_HERE"
```

With:

```yaml
# Set after registering at https://search.google.com/search-console (URL-prefix
# property for https://culture.dev/). Picked up by head_custom.html, not by the
# just-the-docs theme directly. Leave commented to disable the meta tag.
# google_site_verification: "REPLACE_WITH_REAL_CODE_FROM_GSC"
# webmaster_verifications:
#   bing: "REPLACE_WITH_REAL_CODE_FROM_BING"
```

(Kept commented because the implementor doesn't have a code yet — the operator uncomments and substitutes their real code in a follow-up commit.)

- [ ] **Step 2: Add the meta-tag emission to head_custom.html**

Modify `site/_includes/head_custom.html`. After the existing `<link rel="related" ... />` lines and before `{% include analytics.html %}`, insert:

```html
{%- if site.google_site_verification -%}
<meta name="google-site-verification" content="{{ site.google_site_verification }}">
{%- endif -%}
```

- [ ] **Step 3: Sanity-check the Jekyll build still works**

Run:

```bash
cd site
bundle exec jekyll build --config _config.base.yml,_config.culture.yml
```

Expected: build succeeds. Without `google_site_verification` set in `_config.culture.yml`, no `google-site-verification` meta tag appears in `_site/index.html` — that's correct.

- [ ] **Step 4: Verify gated emission with a temporary value**

Temporarily uncomment the line in `_config.culture.yml` (set value to a dummy like `"test-verification-code"`), rebuild, and grep:

```bash
grep -r "google-site-verification" _site/index.html
```

Expected: one match with the dummy value. Then revert the temporary edit so the line stays commented.

- [ ] **Step 5: Commit**

```bash
cd ..
git add site/_config.culture.yml site/_includes/head_custom.html
git commit -m "feat(site): wire google-site-verification meta tag (gated by config)"
```

---

## Task 9: Setup docs + README update

**Files:**
- Create: `docs/gsc-setup.md`
- Modify: `README.md`

- [ ] **Step 1: Write the setup guide**

Create `docs/gsc-setup.md`:

```markdown
# Google Search Console setup

One-time human steps to enable `katvan gsc` against the live `culture.dev`
property. Re-run only if the service account is rotated or the property is
re-created.

## Prerequisites

- Owner-level access to the GSC property `https://culture.dev/` (or
  rights to be added as a user).
- A Google Cloud project where a service account can be created. A
  brand-new project works fine; we use this for no other API.

## Steps

### 1. Verify the site with Google Search Console

1. Go to https://search.google.com/search-console.
2. Add a property of type **URL prefix**: `https://culture.dev/`.
3. Choose the **HTML tag** verification method. Copy the `content="..."`
   value (the verification code).
4. In this repo, edit `site/_config.culture.yml`, uncomment the
   `google_site_verification` line, and set it to your verification
   code.
5. Commit, merge, and let CI publish the site. Once live, return to
   GSC and click **Verify**.

### 2. Enable the Search Console API

1. Open https://console.cloud.google.com and select (or create) a
   project.
2. Navigate to **APIs & Services → Library**.
3. Find **Google Search Console API** and click **Enable**.

### 3. Create a service account

1. **APIs & Services → Credentials → Create credentials → Service account**.
2. Give it a descriptive name (e.g. `katvan-gsc-reader`). No project-level
   roles are required.
3. After creation, click into the account → **Keys → Add key → Create new
   key → JSON**. Save the JSON file somewhere private.

### 4. Grant the service account on the GSC property

1. Back in https://search.google.com/search-console, select the
   `https://culture.dev/` property.
2. **Settings → Users and permissions → Add user**.
3. Paste the service account's email (looks like
   `katvan-gsc-reader@<project>.iam.gserviceaccount.com`).
4. Permission: **Restricted** (read-only is sufficient for our scope).

### 5. Configure the CLI

Export the credential path in whichever shell or service runs `katvan`:

```sh
export KATVAN_GSC_CREDENTIALS=/absolute/path/to/sa.json
```

Optionally override the site URL for testing against a staging property:

```sh
export KATVAN_GSC_SITE=https://staging.example.com/
```

Default is `https://culture.dev/`.

### 6. Smoke test

```sh
katvan gsc sitemaps
```

Expected: a row per submitted sitemap with last-download timestamps and
error / warning counts. If `errors=0 warnings=0`, indexing health is
nominal.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `error: KATVAN_GSC_CREDENTIALS env var is not set` | Step 5 not run in this shell. |
| `error: KATVAN_GSC_CREDENTIALS file not found: ...` | Path typo or the key was moved. |
| HTTP 403 from any subcommand | Step 4 was skipped, or the SA email was added to the wrong property. |
| HTTP 401 | The key has been disabled or the project's API is disabled. |
| `katvan gsc doctor` reports `crawl_errors` | Investigate via `katvan gsc inspect <url>` — usually 5xx from the live site. |
```

- [ ] **Step 2: Update the README**

Modify `README.md`. Locate the "Verbs available today" section that lists `learn` and `explain` and add a `gsc` bullet:

```markdown
- `katvan gsc {sitemaps,inspect,doctor}` — read indexing-health data from
  Google Search Console (one-time setup: [`docs/gsc-setup.md`](docs/gsc-setup.md)).
```

- [ ] **Step 3: Commit**

```bash
git add docs/gsc-setup.md README.md
git commit -m "docs(gsc): setup guide and README entry"
```

---

## Task 10: Version bump and CHANGELOG

**Files:**
- Modify: `pyproject.toml`
- Modify: `katvan/__init__.py`
- Modify: `CHANGELOG.md`

Per project convention, run the project's version-bump tooling — this is a feature addition (`minor` bump), so `0.2.8` → `0.3.0`.

- [ ] **Step 1: Bump version in pyproject.toml**

Edit `pyproject.toml` line 3: change `version = "0.2.8"` to `version = "0.3.0"`.

- [ ] **Step 2: Bump version in katvan/__init__.py**

Find the `__version__` constant in `katvan/__init__.py` and update it to `"0.3.0"`. (Path may include a docstring + assignment; preserve everything else.)

- [ ] **Step 3: Add a CHANGELOG entry**

Edit `CHANGELOG.md`. Prepend a new section above the most recent entry, matching the existing format:

```markdown
## [0.3.0] - 2026-05-18

### Added
- New `katvan gsc` verb with `sitemaps`, `inspect`, and `doctor` subcommands
  for Google Search Console indexing-health data (#26).
- Site verification meta tag wired in `head_custom.html`, gated on
  `site.google_site_verification`.
- One-time setup guide at `docs/gsc-setup.md`.

### Dependencies
- Added `google-api-python-client` and `google-auth` as runtime deps.
```

- [ ] **Step 4: Run the full test suite once more**

Run: `uv run pytest -v`
Expected: all green.

- [ ] **Step 5: Run lint checks**

Run: `uv run flake8 katvan/gsc/ tests/unit/test_gsc_*.py tests/cli/test_gsc_*.py && uv run pylint katvan/gsc/`
Expected: clean (or only pre-existing style nits unrelated to this change — do not introduce new violations).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml katvan/__init__.py CHANGELOG.md
git commit -m "chore: bump version to 0.3.0 for GSC integration"
```

---

## Task 11: Open the PR

- [ ] **Step 1: Push the branch**

Run: `git push -u origin feat/gsc-integration-spec`

- [ ] **Step 2: Open a PR via `gh`**

Use the project's cicd / `gh pr create` flow with this body skeleton:

```markdown
## Summary
- New `katvan gsc` verb (sitemaps / inspect / doctor) reading indexing health
  from Google Search Console.
- Site verified via the `google-site-verification` meta tag, gated by
  `site.google_site_verification` in `_config.culture.yml`.
- One-time setup documented in `docs/gsc-setup.md`.

## Test plan
- [x] `uv run pytest -v` — all green (unit + cli).
- [x] `bundle exec jekyll build` — site builds without the meta tag when the
      config key is unset, emits it when set.
- [ ] Manual smoke: after merging and acquiring a real GSC verification code,
      uncomment `google_site_verification` and verify the property in GSC.
- [ ] Manual smoke: with `KATVAN_GSC_CREDENTIALS` pointing at a real SA key,
      run `katvan gsc sitemaps`, `katvan gsc inspect https://culture.dev/`,
      `katvan gsc doctor`.

Closes #26.

- katvan (Claude)
```

- [ ] **Step 3: Run the cicd `await` flow per project convention**

Use `cicd` skill or equivalent to wait for CI green + SonarCloud quality
gate + reviewer feedback. Address review comments via the existing
`pr-review` flow.
