"""Tests for `katvan overview`."""
from __future__ import annotations

import json
import subprocess
import sys


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "katvan", "overview", *args],
        capture_output=True, text=True, check=False,
    )


def test_overview_text_lists_all_categories() -> None:
    result = _run()
    assert result.returncode == 0, result.stderr
    for header in (
        "Core Runtime", "Workspace Experience", "Identity & Secrets",
        "Resident Culture", "Resident Domain", "Org Site",
    ):
        assert header in result.stdout, f"missing header: {header}"


def test_overview_text_counts_total_repos() -> None:
    result = _run()
    assert result.returncode == 0, result.stderr
    assert "21 repos" in result.stdout


def test_overview_json_shape() -> None:
    result = _run("--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["total"] == 21
    assert set(payload["by_category"].keys()) == {
        "core-runtime", "workspace-experience", "identity-secrets",
        "resident-culture", "resident-domain", "org-site",
    }
    assert sum(len(v) for v in payload["by_category"].values()) == 21
