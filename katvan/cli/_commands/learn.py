"""``katvan learn`` — the learnability affordance.

Prints a structured self-teaching prompt with enough shape that an agent can
author its own usage skill without scraping ``--help``. Also supports
``--json`` for agents that would rather parse structure than text.

Content satisfies the agent-first rubric's learnability bundle: ≥200 chars
and mentions purpose, command map, exit codes, ``--json``, and ``explain``.
"""

from __future__ import annotations

import argparse

from katvan import __version__
from katvan.cli._output import emit_result

_TEXT = """\
katvan — maintain sibling-repo docs under one roof on the culture.dev site.

Purpose
-------
katvan keeps the culture.dev Jekyll site's docs tree coherent: it surveys
which AgentCulture sibling repos are synced and fresh, pulls their raw
markdown docs/ trees into site/docs/<repo>/ with Jekyll frontmatter
injected, and diagnoses doc defects (missing frontmatter, broken links,
staleness). It is the librarian skill's logic, growing into a real CLI.

Commands
--------
  katvan learn              Print this self-teaching prompt. Supports --json.
  katvan explain <path>...  Print markdown docs for any noun/verb path; the
                            primary way for an agent to introspect katvan's
                            grammar. Supports --json.

The docs verbs — overview, pull, and doctor — are coming in a later
release, ported from the librarian skill.

Universal verb tier (agent-first)
---------------------------------
katvan exposes the universal agent-first verbs:

  - learn     — what is this tool?
  - explain   — what does this command do?

Machine-readable output
-----------------------
Every command that produces a listing or report supports --json. Errors in
JSON mode emit {"code", "message", "remediation"} to stderr. Stdout and
stderr are never mixed.

Exit-code policy
----------------
  0 success
  1 user-input error (bad flag, bad path, missing arg)
  2 environment / setup error (registry not found, unreadable file)
  3+ reserved

More detail
-----------
  katvan explain katvan
  katvan explain learn
  katvan explain explain

Homepage: https://github.com/agentculture/katvan
"""


def _as_json_payload() -> dict[str, object]:
    return {
        "tool": "katvan",
        "version": __version__,
        "purpose": ("Maintain sibling-repo docs under one roof on the culture.dev site."),
        "commands": [
            {"path": ["learn"], "summary": "Self-teaching prompt."},
            {"path": ["explain"], "summary": "Markdown docs by noun/verb path."},
        ],
        "coming_soon": [
            {"path": ["overview"], "summary": "Survey synced/fresh sibling docs."},
            {"path": ["pull"], "summary": "Sync a sibling's docs/ into the site."},
            {"path": ["doctor"], "summary": "Detect and report doc defects."},
        ],
        "exit_codes": {
            "0": "success",
            "1": "user-input error",
            "2": "environment/setup error",
        },
        "json_support": True,
        "explain_pointer": "katvan explain <path> (e.g. 'katvan explain learn')",
    }


def cmd_learn(args: argparse.Namespace) -> int:
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        emit_result(_as_json_payload(), json_mode=True)
    else:
        emit_result(_TEXT, json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "learn",
        help="Print a structured self-teaching prompt for agent consumers.",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_learn)
