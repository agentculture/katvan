"""Tests for ``katvan learn`` — ensures it satisfies the learnability rubric.

The learnability bundle requires stdout ≥ 200 chars and mentions of:
purpose, commands, exit codes, ``--json``, ``explain``.
"""

from __future__ import annotations

import json

import pytest

from katvan.cli import main


def test_learn_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn"]) == 0


def test_learn_output_meets_min_length(capsys: pytest.CaptureFixture[str]) -> None:
    main(["learn"])
    assert len(capsys.readouterr().out) >= 200


@pytest.mark.parametrize(
    "marker",
    ["purpose", "Commands", "exit", "--json", "explain"],
)
def test_learn_mentions_required_marker(capsys: pytest.CaptureFixture[str], marker: str) -> None:
    main(["learn"])
    out = capsys.readouterr().out
    # Case-insensitive — the rubric checks for the concept, not specific casing.
    assert marker.lower() in out.lower(), f"missing marker: {marker}"


def test_learn_json_mode_emits_parseable_structure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["learn", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tool"] == "katvan"
    assert "purpose" in payload
    assert isinstance(payload["commands"], list) and payload["commands"]
    assert "0" in payload["exit_codes"]
    assert payload["json_support"] is True
    assert "explain_pointer" in payload


def test_learn_json_does_not_claim_unregistered_verbs(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """overview/pull/doctor are not registered yet — they live under coming_soon."""
    main(["learn", "--json"])
    payload = json.loads(capsys.readouterr().out)
    command_paths = {tuple(c["path"]) for c in payload["commands"]}
    assert command_paths == {("learn",), ("explain",)}
    coming = {tuple(c["path"]) for c in payload["coming_soon"]}
    assert coming == {("overview",), ("pull",), ("doctor",)}
