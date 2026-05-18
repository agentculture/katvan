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
