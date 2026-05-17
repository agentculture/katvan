"""`katvan overview` — per-category registry summary.

Reads ``site/_data/agentculture_repos.yml`` and emits either a human-readable
breakdown grouped by category or a JSON payload of the same shape.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from typing import Any

from katvan import repos
from katvan.cli._output import emit_result

_CATEGORY_ORDER: tuple[tuple[str, str], ...] = (
    ("workspace-experience", "Workspace Experience"),
    ("core-runtime", "Core Runtime"),
    ("identity-secrets", "Identity & Secrets"),
    ("resident-culture", "Resident Culture"),
    ("resident-domain", "Resident Domain"),
    ("org-site", "Org Site"),
)


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "overview",
        help="per-category summary of the sibling-repo registry",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.set_defaults(func=_handle)


def _handle(args: argparse.Namespace) -> None:
    """Print the registry overview.

    No failure path — registry-parse errors raise :class:`KatvanError` upstream
    in ``repos.entries()``. The dispatcher in :mod:`katvan.cli` translates a
    ``None`` return into exit code 0.
    """
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in repos.entries():
        grouped[entry["category"]].append(entry)
    total = sum(len(v) for v in grouped.values())

    if args.json:
        emit_result({"total": total, "by_category": dict(grouped)}, json_mode=True)
        return

    print(f"AgentCulture registry — {total} repos")
    print()
    for cat_id, cat_label in _CATEGORY_ORDER:
        items = grouped.get(cat_id, [])
        if not items:
            continue
        print(f"{cat_label} ({len(items)})")
        for entry in items:
            print(f"  - {entry['id']}: {entry['description']}")
        print()
