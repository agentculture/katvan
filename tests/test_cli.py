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


def test_internal_crash_exits_three_with_bug_hint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A handler raising a plain (non-KatvanError) exception exits 3, not 1.

    Exit 1 is the user-input code; an internal crash is a bug in katvan and
    must be distinguishable for scripts/agents (see _errors.EXIT_INTERNAL_ERROR).
    """
    import argparse

    from katvan.cli import _dispatch

    def _boom(_args: argparse.Namespace) -> int:
        raise RuntimeError("boom")

    ns = argparse.Namespace(func=_boom, json=False)
    rc = _dispatch(ns)
    assert rc == 3
    err = capsys.readouterr().err
    assert "file a bug" in err


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
