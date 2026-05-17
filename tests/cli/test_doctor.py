"""Tests for `katvan doctor`."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def site_tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    site = tmp_path / "site"
    (site / "_data").mkdir(parents=True)
    (site / "_data" / "agentculture_repos.yml").write_text(
        """- id: alpha
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
    )
    monkeypatch.chdir(tmp_path)
    return site


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "katvan", "doctor", *args],
        capture_output=True, text=True, check=False,
    )


def test_doctor_fails_when_index_missing(site_tree: Path) -> None:
    result = _run()
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "alpha" in combined
    assert "index.md" in combined


def test_doctor_passes_when_all_required_present(site_tree: Path) -> None:
    for repo_id in ("alpha", "beta"):
        page = site_tree / "docs" / repo_id / "index.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(f"# {repo_id}\n\nReal content.\n")
    ref = site_tree / "docs" / "alpha" / "reference" / "index.md"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text("# alpha reference\n")
    result = _run()
    assert result.returncode == 0, result.stdout + result.stderr


def test_doctor_json_lists_failures(site_tree: Path) -> None:
    result = _run("--json")
    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert any(f["id"] == "alpha" for f in payload["failures"])


def test_doctor_skips_readme_check_when_sibling_not_checked_out(site_tree: Path) -> None:
    for repo_id in ("alpha", "beta"):
        page = site_tree / "docs" / repo_id / "index.md"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(f"# {repo_id}\n\nReal content.\n")
    ref = site_tree / "docs" / "alpha" / "reference" / "index.md"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_text("ref")
    result = _run()
    assert result.returncode == 0
