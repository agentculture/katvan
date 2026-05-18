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
