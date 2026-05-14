"""Tests for :mod:`katvan.explain` and the ``katvan explain`` command."""

from __future__ import annotations

import json

import pytest

from katvan.cli import main
from katvan.cli._errors import KatvanError
from katvan.explain import known_paths, resolve


def test_resolve_root_path_returns_markdown() -> None:
    text = resolve(())
    assert text.startswith("# katvan")


def test_resolve_katvan_alias_matches_root() -> None:
    assert resolve(("katvan",)) == resolve(())


def test_resolve_known_verbs() -> None:
    for path in [("learn",), ("explain",)]:
        assert resolve(path).startswith("#")


def test_resolve_unknown_path_raises_katvan_error() -> None:
    with pytest.raises(KatvanError) as exc:
        resolve(("nope",))
    assert exc.value.code == 1
    assert "no explain entry" in exc.value.message
    assert "katvan explain katvan" in exc.value.remediation


def test_known_paths_covers_core_entries() -> None:
    paths = set(known_paths())
    assert () in paths
    assert ("katvan",) in paths
    assert ("learn",) in paths
    assert ("explain",) in paths


def test_cli_explain_root_prints_markdown(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["explain", "katvan"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("# katvan")


def test_cli_explain_learn_prints_markdown(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["explain", "learn"])
    assert rc == 0
    assert "# katvan learn" in capsys.readouterr().out


def test_cli_explain_json_shape(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["explain", "learn", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["path"] == ["learn"]
    assert payload["markdown"].startswith("# katvan learn")


def test_cli_explain_unknown_path_exits_nonzero_with_hint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["explain", "nope"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "error:" in err
    assert "hint:" in err


def test_cli_explain_empty_path_resolves_to_root(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["explain"])
    assert rc == 0
    assert capsys.readouterr().out.startswith("# katvan")
