"""Tests for `katvan pull`."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


FIXTURE_BIN = Path(__file__).parent.parent / "fixtures" / "fake_afi_bin.py"


@pytest.fixture
def fake_sibling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    site = tmp_path / "site"
    (site / "_data").mkdir(parents=True)
    (site / "_data" / "agentculture_repos.yml").write_text(
        """- id: fakecli
  category: workspace-experience
  maturity: experimental
  docs_mode: pull-reference
  binary: fakecli
  description: A fake sibling for tests.
"""
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "fakecli").symlink_to(FIXTURE_BIN)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.chdir(tmp_path)
    return site


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "katvan", "pull", *args],
        capture_output=True, text=True, check=False,
    )


def test_pull_one_repo_writes_reference_tree(fake_sibling: Path) -> None:
    result = _run("fakecli")
    assert result.returncode == 0, result.stderr
    ref = fake_sibling / "docs" / "fakecli" / "reference"
    assert (ref / "index.md").is_file()
    assert (ref / "learn.md").is_file()
    assert (ref / "explain").is_dir()


def test_pull_all_skips_skip_mode(fake_sibling: Path) -> None:
    yml = fake_sibling / "_data" / "agentculture_repos.yml"
    yml.write_text(yml.read_text() + """
- id: skippy
  category: org-site
  maturity: experimental
  docs_mode: skip
  description: Skipped.
""")
    result = _run("--all")
    assert result.returncode == 0, result.stderr
    assert (fake_sibling / "docs" / "fakecli" / "reference").is_dir()
    assert not (fake_sibling / "docs" / "skippy").exists()


def test_pull_deterministic_output(fake_sibling: Path) -> None:
    _run("fakecli")
    first = (fake_sibling / "docs" / "fakecli" / "reference" / "learn.md").read_text()
    _run("fakecli")
    second = (fake_sibling / "docs" / "fakecli" / "reference" / "learn.md").read_text()
    assert first == second, "pull must be idempotent / deterministic"


def test_pull_json_emits_summary(fake_sibling: Path) -> None:
    result = _run("--all", "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["pulled"] == ["fakecli"]
    assert payload["skipped"] == []
    assert payload["failed"] == []
