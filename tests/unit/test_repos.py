"""Unit tests for :mod:`katvan.repos` — the ported sibling-repo registry.

These exercise the registry walk-up, the line-oriented YAML parse, and the
classify / repos / local_path helpers. They use a synthetic registry fixture
written into a temp tree so they do not depend on the live
``site/_data/agentculture_repos.yml`` contents drifting.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from katvan import repos as repos_mod
from katvan.cli._errors import KatvanError

_FIXTURE_REGISTRY = """\
# Synthetic registry fixture for tests.
- id: agentirc
  category: core-runtime
  maturity: usable
  docs_mode: pull
  description: The IRC-native runtime.

- id: culture
  category: workspace-experience
  maturity: usable
  docs_mode: skip
  description: The integrated workspace.

- id: afi-cli
  category: workspace-experience
  maturity: usable
  docs_mode: self-published
  description: Agent-First Interface.
"""


def _reset_repos_caches() -> None:
    """Clear the lru_cache on _find_repo_root / _parse_registry / _parse_entries.

    All are memoized for process lifetime; tests deliberately point them at
    different temp checkouts, so the caches must be cleared between tests.
    """
    repos_mod._find_repo_root.cache_clear()
    repos_mod._parse_registry.cache_clear()
    repos_mod._parse_entries.cache_clear()


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    """Reset the memoization caches around every test (autouse)."""
    _reset_repos_caches()
    yield
    _reset_repos_caches()


def _write_checkout(tmp_path: Path, registry_text: str, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Lay out a temp dir like a katvan checkout and chdir into a nested subdir."""
    registry = tmp_path / "site" / "_data" / "agentculture_repos.yml"
    registry.parent.mkdir(parents=True)
    registry.write_text(registry_text, encoding="utf-8")
    nested = tmp_path / "docs" / "deep"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.delenv("KATVAN_SIBLINGS_ROOT", raising=False)
    repos_mod.set_siblings_root(None)
    return tmp_path


@pytest.fixture()
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A temp dir laid out like a katvan checkout, with CWD pointed at a subdir."""
    root = _write_checkout(tmp_path, _FIXTURE_REGISTRY, monkeypatch)
    yield root
    repos_mod.set_siblings_root(None)


def test_registry_path_walks_up_to_find_registry(fake_repo: Path) -> None:
    found = repos_mod.registry_path()
    assert found == fake_repo / "site" / "_data" / "agentculture_repos.yml"
    assert found.is_file()


def test_registry_path_raises_env_error_when_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(KatvanError) as exc:
        repos_mod.registry_path()
    assert exc.value.code == 2  # EXIT_ENV_ERROR


def test_classify_known_modes(fake_repo: Path) -> None:
    assert repos_mod.classify("agentirc") == "pull"
    assert repos_mod.classify("culture") == "skip"
    assert repos_mod.classify("afi-cli") == "self-published"


def test_classify_unknown_repo_returns_unknown(fake_repo: Path) -> None:
    assert repos_mod.classify("does-not-exist") == "unknown"


def test_repos_yields_id_mode_localpath_tuples(fake_repo: Path) -> None:
    rows = list(repos_mod.repos())
    assert [r[0] for r in rows] == ["agentirc", "culture", "afi-cli"]
    for repo_id, mode, local in rows:
        assert isinstance(repo_id, str) and repo_id
        assert mode in {"pull", "self-published", "skip"}
        assert isinstance(local, str)


def test_local_path_resolves_existing_sibling(
    fake_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    siblings = fake_repo.parent
    # agentirc checked out next to the repo; culture not.
    (siblings / "agentirc").mkdir(exist_ok=True)
    repos_mod.set_siblings_root(siblings)
    assert repos_mod.local_path("agentirc") == str(siblings / "agentirc")
    assert repos_mod.local_path("culture") == ""


def test_siblings_root_env_var_override(
    fake_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    custom = tmp_path / "elsewhere"
    custom.mkdir()
    monkeypatch.setenv("KATVAN_SIBLINGS_ROOT", str(custom))
    repos_mod.set_siblings_root(None)  # clear programmatic override
    assert repos_mod.siblings_root() == custom


def test_siblings_root_default_is_repo_parent(fake_repo: Path) -> None:
    # No env var, no override — default is the parent of the discovered root.
    assert repos_mod.siblings_root() == fake_repo.parent


def test_set_siblings_root_takes_precedence_over_env(
    fake_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KATVAN_SIBLINGS_ROOT", str(tmp_path / "from-env"))
    explicit = tmp_path / "from-setter"
    explicit.mkdir()
    repos_mod.set_siblings_root(explicit)
    assert repos_mod.siblings_root() == explicit


def test_main_prints_table(fake_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = repos_mod.main([])
    assert rc == 0
    out = capsys.readouterr().out
    assert "agentirc\tpull\t" in out
    assert "culture\tskip\t" in out


def test_main_classify_flag(fake_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = repos_mod.main(["--classify", "afi-cli"])
    assert rc == 0
    assert capsys.readouterr().out.strip() == "self-published"


def test_main_registry_path_flag(fake_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = repos_mod.main(["--registry-path"])
    assert rc == 0
    assert capsys.readouterr().out.strip().endswith("agentculture_repos.yml")


def test_main_surfaces_env_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    rc = repos_mod.main([])
    assert rc == 2
    err = capsys.readouterr().err
    assert "error:" in err
    assert "hint:" in err


def test_comment_only_registry_yields_zero_entries_without_erroring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registry with only comments / blank lines is legitimately empty."""
    _write_checkout(tmp_path, "# just a comment\n\n#   another\n\n", monkeypatch)
    assert list(repos_mod.repos()) == []
    assert repos_mod.classify("anything") == "unknown"


def test_quoted_ids_are_unquoted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``- id: "foo"`` / ``- id: 'bar'`` strip to ``foo`` / ``bar``."""
    registry = (
        '- id: "foo"\n'
        "  docs_mode: pull\n"
        "- id: 'bar'\n"
        "  docs_mode: skip\n"
    )
    _write_checkout(tmp_path, registry, monkeypatch)
    rows = list(repos_mod.repos())
    assert [r[0] for r in rows] == ["foo", "bar"]
    assert repos_mod.classify("foo") == "pull"
    assert repos_mod.classify("bar") == "skip"


def test_trailing_whitespace_on_docs_mode_is_parsed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``docs_mode:`` lines with trailing whitespace still parse correctly."""
    registry = "- id: spaced\n  docs_mode: pull   \n"
    _write_checkout(tmp_path, registry, monkeypatch)
    assert repos_mod.classify("spaced") == "pull"


def test_malformed_block_style_registry_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-empty registry with no inline ``- id:`` openers raises KatvanError."""
    registry = "-\n  id: blockstyle\n  docs_mode: pull\n"
    _write_checkout(tmp_path, registry, monkeypatch)
    with pytest.raises(KatvanError) as exc:
        list(repos_mod.repos())
    assert exc.value.code == 2  # EXIT_ENV_ERROR
    assert "zero entries" in exc.value.message


def test_main_classify_unknown_exits_nonzero(
    fake_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI shim exits non-zero for an unknown id (matching _repos.sh)."""
    rc = repos_mod.main(["--classify", "does-not-exist"])
    assert rc == 1  # EXIT_USER_ERROR
    assert capsys.readouterr().out.strip() == "unknown"


# --- entries() / _parse_entries() ----------------------------------------


def test_entries_returns_all_scalar_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registry with every scalar field populated → ``entries()`` carries them."""
    registry = (
        "- id: fully\n"
        "  category: workspace-experience\n"
        "  maturity: usable\n"
        "  docs_mode: pull\n"
        "  description: All fields populated.\n"
        "  package: fully-pkg\n"
        "  binary: fully-bin\n"
        "  docs: https://example.test/docs\n"
        "  site_path: /fully/\n"
        "  install: pip install fully-pkg\n"
        "  caveat: handle with care\n"
    )
    _write_checkout(tmp_path, registry, monkeypatch)
    out = repos_mod.entries()
    assert len(out) == 1
    entry = out[0]
    for key in (
        "id", "category", "maturity", "docs_mode", "description",
        "package", "binary", "docs", "site_path", "install", "caveat",
    ):
        assert key in entry, f"missing field: {key}"
    assert entry["id"] == "fully"
    assert entry["category"] == "workspace-experience"
    assert entry["caveat"] == "handle with care"
    assert entry["site_path"] == "/fully/"


def test_entries_skips_list_valued_fields_without_brackets_in_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``related: [a, b]`` style lines are silently dropped (not stored with brackets)."""
    registry = (
        "- id: skippy\n"
        "  category: core-runtime\n"
        "  docs_mode: pull\n"
        "  description: Has a related-list line.\n"
        "  install: [pip, install, skippy]\n"
    )
    _write_checkout(tmp_path, registry, monkeypatch)
    out = repos_mod.entries()
    assert len(out) == 1
    entry = out[0]
    # install is list-shaped → skipped entirely, not stored as a string.
    assert "install" not in entry
    # other scalars are still captured.
    assert entry["docs_mode"] == "pull"
    assert entry["description"] == "Has a related-list line."


def test_entries_multiple_rows_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two consecutive entries both surface, with the first preserved on the second's open."""
    registry = (
        "- id: one\n"
        "  category: core-runtime\n"
        "  description: First.\n"
        "- id: two\n"
        "  category: org-site\n"
        "  description: Second.\n"
    )
    _write_checkout(tmp_path, registry, monkeypatch)
    out = repos_mod.entries()
    assert [e["id"] for e in out] == ["one", "two"]
    assert out[0]["description"] == "First."
    assert out[1]["description"] == "Second."


def test_entries_unreadable_registry_raises_env_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registry path that points at a directory (read fails) surfaces EXIT_ENV_ERROR."""
    # Build a "checkout" where the registry path is a directory, not a file.
    site_data = tmp_path / "site" / "_data"
    site_data.mkdir(parents=True)
    fake_registry = site_data / "agentculture_repos.yml"
    fake_registry.mkdir()  # directory instead of file → read_text raises OSError
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("KATVAN_SIBLINGS_ROOT", raising=False)
    repos_mod.set_siblings_root(None)
    with pytest.raises(KatvanError) as exc:
        repos_mod._parse_entries(fake_registry)
    assert exc.value.code == 2  # EXIT_ENV_ERROR
    assert "not readable" in exc.value.message


def test_repos_skips_blank_id_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``- id:`` line with no value is skipped by ``repos()``."""
    registry = (
        "- id:\n"
        "  docs_mode: pull\n"
        "- id: real\n"
        "  docs_mode: skip\n"
    )
    _write_checkout(tmp_path, registry, monkeypatch)
    rows = list(repos_mod.repos())
    assert [r[0] for r in rows] == ["real"]


def test_entries_raises_when_registry_has_content_but_zero_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Belt-and-suspenders: ``_parse_entries`` must guard like ``_parse_registry``.

    A non-empty registry with no inline ``- id:`` openers used to silently
    yield zero entries from ``_parse_entries``, which let ``doctor`` report
    "ok (0 repos)" on a malformed file.
    """
    registry = "-\n  id: blockstyle\n  docs_mode: pull\n"
    _write_checkout(tmp_path, registry, monkeypatch)
    with pytest.raises(KatvanError) as exc:
        repos_mod.entries()
    assert exc.value.code == 1  # EXIT_USER_ERROR
    assert "zero entries" in exc.value.message


def test_entries_comment_only_registry_yields_zero_without_erroring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A comment-only registry is legitimately empty — no raise."""
    registry = "# only a comment, no entries\n\n   \n"
    _write_checkout(tmp_path, registry, monkeypatch)
    assert repos_mod.entries() == []


def test_real_registry_is_parseable() -> None:
    """Sanity check against the live registry (when run from a katvan checkout)."""
    # This test is environment-dependent; skip gracefully if not in a checkout.
    try:
        path = repos_mod.registry_path()
    except KatvanError:
        pytest.skip("not running inside a katvan checkout")
    assert path.name == "agentculture_repos.yml"
    rows = list(repos_mod.repos())
    assert rows, "live registry parsed to zero entries"
    assert all(len(r) == 3 for r in rows)
