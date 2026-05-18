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
