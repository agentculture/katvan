"""`katvan doctor` — culture.dev IA health check.

Required (failures): hand-authored ``site/docs/<id>/index.md`` for every
registered repo; ``site/docs/<id>/reference/index.md`` for every repo with
``docs_mode: pull-reference``.

Best-effort (warnings): sibling README links to ``https://culture.dev/<id>/``,
checked only when the sibling is checked out under ``siblings_root()``.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from katvan import repos
from katvan.cli._output import emit_result


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("doctor", help="check culture.dev IA health")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    parser.set_defaults(func=_handle)


def _check_index(site_root: Path, entry: dict) -> str | None:
    page = site_root / "docs" / entry["id"] / "index.md"
    if not page.is_file():
        return f"missing site/docs/{entry['id']}/index.md (hand-authored page)"
    if not page.read_text().strip():
        return f"site/docs/{entry['id']}/index.md is empty"
    return None


def _check_reference(site_root: Path, entry: dict) -> str | None:
    if entry.get("docs_mode") != "pull-reference":
        return None
    ref = site_root / "docs" / entry["id"] / "reference" / "index.md"
    if not ref.is_file():
        return f"missing site/docs/{entry['id']}/reference/index.md (run `katvan pull {entry['id']}`)"
    return None


def _check_readme_link(entry: dict) -> str | None:
    sibling = repos.siblings_root() / entry["id"]
    readme = sibling / "README.md"
    if not readme.is_file():
        return None
    expected = f"https://culture.dev/{entry['id']}/"
    if expected not in readme.read_text():
        return f"warning: {sibling}/README.md missing link to {expected}"
    return None


def _handle(args: argparse.Namespace) -> int:
    site_root = repos.registry_path().parent.parent
    failures: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    entries = list(repos.entries())
    if not entries:
        failures.append(
            {
                "id": "<registry>",
                "message": (
                    "registry is empty — no repos to check; "
                    "verify site/_data/agentculture_repos.yml has entries"
                ),
            }
        )
    for entry in entries:
        for check in (_check_index, _check_reference):
            msg = check(site_root, entry)
            if msg:
                failures.append({"id": entry["id"], "message": msg})
        msg = _check_readme_link(entry)
        if msg:
            warnings.append({"id": entry["id"], "message": msg})

    ok = not failures
    if args.json:
        emit_result({"ok": ok, "failures": failures, "warnings": warnings}, json_mode=True)
    else:
        for f in failures:
            print(f"FAIL [{f['id']}]: {f['message']}")
        for w in warnings:
            print(f"WARN [{w['id']}]: {w['message']}")
        if ok:
            print(f"\ndoctor: ok ({len(entries)} repos)")
    return 0 if ok else 1
