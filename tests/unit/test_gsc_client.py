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
