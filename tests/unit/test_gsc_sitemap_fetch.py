"""Tests for :mod:`katvan.gsc._sitemap_fetch`."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from katvan.cli._errors import EXIT_ENV_ERROR, KatvanError
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


def test_non_http_scheme_rejected() -> None:
    with pytest.raises(KatvanError) as exc:
        fetch_sitemap_urls("file:///etc/")
    assert exc.value.code == EXIT_ENV_ERROR
    assert "http" in exc.value.message


def test_child_sitemap_fetch_failure_raises_katvan_error() -> None:
    def fake_get(url: str) -> _FakeResponse:
        if url.endswith("sitemap.xml"):
            return _FakeResponse(_index_bytes())
        # child sitemap returns 503
        return _FakeResponse(b"", status=503)

    with patch("katvan.gsc._sitemap_fetch._http_get", side_effect=fake_get):
        with pytest.raises(KatvanError) as exc:
            fetch_sitemap_urls("https://culture.dev/")
    assert exc.value.code == EXIT_ENV_ERROR
    assert "sitemap-leaf-a.xml" in exc.value.message or "leaf" in exc.value.message


def test_malformed_xml_raises_katvan_error() -> None:
    def fake_get(url: str) -> _FakeResponse:
        return _FakeResponse(b"this is not xml <<< at all")

    with patch("katvan.gsc._sitemap_fetch._http_get", side_effect=fake_get):
        with pytest.raises(KatvanError) as exc:
            fetch_sitemap_urls("https://culture.dev/")
    assert exc.value.code == EXIT_ENV_ERROR
    assert "parse" in exc.value.message.lower()
