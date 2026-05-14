"""Smoke tests for the katvan CLI entry point."""

from __future__ import annotations

import subprocess
import sys

import pytest

from katvan import __version__
from katvan.cli import main


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert __version__ in out


def test_no_args_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "usage: katvan" in out


def test_learn_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["learn"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "katvan" in out
    assert "culture.dev" in out


def test_explain_learn_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["explain", "learn"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("# katvan learn")


def test_unknown_verb_exits_nonzero_with_hint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["zzz-not-a-real-verb"])
    assert exc.value.code != 0
    err = capsys.readouterr().err
    assert "error:" in err
    assert "hint:" in err


def test_python_dash_m_invocation() -> None:
    """`python -m katvan --version` exits 0 and prints the version."""
    result = subprocess.run(
        [sys.executable, "-m", "katvan", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout
