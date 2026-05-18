"""Unit tests for scripts/sync_agex_skills.py."""
from __future__ import annotations

from pathlib import Path

import pytest

import sync_agex_skills as sync


def _write_skill(path: Path, name: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {name}\ndescription: test {name}\ntype: command\n---\n\n{body}\n")


def test_parse_skill_md_extracts_name_and_body():
    text = "---\nname: pr\ndescription: x\n---\n\n# body line\n"
    name, body = sync.parse_skill_md(text)
    assert name == "pr"
    assert body == "# body line\n"


def test_parse_skill_md_rejects_missing_opening_fence():
    with pytest.raises(ValueError, match="opening frontmatter fence"):
        sync.parse_skill_md("# body without frontmatter\n")


def test_parse_skill_md_rejects_missing_closing_fence():
    with pytest.raises(ValueError, match="closing frontmatter fence"):
        sync.parse_skill_md("---\nname: x\n")


def test_parse_skill_md_rejects_missing_name():
    with pytest.raises(ValueError, match="missing `name:`"):
        sync.parse_skill_md("---\ndescription: y\n---\n\n# body\n")


def test_render_writes_one_page_per_top_level_command(tmp_path: Path):
    src = tmp_path / "agex-src"
    out = tmp_path / "out"
    _write_skill(src / "src/agent_experience/commands/pr/SKILL.md", "pr", "# pr body")
    _write_skill(src / "src/agent_experience/commands/learn/SKILL.md", "learn", "# learn body")

    rc = sync.render(src, out)

    assert rc == 0
    assert sorted(p.name for p in out.iterdir()) == ["index.md", "learn.md", "pr.md"]


def test_render_jekyll_frontmatter_shape(tmp_path: Path):
    src = tmp_path / "agex-src"
    out = tmp_path / "out"
    _write_skill(src / "src/agent_experience/commands/pr/SKILL.md", "pr", "# pr body")

    sync.render(src, out)

    page = (out / "pr.md").read_text()
    assert page.startswith("---\n")
    assert "title: pr\n" in page
    assert "parent: Commands\n" in page
    assert "sites: [culture]\n" in page
    assert "permalink: /agex/commands/pr/\n" in page
    assert "nav_order: 10\n" in page
    assert page.endswith("# pr body\n")


def test_render_order_is_alphabetical_and_multiples_of_ten(tmp_path: Path):
    src = tmp_path / "agex-src"
    out = tmp_path / "out"
    for n in ["pr", "doctor", "explain"]:
        _write_skill(src / f"src/agent_experience/commands/{n}/SKILL.md", n, f"# {n}")

    sync.render(src, out)

    # Alphabetical: doctor=10, explain=20, pr=30
    assert "nav_order: 10\n" in (out / "doctor.md").read_text()
    assert "nav_order: 20\n" in (out / "explain.md").read_text()
    assert "nav_order: 30\n" in (out / "pr.md").read_text()


def test_render_writes_index_md(tmp_path: Path):
    src = tmp_path / "agex-src"
    out = tmp_path / "out"
    _write_skill(src / "src/agent_experience/commands/pr/SKILL.md", "pr", "# pr")

    sync.render(src, out)

    idx = (out / "index.md").read_text()
    assert "title: Commands\n" in idx
    assert "has_children: true\n" in idx
    assert "permalink: /agex/commands/\n" in idx
    assert "sites: [culture]\n" in idx


def test_render_clears_stale_pages(tmp_path: Path):
    src = tmp_path / "agex-src"
    out = tmp_path / "out"
    out.mkdir()
    (out / "removed-command.md").write_text("stale\n")
    _write_skill(src / "src/agent_experience/commands/pr/SKILL.md", "pr", "# pr")

    sync.render(src, out)

    assert not (out / "removed-command.md").exists()
    assert (out / "pr.md").exists()
    assert (out / "index.md").exists()


def test_render_skips_directories_without_skill_md(tmp_path: Path):
    src = tmp_path / "agex-src"
    out = tmp_path / "out"
    _write_skill(src / "src/agent_experience/commands/pr/SKILL.md", "pr", "# pr")
    # Subdirectory without SKILL.md: must not be rendered (matches sync_skill_md.py's
    # "top-level only" rule — assets/, scripts/, __pycache__ are not commands).
    (src / "src/agent_experience/commands/pr/assets").mkdir(parents=True)
    (src / "src/agent_experience/commands/__pycache__").mkdir(parents=True)

    sync.render(src, out)

    assert sorted(p.name for p in out.iterdir()) == ["index.md", "pr.md"]


def test_main_rejects_wrong_argv():
    assert sync.main(["sync_agex_skills.py"]) == 2
    assert sync.main(["sync_agex_skills.py", "a", "b"]) == 2
