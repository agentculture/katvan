"""Tests for :mod:`katvan.gsc.sitemaps`."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError

from katvan._errors import EXIT_ENV_ERROR, KatvanError
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


def _http_error(status: int) -> HttpError:
    resp = MagicMock()
    resp.status = status
    resp.reason = "Forbidden"
    return HttpError(resp=resp, content=b"")


@pytest.mark.parametrize(
    "status,expected_in_remediation",
    [
        (401, "docs/gsc-setup.md"),
        (403, "docs/gsc-setup.md"),
        (429, "retry later"),
        (500, "check GSC property configuration"),
    ],
)
def test_list_sitemaps_translates_http_error(
    status: int, expected_in_remediation: str
) -> None:
    client = MagicMock()
    client.sitemaps.return_value.list.return_value.execute.side_effect = _http_error(status)
    with pytest.raises(KatvanError) as exc:
        list_sitemaps(client, site_url="https://culture.dev/")
    assert exc.value.code == EXIT_ENV_ERROR
    assert expected_in_remediation in exc.value.remediation
