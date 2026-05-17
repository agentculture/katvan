"""In-process unit tests for :mod:`katvan.cli._commands.overview`.

The corresponding tests under ``tests/cli/test_overview.py`` spawn
``python -m katvan`` as a subprocess and therefore do not get picked up by
pytest-cov. These tests call ``_handle()`` and ``_group_by_category()``
directly so the verb internals are instrumented.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from katvan import repos as repos_mod
from katvan.cli._commands import overview as overview_mod

# Synthetic registry covering all six known categories plus an unknown one
# (to confirm defaultdict semantics in ``_group_by_category``).
_FIXTURE_REGISTRY = """\
- id: alpha
  category: workspace-experience
  description: Alpha workspace tool.
- id: bravo
  category: core-runtime
  description: Bravo runtime.
- id: charlie
  category: identity-secrets
  description: Charlie identity.
- id: delta
  category: resident-culture
  description: Delta culture resident.
- id: echo
  category: resident-domain
  description: Echo domain resident.
- id: foxtrot
  category: org-site
  description: Foxtrot site.
- id: oddball
  category: experimental-future-thing
  description: Oddball with an unknown category.
"""


def _reset_caches() -> None:
    repos_mod._find_repo_root.cache_clear()
    repos_mod._parse_registry.cache_clear()
    repos_mod._parse_entries.cache_clear()


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    _reset_caches()
    yield
    _reset_caches()


@pytest.fixture()
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A temp dir laid out like a katvan checkout with the synthetic registry."""
    registry = tmp_path / "site" / "_data" / "agentculture_repos.yml"
    registry.parent.mkdir(parents=True)
    registry.write_text(_FIXTURE_REGISTRY, encoding="utf-8")
    nested = tmp_path / "docs" / "deep"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.delenv("KATVAN_SIBLINGS_ROOT", raising=False)
    repos_mod.set_siblings_root(None)
    yield tmp_path
    repos_mod.set_siblings_root(None)


# --- category grouping (inlined into _handle) ------------------------------


def test_handle_json_groups_all_six_known_categories(
    fake_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """JSON mode surfaces every known category bucket from the fixture."""
    rc = overview_mod._handle(argparse.Namespace(json=True))
    assert rc == 0
    by_cat = json.loads(capsys.readouterr().out)["by_category"]
    assert set(by_cat) >= {
        "workspace-experience",
        "core-runtime",
        "identity-secrets",
        "resident-culture",
        "resident-domain",
        "org-site",
    }
    for ids in by_cat.values():
        assert all(isinstance(e, dict) for e in ids)


def test_handle_json_keeps_unknown_categories(
    fake_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A registry with a category not in ``_CATEGORY_ORDER`` still groups it.

    This exercises the defaultdict semantics in ``_handle`` — the overview
    text mode then silently drops the unknown bucket (no `KeyError`).
    """
    rc = overview_mod._handle(argparse.Namespace(json=True))
    assert rc == 0
    by_cat = json.loads(capsys.readouterr().out)["by_category"]
    assert "experimental-future-thing" in by_cat
    assert by_cat["experimental-future-thing"][0]["id"] == "oddball"


# --- _handle: text mode ----------------------------------------------------


def test_handle_text_prints_total_and_known_headers(
    fake_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = argparse.Namespace(json=False)
    rc = overview_mod._handle(args)
    assert rc == 0
    out = capsys.readouterr().out
    # Total counts every entry (including the oddball).
    assert "AgentCulture registry — 7 repos" in out
    # All six known category labels render.
    for header in (
        "Workspace Experience",
        "Core Runtime",
        "Identity & Secrets",
        "Resident Culture",
        "Resident Domain",
        "Org Site",
    ):
        assert header in out
    # Per-entry lines render the id + description.
    assert "- alpha: Alpha workspace tool." in out
    assert "- foxtrot: Foxtrot site." in out


def test_handle_text_skips_categories_with_no_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Categories with zero entries are not printed."""
    minimal = "- id: only\n  category: core-runtime\n  description: Just one.\n"
    registry = tmp_path / "site" / "_data" / "agentculture_repos.yml"
    registry.parent.mkdir(parents=True)
    registry.write_text(minimal, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KATVAN_SIBLINGS_ROOT", raising=False)
    repos_mod.set_siblings_root(None)

    rc = overview_mod._handle(argparse.Namespace(json=False))
    assert rc == 0
    out = capsys.readouterr().out
    assert "Core Runtime" in out
    assert "Workspace Experience" not in out
    assert "Org Site" not in out


# --- _handle: json mode ----------------------------------------------------


def test_handle_json_emits_total_and_by_category(
    fake_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = argparse.Namespace(json=True)
    rc = overview_mod._handle(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 7
    assert "by_category" in payload
    by_cat = payload["by_category"]
    # All seven categories appear (six known + one oddball).
    assert set(by_cat) == {
        "workspace-experience",
        "core-runtime",
        "identity-secrets",
        "resident-culture",
        "resident-domain",
        "org-site",
        "experimental-future-thing",
    }
    # Each bucket carries dict entries with id+description.
    assert by_cat["workspace-experience"][0]["id"] == "alpha"
    assert by_cat["org-site"][0]["description"] == "Foxtrot site."
