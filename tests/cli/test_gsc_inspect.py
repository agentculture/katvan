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
