---
name: librarian
description: >
  Maintains the docs of sibling AgentCulture repos under one roof on the
  culture.dev site. Three verbs: `overview` (survey which siblings are
  synced / fresh / healthy), `pull` (sync a sibling's raw-markdown `docs/`
  into `site/docs/<repo>/`, injecting Jekyll frontmatter), `doctor` (detect
  doc defects — missing frontmatter, broken links, staleness, drift — and
  auto-file dedup'd GitHub issues on the source repos for sibling-actionable
  ones). Use when the user talks about syncing, checking, surveying, or
  importing sibling-repo docs, or says "pull <repo>'s docs", "are the docs
  fresh", "run doctor on the docs". katvan-original skill — authored here,
  not vendored.
---

# Librarian — Cross-Repo Docs Under One Roof

katvan owns the `culture.dev` Jekyll site (`site/`). Its long-term job is
to pull the documentation of sibling AgentCulture repos into the unified
site at `site/docs/<repo>/`, so a reader gets every repo's docs in one
navigable place instead of hunting across a dozen GitHub repos.

The librarian skill gives katvan three verbs for that job:

- **overview** — read-only survey. For every sibling repo: what's its
  docs mode, is it synced into `site/docs/`, is the sync fresh against
  the source, and how healthy is the frontmatter.
- **pull** — sync one sibling's `docs/` tree into `site/docs/<repo>/`,
  injecting the Jekyll frontmatter every culture.dev page needs. Never
  commits — leaves the working tree dirty for the cicd skill to PR.
- **doctor** — run a check-set against synced repos. Defects that the
  *sibling* must fix become dedup'd GitHub issues on the source repo;
  defects *katvan* must fix are printed locally.

## When to Use

- The user asks to **sync / pull / import** a sibling repo's docs into
  the culture.dev site.
- The user wants a **survey** of which siblings' docs are present, fresh,
  or healthy on the site.
- The user wants to **check / audit / doctor** the synced docs for
  defects (missing frontmatter, broken links, staleness, drift).
- A sibling repo updated its `docs/` and katvan needs to re-pull.

## When NOT to Use

- **In-katvan docs** (`site/docs/shared/`, `site/docs/reference/`,
  hand-authored culture.dev pages) — those are edited directly, not
  pulled.
- **Opening the PR** for a pull — that's the `cicd` skill. `pull` only
  stages the working tree.
- **Generic cross-repo issues / briefs** — that's the `communicate`
  skill. `doctor` only files issues for the specific doc-defect classes
  in its check-set, and it does so through `communicate`'s scripts.
- **Self-published siblings** — `afi-cli`, `agex-cli` ship their own
  Jekyll sites; culture.dev links out to them. `pull` refuses these.

## Prerequisites

- `git` — local-mode source resolution (sibling repos checked out under
  `/home/spark/git/<repo>/`).
- `gh` (authenticated) — remote-mode source resolution when a sibling
  isn't checked out locally, and the `doctor` issue-dedup search.
- `agtag` (>=0.1) — `doctor` files issues through the `communicate`
  skill's scripts, which wrap `agtag issue post|reply`.
- `python3` (stdlib only) — YAML registry parsing, frontmatter injection,
  JSON manifests. No PyYAML import is required (it's used opportunistically
  by the registry parser when present, with a hand-rolled fallback).

Sibling repos under `/home/spark/git/` are used directly (fast, offline);
otherwise the skill falls back to `gh api` against `agentculture/<repo>`.
Override the siblings root with `LIBRARIAN_SIBLINGS_ROOT`.

## How to run

| Command | What it does |
|---------|--------------|
| `scripts/overview.sh [--json] [--repo <id>]` | Read-only survey. Per repo: docs mode, synced?, fresh vs source?, file count, frontmatter-health findings. Always exits 0. |
| `scripts/pull.sh --repo <id> [--ref <branch-or-sha>] [--dry-run] [--json]` | Sync `<id>`'s `docs/` into `site/docs/<id>/` with frontmatter injection. `--dry-run` prints the add/update/remove plan, writes nothing. Never commits. Exit 0 ok / 1 user error / 2 env error. |
| `scripts/doctor.sh [--repo <id>] [--dry-run] [--json]` | Run the check-set against `pull`-mode repos. Files dedup'd issues for sibling-actionable findings; prints katvan-actionable ones. `--dry-run` files nothing. Exit 0 = no findings, 1 = findings. |

`_repos.sh` (sourced helper — parses the registry) and `_frontmatter.py`
(stdlib frontmatter injector) are internal and not invoked directly.

## Repo classification

Every entry in `site/_data/agentculture_repos.yml` carries a `docs_mode:`
key that tells librarian how to treat that repo's docs:

| `docs_mode` | Meaning | librarian behavior |
|-------------|---------|--------------------|
| `pull` | Raw-markdown `docs/` dir, no own Jekyll site. | `pull` syncs it into `site/docs/<id>/`; `overview` and `doctor` cover it. |
| `self-published` | Ships its own standalone Jekyll site (`afi-cli`, `agex-cli`). | culture.dev links out; `pull` refuses; `overview` lists it with the label only. |
| `skip` | Reference/system docs or already migrated (`steward`, `culture`). | librarian leaves it alone. |

Adding a sibling to the registry means picking its `docs_mode`. When
unsure, default to `skip` — it's the no-op.

## Frontmatter-injection contract

Sibling docs are raw markdown — most have no frontmatter at all — but
every culture.dev page needs at minimum a `sites:` key (see
`site/docs/README.md` rule 7). On `pull`, every `.md` file is piped
through `_frontmatter.py`, which **merges defaults only for keys that are
absent** — it never clobbers a value the sibling already set:

| Key | Default injected (only if absent) |
|-----|-----------------------------------|
| `sites:` | `[culture]` |
| `title:` | derived from the first `# H1` in the body; **omitted** if there's no H1 (`doctor` flags `no-h1`) |
| `permalink:` | `/<repo>/<rel-path with .md stripped>/` — e.g. `ghafi` + `guides/intro.md` → `/ghafi/guides/intro/` |
| `nav_order:` | `N` if the filename has a numeric prefix like `01-foo.md`; else omitted |

The original body is preserved byte-for-byte. Non-markdown files (images,
templates) are copied verbatim. Each pull writes a manifest at
`site/docs/<repo>/.katvan-pull.json` recording `repo`, `ref`, `sha`,
`pulled_at`, and a per-file `source_sha256`.

## The doctor check-set

`doctor` diffs `site/docs/<repo>/` against the sibling source and runs
six checks, split into two actionability classes:

| Check | Detects | Class | Severity |
|-------|---------|-------|----------|
| `missing-frontmatter` | sibling SOURCE file lacks `sites:`/`title:` | sibling-actionable | error |
| `broken-internal-link` | a `[..](..)` link in `site/docs/<repo>/` whose target file doesn't exist | sibling-actionable | error |
| `no-h1` | a sibling source doc with no `# H1` | sibling-actionable | warning |
| `stale-vs-source` | `.katvan-pull.json` sha behind the sibling's latest `docs/` commit | katvan-actionable | warning |
| `orphaned-file` | a file in `site/docs/<repo>/` no longer in the sibling source | katvan-actionable | warning |
| `drift` | a `site/docs/<repo>/` file diverges from source beyond frontmatter injection | katvan-actionable | warning |

**sibling-actionable** — the fix belongs in the *sibling's* `docs/` tree.
`doctor` files (or updates) **one GitHub issue per `(repo, check-id)`** on
`agentculture/<repo>`, aggregating every finding of that check into the
one issue body, via the `communicate` skill's `post-issue.sh` /
`post-comment.sh` (so the signature auto-resolves from `culture.yaml`).

**katvan-actionable** — the fix belongs in katvan. `doctor` prints these
locally and **never files an issue** for them.

### The dedup-marker convention

Every doctor-filed issue body embeds an HTML-comment marker:

```
<!-- katvan-doctor: <repo>/<check-id> -->
```

Before filing, `doctor` searches the sibling's open issues for that
marker (`gh issue list --repo agentculture/<repo> --state open --search
"katvan-doctor: <repo>/<check-id>" --json number,body` — note plain `gh
issue view` hits a Projects-classic error, so `doctor` uses `gh issue
list`). If a matching open issue exists, `doctor` comments "still present
as of <date>" via `post-comment.sh` instead of filing a duplicate. One
issue per `(repo, check-id)`, forever — re-runs update, never multiply.

## Conventions

- **`pull` never commits.** It stages `site/docs/<repo>/` in the working
  tree and stops. Hand off to the `cicd` skill to open the PR — that's
  where lint, the briefing, and the signature live.
- **Signatures resolve at runtime.** `doctor`'s issues and comments go
  through `communicate`'s scripts, which call `agtag` — the signing nick
  resolves from katvan's `culture.yaml` (`suffix: katvan`). No hard-coded
  signature literal anywhere in this skill.
- **Local source is the fast path.** If a sibling is checked out under
  `/home/spark/git/`, librarian reads it directly — offline, no API
  budget. Remote `gh api` is the fallback, not the default.
- **`--dry-run` is always safe.** `pull --dry-run` writes nothing;
  `doctor --dry-run` files no issues. Use it freely to preview.

## Red Flags

**Never:**

- Run `doctor` without `--dry-run` when you only want to *see* the
  findings — the real run files GitHub issues on sibling repos.
- `git commit` from inside `pull` — it stages only; the PR is the cicd
  skill's job.
- Pull a `self-published` or `skip` repo — `pull` refuses, and forcing
  it would duplicate docs that already live elsewhere or shouldn't move.
- Hand-author the `<!-- katvan-doctor: ... -->` marker or a doctor issue
  body — `doctor` builds and dedups them. Manual issues break the dedup.
- File an issue for a katvan-actionable finding (`stale-vs-source`,
  `orphaned-file`, `drift`) — those are katvan's to fix, printed locally.
- Edit a pulled file under `site/docs/<repo>/` by hand — the next `pull`
  overwrites it, and `doctor` flags the divergence as `drift`. Fix it at
  the source.
