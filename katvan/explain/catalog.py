"""Markdown catalog for ``katvan explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty
tuple and ``("katvan",)`` both resolve to the root entry (aliased).

Keep bodies self-contained — an agent reading a single entry should get
enough context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# katvan

katvan maintains the docs of sibling AgentCulture repos under one roof on
the culture.dev Jekyll site. It surveys which siblings are synced and
fresh, pulls their raw-markdown `docs/` trees into `site/docs/<repo>/` with
Jekyll frontmatter injected, and diagnoses doc defects. It is the
`librarian` skill's logic, migrating into a real installable CLI.

## Verbs

- `katvan learn` — structured self-teaching prompt.
- `katvan explain <path>` — markdown docs for any noun/verb.

The docs verbs — `overview`, `pull`, and `doctor` — land in a later
release, ported from the librarian skill.

## Universal verb tier (agent-first)

katvan exposes the universal agent-first verbs:

- `learn` — what is this tool?
- `explain <path>` — what does this command do?

## Exit-code policy

- `0` success
- `1` user-input error (bad flag, bad path, missing arg)
- `2` environment / setup error (registry not found, unreadable file)
- `3+` reserved

## See also

- `katvan explain learn`
- `katvan explain explain`
"""

_LEARN = """\
# katvan learn

Prints a structured self-teaching prompt covering katvan's purpose, command
map, exit-code policy, `--json` support, and `explain` pointer.

## Usage

    katvan learn
    katvan learn --json

In JSON mode, emits
`{"tool", "version", "purpose", "commands", "coming_soon", "exit_codes",
"json_support", "explain_pointer"}` to stdout.

## Rubric role

`learn` is the learnability bundle of the agent-first rubric. Any CLI that
passes it prints ≥200 characters and mentions purpose, commands, exit
codes, `--json`, and `explain`.
"""

_EXPLAIN = """\
# katvan explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help`
(terse, positional), `explain` is global and addressable by path.

## Usage

    katvan explain katvan
    katvan explain learn
    katvan explain explain --json

In text mode emits the markdown to stdout. In JSON mode emits
`{"path": [...], "markdown": "..."}` to stdout.

## Path resolution

Paths are shell-tokenised: `katvan explain learn` resolves to the catalog
entry `("learn",)`. Unknown paths exit `1` with a `hint:` pointing at
`katvan explain katvan` for the top-level map.

## Rubric role

`explain` is the explain bundle of the agent-first rubric: every registered
noun must resolve, and bad paths must exit non-zero with remediation.
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    ("katvan",): _ROOT,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
}
