"""`katvan pull` — reference-only sync from sibling AFI binaries.

For each registered repo with ``docs_mode: pull-reference``, invoke
``<binary> learn --json`` and ``<binary> explain [path] --json`` and render
deterministic markdown into ``site/docs/<id>/reference/``.

Determinism: outputs are sorted, JSON is re-serialised with ``sort_keys``,
markdown front-matter is identical run-to-run. The per-repo reference tree is
rewritten from scratch on every call — `_pull_one` deletes
``site/docs/<id>/reference/`` before any writes, so nouns / verbs removed
upstream disappear locally too. Re-running pull on unchanged sibling state
MUST produce a byte-identical tree (CI relies on this to keep bot-PR diffs
minimal).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from katvan import repos
from katvan.cli._errors import EXIT_INTERNAL_ERROR, EXIT_USER_ERROR, KatvanError
from katvan.cli._output import emit_result


@dataclass
class _PullResult:
    pulled: list[str]
    skipped: list[str]
    failed: list[dict[str, str]]


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser(
        "pull",
        help="sync AFI-derived reference docs from sibling binaries",
    )
    parser.add_argument(
        "repo",
        nargs="?",
        help="single repo id to pull; omit + use --all for the full registry",
    )
    parser.add_argument("--all", action="store_true", help="pull every pull-reference repo")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    parser.set_defaults(func=_handle)


def _require_target_selector(args: argparse.Namespace) -> None:
    if not args.repo and not args.all:
        raise KatvanError(
            code=EXIT_USER_ERROR,
            message="specify a repo id or pass --all",
            remediation="examples: katvan pull culture | katvan pull --all",
        )


def _process_entry(site_root: Path, entry: dict[str, str], result: _PullResult) -> None:
    repo_id = entry["id"]
    if entry.get("docs_mode") != "pull-reference":
        result.skipped.append(repo_id)
        return
    try:
        _pull_one(site_root, entry)
        result.pulled.append(repo_id)
    except Exception as err:  # noqa: BLE001
        result.failed.append({"id": repo_id, "error": str(err)})


def _emit_text_result(result: _PullResult) -> None:
    for rid in result.pulled:
        print(f"pulled: {rid}")
    for rid in result.skipped:
        print(f"skipped: {rid}")
    for fail in result.failed:
        print(f"failed: {fail['id']}: {fail['error']}")


def _handle(args: argparse.Namespace) -> int:
    _require_target_selector(args)

    targets = list(_select_targets(args))
    result = _PullResult(pulled=[], skipped=[], failed=[])
    site_root = repos.registry_path().parent.parent

    for entry in targets:
        _process_entry(site_root, entry, result)

    if args.json:
        emit_result(vars(result), json_mode=True)
    else:
        _emit_text_result(result)

    return 1 if result.failed else 0


def _select_targets(args: argparse.Namespace) -> Iterable[dict[str, str]]:
    if args.all:
        return list(repos.entries())
    for e in repos.entries():
        if e["id"] == args.repo:
            return [e]
    raise KatvanError(
        code=EXIT_USER_ERROR,
        message=f"unknown repo id: {args.repo}",
        remediation="run 'katvan overview' to see registered ids",
    )


def _pull_one(site_root: Path, entry: dict[str, str]) -> None:
    binary = entry.get("binary", entry["id"])
    out = site_root / "docs" / entry["id"] / "reference"

    # Fetch learn first. If the binary isn't installed in this environment
    # (CI lanes that don't pre-install every sibling), we fail HERE — leaving
    # the existing committed reference tree intact. The destructive rmtree
    # below only runs once we know we have replacement data, so removed-
    # upstream nouns / verbs disappear locally too.
    learn_json = _invoke_json(binary, ["learn", "--json"])

    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)

    (out / "learn.md").write_text(_render_learn(entry, learn_json))

    explain_root = out / "explain"
    explain_root.mkdir(exist_ok=True)
    for noun in sorted(learn_json.get("nouns", [])):
        payload = _invoke_json(binary, ["explain", noun, "--json"])
        (explain_root / f"{noun}.md").write_text(_render_explain(noun, payload))
        for verb in sorted(payload.get("verbs", [])):
            verb_payload = _invoke_json(binary, ["explain", f"{noun}/{verb}", "--json"])
            verb_dir = explain_root / noun
            verb_dir.mkdir(exist_ok=True)
            (verb_dir / f"{verb}.md").write_text(
                _render_explain(f"{noun}/{verb}", verb_payload)
            )

    (out / "index.md").write_text(_render_index(entry, learn_json))


def _invoke_json(binary: str, args: list[str]) -> dict:
    proc = subprocess.run(
        [binary, *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise KatvanError(
            code=EXIT_INTERNAL_ERROR,
            message=(
                f"{binary} {' '.join(args)} exited {proc.returncode}: "
                f"{proc.stderr.strip()}"
            ),
            remediation="confirm the sibling binary is AFI-compatible (supports --json)",
        )
    return json.loads(proc.stdout or "{}")


def _render_index(entry: dict, learn: dict) -> str:
    return (
        f"---\ntitle: {entry['id']} reference\nparent: {entry['id']}\n"
        f"nav_order: 1\nsites: [culture]\n---\n\n"
        f"# {entry['id']} reference\n\n"
        f"{learn.get('summary', entry.get('description', ''))}\n\n"
        f"- [learn](learn.md)\n"
        + "".join(
            f"- [explain {n}](explain/{n}.md)\n" for n in sorted(learn.get("nouns", []))
        )
    )


def _render_learn(entry: dict, payload: dict) -> str:
    return (
        f"---\ntitle: {entry['id']} learn\nparent: {entry['id']} reference\n"
        f"sites: [culture]\n---\n\n"
        f"# `{entry.get('binary', entry['id'])} learn`\n\n"
        f"```json\n{json.dumps(payload, indent=2, sort_keys=True)}\n```\n"
    )


def _render_explain(path: str, payload: dict) -> str:
    return (
        f"---\ntitle: explain {path}\nsites: [culture]\n---\n\n"
        f"# `explain {path}`\n\n"
        f"```json\n{json.dumps(payload, indent=2, sort_keys=True)}\n```\n"
    )
