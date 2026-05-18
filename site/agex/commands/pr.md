---
title: pr
parent: Commands
nav_order: 70
sites: [culture]
permalink: /agex/commands/pr/
---

# `agex pr` — PR lifecycle for agents

Six verbs, in roughly the order an agent uses them on a PR:

| Verb | Purpose |
|---|---|
| `agex pr lint` | Portability + alignment-trigger lint on the working diff. |
| `agex pr open --title T [--body-file F] [--draft] [--delayed-read]` | `gh pr create` with auto-signed body; with `--delayed-read` chains to `read --wait 180`. |
| `agex pr read [<PR>] [--wait SECS]` | Unified briefing: CI checks, SonarCloud quality gate, all comments, reviewer readiness. With `--wait`, polls until required reviewers are ready or timeout. Always exits 0. |
| `agex pr reply <PR>` | Read JSONL replies on stdin, post each, resolve threads. |
| `agex pr await [<PR>] [--max-wait SECS]` | "Wake me when this is triage-able" — polls readiness, runs CI + Sonar gate, dumps briefing. **Exits 1 on quality-gate `ERROR`, unresolved threads, or failing CI checks**, 0 on clean state or timeout. Default `--max-wait 1800` (30 min). |
| `agex pr delta` | Dump sibling-project `CLAUDE.md` heads + `culture.yaml` for alignment review. |

`pr read --wait` and `pr await` share the same readiness-polling loop; the
difference is the exit code. Use `read` when you want the briefing
unconditionally; use `await` when you want to **gate** the next step on
PR health (e.g., in scripts that should fail if Sonar errors).

## SonarCloud project key

`pr read` and `pr await` query the SonarCloud quality gate for the current
PR. The project key is resolved in order:

1. `SONAR_PROJECT_KEY` env var (override for non-standard naming).
2. `[pr] sonar_project_key` in `.agex/config.toml`.
3. `<owner>_<repo>` (SonarCloud GitHub-import default).

When the project isn't on SonarCloud the API 404s and agex silently
skips the section, so the verbs stay safe for non-Sonar repos.

Every command ends with a `**Next step:**` footer — chase the chain without guessing.

## Side effects

Network: every command except `lint` and `delta` talks to GitHub via `gh`.
Disk: `pr open`, `pr read`, and `pr reply` append events to
`.agex/data/pr/events.jsonl`.

## Prerequisites

- `gh` (GitHub CLI) on PATH and authenticated (`gh auth login`).
- `--agent` flag, or first agent's `backend:` set in `culture.yaml`.

For each verb's full behavior, error modes, and exit codes, see
`docs/superpowers/specs/2026-05-10-agex-pr-design.md`.
