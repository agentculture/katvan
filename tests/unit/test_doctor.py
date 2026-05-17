"""In-process unit tests for :mod:`katvan.cli._commands.doctor`.

The corresponding tests under ``tests/cli/test_doctor.py`` spawn
``python -m katvan`` as a subprocess and are not picked up by pytest-cov.
These tests call the check helpers and ``_handle()`` directly.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from katvan import repos as repos_mod
from katvan.cli._commands import doctor as doctor_mod

_FIXTURE_REGISTRY = """\
- id: alpha
  category: core-runtime
  maturity: usable
  docs_mode: pull-reference
  description: Alpha repo.
- id: beta
  category: org-site
  maturity: usable
  docs_mode: skip
  description: Beta repo.
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
    registry = tmp_path / "site" / "_data" / "agentculture_repos.yml"
    registry.parent.mkdir(parents=True)
    registry.write_text(_FIXTURE_REGISTRY, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KATVAN_SIBLINGS_ROOT", raising=False)
    repos_mod.set_siblings_root(None)
    yield tmp_path
    repos_mod.set_siblings_root(None)


# --- _check_index ----------------------------------------------------------


def test_check_index_missing_file(tmp_path: Path) -> None:
    msg = doctor_mod._check_index(tmp_path, {"id": "alpha"})
    assert msg is not None
    assert "missing site/docs/alpha/index.md" in msg


def test_check_index_empty_file(tmp_path: Path) -> None:
    page = tmp_path / "docs" / "alpha" / "index.md"
    page.parent.mkdir(parents=True)
    page.write_text("   \n\n")
    msg = doctor_mod._check_index(tmp_path, {"id": "alpha"})
    assert msg is not None
    assert "is empty" in msg


def test_check_index_populated_file_returns_none(tmp_path: Path) -> None:
    page = tmp_path / "docs" / "alpha" / "index.md"
    page.parent.mkdir(parents=True)
    page.write_text("# Alpha\n\nReal content.\n")
    assert doctor_mod._check_index(tmp_path, {"id": "alpha"}) is None


# --- _check_reference ------------------------------------------------------


def test_check_reference_skip_mode_returns_none(tmp_path: Path) -> None:
    """``docs_mode != pull-reference`` short-circuits the check."""
    assert doctor_mod._check_reference(tmp_path, {"id": "beta", "docs_mode": "skip"}) is None


def test_check_reference_missing_when_required(tmp_path: Path) -> None:
    entry = {"id": "alpha", "docs_mode": "pull-reference"}
    msg = doctor_mod._check_reference(tmp_path, entry)
    assert msg is not None
    assert "missing site/docs/alpha/reference/index.md" in msg
    assert "katvan pull alpha" in msg


def test_check_reference_present(tmp_path: Path) -> None:
    ref = tmp_path / "docs" / "alpha" / "reference" / "index.md"
    ref.parent.mkdir(parents=True)
    ref.write_text("# alpha reference\n")
    entry = {"id": "alpha", "docs_mode": "pull-reference"}
    assert doctor_mod._check_reference(tmp_path, entry) is None


# --- _check_readme_link ----------------------------------------------------


def test_check_readme_link_no_sibling_checkout_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the sibling repo isn't checked out locally, the check is skipped."""
    monkeypatch.setattr(doctor_mod.repos, "siblings_root", lambda: tmp_path / "nowhere")
    assert doctor_mod._check_readme_link({"id": "alpha"}) is None


def test_check_readme_link_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sib = tmp_path / "alpha"
    sib.mkdir()
    (sib / "README.md").write_text("See https://culture.dev/alpha/ for docs.\n")
    monkeypatch.setattr(doctor_mod.repos, "siblings_root", lambda: tmp_path)
    assert doctor_mod._check_readme_link({"id": "alpha"}) is None


def test_check_readme_link_missing_warns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sib = tmp_path / "alpha"
    sib.mkdir()
    (sib / "README.md").write_text("No link here.\n")
    monkeypatch.setattr(doctor_mod.repos, "siblings_root", lambda: tmp_path)
    msg = doctor_mod._check_readme_link({"id": "alpha"})
    assert msg is not None
    assert "missing link to https://culture.dev/alpha/" in msg


# --- _handle: text + json end-to-end ---------------------------------------


def test_handle_text_reports_failures_and_returns_nonzero(
    fake_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = doctor_mod._handle(argparse.Namespace(json=False))
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAIL [alpha]" in out
    assert "index.md" in out


def test_handle_text_passes_when_all_present(
    fake_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    site = fake_repo / "site"
    for repo_id in ("alpha", "beta"):
        page = site / "docs" / repo_id / "index.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(f"# {repo_id}\n\nContent.\n")
    ref = site / "docs" / "alpha" / "reference" / "index.md"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text("# alpha reference\n")

    rc = doctor_mod._handle(argparse.Namespace(json=False))
    assert rc == 0
    out = capsys.readouterr().out
    assert "doctor: ok (2 repos)" in out


def test_handle_json_emits_failure_summary(
    fake_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = doctor_mod._handle(argparse.Namespace(json=True))
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert any(f["id"] == "alpha" for f in payload["failures"])
    assert isinstance(payload["warnings"], list)


def test_handle_fails_on_empty_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Belt-and-suspenders: an empty registry must surface a failure, not 'ok (0 repos)'."""
    registry = tmp_path / "site" / "_data" / "agentculture_repos.yml"
    registry.parent.mkdir(parents=True)
    registry.write_text("# only a comment, no entries\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KATVAN_SIBLINGS_ROOT", raising=False)
    repos_mod.set_siblings_root(None)
    rc = doctor_mod._handle(argparse.Namespace(json=False))
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAIL [<registry>]" in out
    assert "registry is empty" in out


def test_handle_emits_warnings_for_readme_links(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Sibling README without the culture.dev link surfaces a warning."""
    site = fake_repo / "site"
    for repo_id in ("alpha", "beta"):
        page = site / "docs" / repo_id / "index.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(f"# {repo_id}\n\nContent.\n")
    ref = site / "docs" / "alpha" / "reference" / "index.md"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text("# alpha reference\n")

    # Point siblings_root at a tmp tree with an alpha sibling whose README
    # lacks the expected link.
    siblings = fake_repo / "_siblings"
    (siblings / "alpha").mkdir(parents=True)
    (siblings / "alpha" / "README.md").write_text("No link here.\n")
    monkeypatch.setattr(doctor_mod.repos, "siblings_root", lambda: siblings)

    rc = doctor_mod._handle(argparse.Namespace(json=False))
    assert rc == 0
    out = capsys.readouterr().out
    assert "WARN [alpha]" in out
