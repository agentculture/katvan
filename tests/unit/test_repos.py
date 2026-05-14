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


@pytest.fixture()
def fake_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A temp dir laid out like a katvan checkout, with CWD pointed at a subdir."""
    registry = tmp_path / "site" / "_data" / "agentculture_repos.yml"
    registry.parent.mkdir(parents=True)
    registry.write_text(_FIXTURE_REGISTRY, encoding="utf-8")
    # Walk-up should find the registry even from a nested dir.
    nested = tmp_path / "docs" / "deep"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.delenv("KATVAN_SIBLINGS_ROOT", raising=False)
    repos_mod.set_siblings_root(None)
    yield tmp_path
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
