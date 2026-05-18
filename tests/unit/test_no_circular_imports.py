"""Regression: importing katvan.gsc submodules from a cold interpreter must not fail."""
from __future__ import annotations

import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "module",
    ["katvan.gsc", "katvan.gsc.client", "katvan.gsc.inspect",
     "katvan.gsc.sitemaps", "katvan.gsc.doctor",
     "katvan.gsc._sitemap_fetch"],
)
def test_cold_import(module: str) -> None:
    """A fresh interpreter must be able to `import <module>` directly."""
    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
