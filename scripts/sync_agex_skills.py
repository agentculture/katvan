#!/usr/bin/env python3
"""sync_agex_skills.py — render agex-cli SKILL.md files into katvan site pages.

Usage:
    python3 scripts/sync_agex_skills.py <path-to-agex-cli-checkout>

Reads ``<agex-cli>/src/agent_experience/commands/*/SKILL.md``, strips each
SKILL.md's own YAML frontmatter, prepends a Jekyll-friendly frontmatter
pointing at the ``Commands`` parent page, and writes the result to
``site/agex/commands/<verb>.md``. Also writes the ``Commands`` index page.

Deterministic by construction:
  * Inputs are sorted alphabetically (so nav order is stable).
  * Removed-upstream commands are deleted locally on re-run
    (``_clear_stale_pages``).
  * Re-running on unchanged input produces byte-identical output (CI relies
    on this so bot-PR diffs stay minimal).

stdlib only — no dependency on the ``agent_experience`` Python package or
PyYAML. The frontmatter shape we read is small enough for a hand parse.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = REPO_ROOT / "site" / "agex" / "commands"

_JEKYLL_FRONTMATTER = (
    "---\n"
    "title: {title}\n"
    "parent: Commands\n"
    "nav_order: {order}\n"
    "sites: [culture]\n"
    "permalink: /agex/commands/{name}/\n"
    "---\n\n"
)

_INDEX_PAGE = (
    "---\n"
    "title: Commands\n"
    "has_children: true\n"
    "nav_order: 3\n"
    "sites: [culture]\n"
    "permalink: /agex/commands/\n"
    "---\n\n"
    "# Commands\n\n"
    "Auto-imported from `agex-cli/src/agent_experience/commands/*/SKILL.md`"
    " by `scripts/sync_agex_skills.py`. Re-run via the nightly"
    " `reference-sync.yml` workflow or fire `workflow_dispatch` manually"
    " after a notable agex-cli change.\n"
)

_NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)


def parse_skill_md(text: str) -> tuple[str, str]:
    """Return (name, body) from a SKILL.md file.

    SKILL.md format: ``---\\n<yaml>\\n---\\n\\n<body>``. We extract the
    ``name:`` field from the YAML block and return everything after the
    closing fence (byte-for-byte).
    """
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md missing opening frontmatter fence")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md missing closing frontmatter fence")
    frontmatter = text[4:end]
    body = text[end + 5:]
    if body.startswith("\n"):
        body = body[1:]
    match = _NAME_RE.search(frontmatter)
    if not match:
        raise ValueError("SKILL.md frontmatter missing `name:` field")
    return match.group(1), body


def _commands_dir(agex_root: Path) -> Path:
    return agex_root / "src" / "agent_experience" / "commands"


def _top_level_skill_md(agex_root: Path) -> list[Path]:
    """Return alphabetical SKILL.md paths for the top-level command dirs."""
    cmds = _commands_dir(agex_root)
    return sorted(
        cmd_dir / "SKILL.md"
        for cmd_dir in cmds.iterdir()
        if cmd_dir.is_dir() and (cmd_dir / "SKILL.md").is_file()
    )


def _clear_stale_pages(out_dir: Path, expected: set[str]) -> None:
    """Remove out_dir/*.md not in ``expected``. Always re-writes index.md."""
    if not out_dir.exists():
        return
    for path in sorted(out_dir.glob("*.md")):
        if path.name in expected:
            continue
        path.unlink()


def render(agex_root: Path, out_dir: Path = DEFAULT_OUT_DIR) -> int:
    """Render all top-level SKILL.md files under agex_root into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    skills = _top_level_skill_md(agex_root)
    expected = {f"{p.parent.name}.md" for p in skills} | {"index.md"}
    _clear_stale_pages(out_dir, expected)
    for order, skill_md in enumerate(skills, start=1):
        slug = skill_md.parent.name
        title, body = parse_skill_md(skill_md.read_text(encoding="utf-8"))
        page = _JEKYLL_FRONTMATTER.format(
            title=title, order=order * 10, name=slug
        ) + body
        (out_dir / f"{slug}.md").write_text(page, encoding="utf-8")
    (out_dir / "index.md").write_text(_INDEX_PAGE, encoding="utf-8")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(
            "usage: sync_agex_skills.py <agex-cli-checkout-path>",
            file=sys.stderr,
        )
        return 2
    return render(Path(argv[1]).resolve())


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
