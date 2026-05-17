"""In-process unit tests for :mod:`katvan.cli._commands.pull`.

The corresponding tests under ``tests/cli/test_pull.py`` spawn
``python -m katvan`` as a subprocess (and depend on a fake AFI binary on
PATH). These tests call the verb helpers directly so the body of ``pull.py``
is instrumented by pytest-cov.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pytest

from katvan import repos as repos_mod
from katvan.cli._commands import pull as pull_mod
from katvan.cli._errors import EXIT_INTERNAL_ERROR, EXIT_USER_ERROR, KatvanError

_FIXTURE_REGISTRY = """\
- id: fakecli
  category: workspace-experience
  maturity: experimental
  docs_mode: pull-reference
  binary: fakecli
  description: A fake sibling.
- id: skippy
  category: org-site
  docs_mode: skip
  description: A skip-mode sibling.
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


# --- _render_* helpers ------------------------------------------------------


def test_render_index_emits_frontmatter_title_and_links() -> None:
    entry = {"id": "fakecli", "description": "fallback"}
    learn = {"summary": "summary text", "nouns": ["noun-b", "noun-a"]}
    out = pull_mod._render_index(entry, learn)
    assert out.startswith("---\n")
    assert "title: fakecli reference" in out
    assert "parent: fakecli" in out
    assert "nav_order: 1" in out
    assert "# fakecli reference" in out
    assert "summary text" in out
    # learn link present.
    assert "- [learn](learn.md)" in out
    # nouns appear sorted: noun-a before noun-b.
    a_idx = out.index("explain noun-a")
    b_idx = out.index("explain noun-b")
    assert a_idx < b_idx


def test_render_index_falls_back_to_description_without_summary() -> None:
    entry = {"id": "fakecli", "description": "from description"}
    learn = {"nouns": []}
    out = pull_mod._render_index(entry, learn)
    assert "from description" in out


def test_render_learn_uses_binary_or_id_in_header() -> None:
    entry = {"id": "fakecli"}  # no binary key
    out = pull_mod._render_learn(entry, {"k": 1})
    assert "title: fakecli learn" in out
    assert "# `fakecli learn`" in out
    assert '"k": 1' in out

    entry2 = {"id": "fakecli", "binary": "fake-bin"}
    out2 = pull_mod._render_learn(entry2, {})
    assert "# `fake-bin learn`" in out2


def test_render_explain_sorts_json_keys() -> None:
    payload = {"z": 1, "a": 2}
    out = pull_mod._render_explain("noun/verb", payload)
    assert "title: explain noun/verb" in out
    assert "# `explain noun/verb`" in out
    # sort_keys=True ⇒ "a" appears before "z" in the dumped JSON.
    a = out.index('"a"')
    z = out.index('"z"')
    assert a < z


# --- _invoke_json -----------------------------------------------------------


def test_invoke_json_returns_parsed_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd, capture_output, text, check):
        return subprocess.CompletedProcess(cmd, 0, stdout='{"hello": "world"}', stderr="")

    monkeypatch.setattr(pull_mod.subprocess, "run", fake_run)
    assert pull_mod._invoke_json("anything", ["learn", "--json"]) == {"hello": "world"}


def test_invoke_json_handles_empty_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd, capture_output, text, check):
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(pull_mod.subprocess, "run", fake_run)
    assert pull_mod._invoke_json("anything", ["learn", "--json"]) == {}


def test_invoke_json_raises_on_nonzero_return(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd, capture_output, text, check):
        return subprocess.CompletedProcess(cmd, 2, stdout="", stderr="boom")

    monkeypatch.setattr(pull_mod.subprocess, "run", fake_run)
    with pytest.raises(KatvanError) as exc:
        pull_mod._invoke_json("anything", ["learn", "--json"])
    assert exc.value.code == EXIT_INTERNAL_ERROR
    assert "exited 2" in exc.value.message
    assert "boom" in exc.value.message


# --- _select_targets --------------------------------------------------------


def test_select_targets_all_returns_full_registry(fake_repo: Path) -> None:
    args = argparse.Namespace(all=True, repo=None)
    targets = list(pull_mod._select_targets(args))
    assert [t["id"] for t in targets] == ["fakecli", "skippy"]


def test_select_targets_specific_id(fake_repo: Path) -> None:
    args = argparse.Namespace(all=False, repo="fakecli")
    targets = list(pull_mod._select_targets(args))
    assert len(targets) == 1
    assert targets[0]["id"] == "fakecli"


def test_select_targets_unknown_id_raises(fake_repo: Path) -> None:
    args = argparse.Namespace(all=False, repo="nope")
    with pytest.raises(KatvanError) as exc:
        list(pull_mod._select_targets(args))
    assert exc.value.code == EXIT_USER_ERROR
    assert "unknown repo id: nope" in exc.value.message


# --- _handle ----------------------------------------------------------------


def test_handle_requires_repo_or_all(fake_repo: Path) -> None:
    args = argparse.Namespace(repo=None, all=False, json=False)
    with pytest.raises(KatvanError) as exc:
        pull_mod._handle(args)
    assert exc.value.code == EXIT_USER_ERROR
    assert "specify a repo id" in exc.value.message


def test_handle_pulls_and_skips_correctly(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--all`` exercises both the ``pulled`` and ``skipped`` paths."""
    calls: list[str] = []

    def fake_pull_one(site_root: Path, entry: dict) -> None:
        calls.append(entry["id"])

    monkeypatch.setattr(pull_mod, "_pull_one", fake_pull_one)
    args = argparse.Namespace(repo=None, all=True, json=False)
    rc = pull_mod._handle(args)
    assert rc == 0
    assert calls == ["fakecli"]
    out = capsys.readouterr().out
    assert "pulled: fakecli" in out
    assert "skipped: skippy" in out


def test_handle_single_repo_pulls(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(pull_mod, "_pull_one", lambda site_root, entry: None)
    args = argparse.Namespace(repo="fakecli", all=False, json=False)
    rc = pull_mod._handle(args)
    assert rc == 0
    assert "pulled: fakecli" in capsys.readouterr().out


def test_handle_json_emits_summary(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(pull_mod, "_pull_one", lambda site_root, entry: None)
    args = argparse.Namespace(repo=None, all=True, json=True)
    rc = pull_mod._handle(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pulled"] == ["fakecli"]
    assert payload["skipped"] == ["skippy"]
    assert payload["failed"] == []


def test_handle_records_failed_pulls(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def boom(site_root: Path, entry: dict) -> None:
        raise RuntimeError("disk full")

    monkeypatch.setattr(pull_mod, "_pull_one", boom)
    args = argparse.Namespace(repo="fakecli", all=False, json=False)
    rc = pull_mod._handle(args)
    # Failures cause a non-zero exit code.
    assert rc == 1
    out = capsys.readouterr().out
    assert "failed: fakecli: disk full" in out


def test_handle_json_with_failed(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def boom(site_root: Path, entry: dict) -> None:
        raise RuntimeError("oops")

    monkeypatch.setattr(pull_mod, "_pull_one", boom)
    args = argparse.Namespace(repo="fakecli", all=False, json=True)
    rc = pull_mod._handle(args)
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["failed"][0]["id"] == "fakecli"
    assert "oops" in payload["failed"][0]["error"]


# --- _pull_one (light integration via monkeypatched _invoke_json) ----------


def test_pull_one_writes_expected_tree(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stub ``_invoke_json`` so ``_pull_one`` runs purely in-process."""
    site_root = fake_repo / "site"
    entry = {"id": "fakecli", "binary": "fakecli", "description": "x"}

    def fake_invoke(binary: str, args: list[str]) -> dict:
        if args[0] == "learn":
            return {"summary": "s", "nouns": ["thing"]}
        # explain calls: explain "thing" → carries verbs; explain "thing/do" → leaf
        if args == ["explain", "thing", "--json"]:
            return {"verbs": ["do"]}
        if args == ["explain", "thing/do", "--json"]:
            return {"detail": True}
        raise AssertionError(f"unexpected: {args}")

    monkeypatch.setattr(pull_mod, "_invoke_json", fake_invoke)
    pull_mod._pull_one(site_root, entry)

    ref = site_root / "docs" / "fakecli" / "reference"
    assert (ref / "index.md").is_file()
    assert (ref / "learn.md").is_file()
    assert (ref / "explain" / "thing.md").is_file()
    assert (ref / "explain" / "thing" / "do.md").is_file()


def test_pull_one_clears_reference_before_writes(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Determinism: reference/ is rewritten from scratch each call.

    A noun / verb removed upstream must vanish locally too. We seed the
    reference tree with a stale file that no longer maps to a current noun
    and assert that ``_pull_one`` deletes it.
    """
    site_root = fake_repo / "site"
    entry = {"id": "fakecli", "binary": "fakecli", "description": "x"}

    # Seed a stale file at the path of a noun that won't be regenerated.
    stale = site_root / "docs" / "fakecli" / "reference" / "explain" / "removed-upstream.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale content from a previous run\n")

    def fake_invoke(binary: str, args: list[str]) -> dict:
        if args[0] == "learn":
            return {"summary": "s", "nouns": ["thing"]}
        if args == ["explain", "thing", "--json"]:
            return {"verbs": []}
        raise AssertionError(f"unexpected: {args}")

    monkeypatch.setattr(pull_mod, "_invoke_json", fake_invoke)
    pull_mod._pull_one(site_root, entry)

    # Stale file is gone, new tree is present.
    assert not stale.exists(), "stale upstream-removed noun should be deleted"
    ref = site_root / "docs" / "fakecli" / "reference"
    assert (ref / "index.md").is_file()
    assert (ref / "explain" / "thing.md").is_file()


def test_pull_one_preserves_existing_tree_when_binary_missing(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression guard: when ``_invoke_json`` raises on the first ``learn`` call
    (e.g. the sibling binary isn't installed in CI), the existing committed
    ``reference/`` tree MUST be left intact — no destructive rmtree before we
    know we have replacement content.
    """
    site_root = fake_repo / "site"
    entry = {"id": "fakecli", "binary": "fakecli", "description": "x"}

    # Seed a committed reference tree that resembles what CI would have on disk.
    ref = site_root / "docs" / "fakecli" / "reference"
    (ref / "explain").mkdir(parents=True)
    index = ref / "index.md"
    index.write_text("# committed reference content\n")
    learn_md = ref / "learn.md"
    learn_md.write_text("# committed learn\n")
    explain_stub = ref / "explain" / "noun.md"
    explain_stub.write_text("# committed explain\n")

    def fake_invoke(binary: str, args: list[str]) -> dict:
        # Simulate the sibling binary being absent — same shape as the real
        # error from ``_invoke_json`` when the subprocess call fails.
        raise KatvanError(
            code=EXIT_INTERNAL_ERROR,
            message=f"{binary} not found",
            remediation="install it",
        )

    monkeypatch.setattr(pull_mod, "_invoke_json", fake_invoke)

    with pytest.raises(KatvanError):
        pull_mod._pull_one(site_root, entry)

    # Committed content survives — the rmtree must NOT have run.
    assert index.is_file(), "committed reference/index.md must be preserved"
    assert learn_md.is_file(), "committed reference/learn.md must be preserved"
    assert explain_stub.is_file(), "committed explain stub must be preserved"
    assert index.read_text() == "# committed reference content\n"


def test_render_functions_emit_sites_culture_frontmatter() -> None:
    """Generated reference markdown must carry ``sites: [culture]`` frontmatter."""
    entry = {"id": "fakecli"}
    learn = {"nouns": []}
    assert "sites: [culture]" in pull_mod._render_index(entry, learn)
    assert "sites: [culture]" in pull_mod._render_learn(entry, {})
    assert "sites: [culture]" in pull_mod._render_explain("noun", {})
