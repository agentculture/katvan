# agentculture/* coverage audit on culture.dev

**Date:** 2026-05-18
**Source plan:** `/home/spark/.claude/plans/what-about-other-repos-binary-giraffe.md`
**Question this audit answers:** every public `agentculture/*` repo
should have a presence on culture.dev — where are the gaps?

## TL;DR

- **Registry drift: zero.** All 21 public `agentculture/*` repos are in
  `site/_data/agentculture_repos.yml`; no registry entry points at a
  private/archived repo. No Phase 2 PR-A registry-hygiene work needed
  beyond a `package:` field addition (see below).
- **Missing pages: zero.** Every registry entry has at least
  `site/docs/<id>/index.md` (skip-mode hand-authored) or
  `site/docs/<id>/{index.md,reference/}` (pull-reference auto-synced).
  agex-cli has its dedicated `site/agex/` tree from PR #29.
- **Real opportunity — flip-to-pull-reference candidates: 1 today,
  3 more pending upstream work.**
  - Today: **antoine** is `docs_mode: skip` but its CLI ships AFI
    `learn --json` + `explain --json` (verified by invocation). Flip
    in one PR.
  - Pending upstream: **culture**, **agex-cli**, **agentirc**,
    **steward** ship CLIs without the AFI contract. File or reopen
    issues on each.
- **Registry header doc gap:** the `docs_mode:` enum (lines 8–17 of
  `agentculture_repos.yml`) lists only `pull-reference` and `skip`,
  but `librarian` supports a third value `pull` (for narrative
  `docs/` directories). No registry entry currently uses it, but the
  header should mention it for honesty.

## Inputs

- `gh repo list agentculture --visibility public --limit 100` (run
  2026-05-18) — 21 active, non-archived, non-fork public repos.
- `site/_data/agentculture_repos.yml` — 21 entries.
- Per-repo `pyproject.toml` `[project.scripts]` + `[project.name]`.
- Per-repo CLI verb inventory under `<repo>/<pkg>/cli/_commands/`.
- For antoine: live `uv run antoine learn --json` invocation
  confirmed AFI contract.

## Per-repo matrix

| id | category | maturity | docs_mode | binary | PyPI name | has AFI? | site page | classification | action |
|----|----------|----------|-----------|--------|-----------|----------|-----------|----------------|--------|
| agentirc | core-runtime | usable | skip | agentirc | agentirc-cli | no (serve/start/stop/status/link/logs only) | `site/docs/agentirc/index.md` | **b** AFI-blocked | upstream issue: add `learn` + `explain` |
| irc-lens | core-runtime | experimental | pull-reference | (inferred) | (unverified) | (used by nightly cron) | `site/docs/irc-lens/{index.md,reference/}` | covered | none |
| culture | workspace-experience | usable | skip | culture | (probably culture) | partial — `learn` exists, `--json` missing per caveat | `site/docs/culture/index.md` | **b** AFI-blocked | reopen upstream issue on culture: ship `culture learn --json` |
| cultureagent | core-runtime | usable | pull-reference | cultureagent | (unverified) | (used by nightly cron) | `site/docs/cultureagent/{index.md,reference/}` | covered | none |
| agex-cli | workspace-experience | experimental | skip + SKILL.md | agex | agex-cli | partial — `learn` exists, `--json` missing per caveat | `site/agex/*` (11 files, PR #29) | **b** AFI-blocked, mitigated | long-term: get `agex learn --json` shipped → retire `sync_agex_skills.py` |
| afi-cli | workspace-experience | usable | pull-reference | afi | (unverified) | (used by nightly cron) | `site/docs/afi-cli/{index.md,reference/}` | covered | none |
| antoine | workspace-experience | experimental | skip | antoine + kata | antoine-cli | **YES — verified `uv run antoine learn --json` returns valid JSON** | `site/docs/antoine/index.md` | **a** AFI-ready | **Phase 2 PR: flip to pull-reference + add `package: antoine-cli`** |
| code-lens-cli | workspace-experience | experimental | pull-reference | code-lens | (unverified) | (used by nightly cron) | `site/docs/code-lens-cli/{index.md,reference/}` | covered | none |
| zehut | identity-secrets | experimental | skip | (none) | (n/a) | n/a | `site/docs/zehut/index.md` | **c** not-a-CLI yet | none |
| shushu | identity-secrets | experimental | skip | (none) | (n/a) | n/a | `site/docs/shushu/index.md` | **c** not-a-CLI yet | none |
| agtag | resident-culture | usable | pull-reference | agtag | agtag | (used by nightly cron) | `site/docs/agtag/{index.md,reference/}` | covered | none |
| auntiepypi | resident-culture | experimental | pull-reference | (inferred) | (unverified) | (used by nightly cron) | `site/docs/auntiepypi/{index.md,reference/}` | covered | none |
| cultureflare | resident-culture | experimental | skip | (none) | (n/a) | n/a (service / DNS edge) | `site/docs/cultureflare/index.md` | **c** not-a-CLI | none |
| ghafi | resident-culture | experimental | pull-reference | (inferred) | (unverified) | (used by nightly cron) | `site/docs/ghafi/{index.md,reference/}` | covered | none |
| katvan | resident-culture | usable | pull-reference | katvan | katvan | yes — this repo | `site/docs/katvan/{index.md,reference/}` | covered (self) | none |
| steward | resident-culture | experimental | skip | steward | steward-cli | no (doctor/show/announce_skill_update only) | `site/docs/steward/index.md` | **b** AFI-blocked | upstream issue: add `learn` + `explain` to steward |
| appsec | resident-domain | experimental | skip | (none) | (n/a) | n/a (resident agent) | `site/docs/appsec/index.md` | **c** not-a-CLI | none |
| office-agent | resident-domain | experimental | skip | (none) | (n/a) | n/a (resident agent) | `site/docs/office-agent/index.md` | **c** not-a-CLI | none |
| telek | resident-domain | experimental | skip | (none) | (n/a) | n/a | `site/docs/telek/index.md` | **c** not-a-CLI | none |
| tipalti | resident-domain | experimental | skip | (none) | (n/a) | n/a | `site/docs/tipalti/index.md` | **c** not-a-CLI | none |
| landing-page | org-site | experimental | skip | (none) | (n/a) | n/a (Jekyll site) | `site/docs/landing-page/index.md` | **c** not-a-CLI | none |

## Findings summary

### Category a (AFI-ready today, flip in one PR)

- **antoine** — only one. PyPI is `antoine-cli`; registry id is
  `antoine`; needs the `package:` override field added at the same
  time. Without it, the reference-sync workflow loop
  (`reference-sync.yml` line 31) skips it. The override field
  doesn't exist in the registry schema yet; **add it before the
  flip**.

### Category b (AFI-blocked, needs upstream work)

- **culture** — has `culture learn` but no `--json` flag. Existing
  caveat on registry line 66. Reopen on the culture repo.
- **agex-cli** — has `agex learn` but no `--json` flag. Caveat on
  registry line 86. Already mitigated by the SKILL.md sync (PR #29).
- **agentirc** — CLI ships serve/start/stop/status/link/logs/version
  but no `learn`/`explain`. Caveat-worthy but not currently called
  out. File on agentirc.
- **steward** — CLI ships doctor/show/announce_skill_update only.
  No `learn`/`explain`. File on steward.

For each: a tracked issue with title "Ship AFI `learn --json` +
`explain --json`" using the `communicate` skill (signed `- katvan
(Claude)`).

### Category c (not-a-CLI, no action)

zehut, shushu, cultureflare, appsec, office-agent, telek, tipalti,
landing-page — all already have hand-authored `index.md` pages.
zehut and shushu have caveats noting future `culture identity` /
`culture secret` wrappers; revisit when those ship.

### Category d (stale/dead)

None.

## Phase 2 — recommended PR slate (revised from plan)

The plan's original Phase 2 anticipated multiple PRs. Audit results
shrink the slate:

1. **PR-A1 "registry hygiene + package override"**
   - Add `package:` optional field to the schema header (lines
     20–22 area).
   - Update `reference-sync.yml` line 31:
     `uv tool install "${entry.package:-$repo}"` (read the registry
     in Python instead of bash, since the bash loop currently can't
     access per-entry fields).
   - Add `package: antoine-cli` to the antoine entry (still
     skip-mode at this point).
   - Add the missing `docs_mode: pull` value to the schema header
     comment (librarian-supported, not currently exercised).
2. **PR-B1 "flip antoine to pull-reference"** — one-line registry
   change. Validate by triggering `reference-sync.yml` via
   `workflow_dispatch` after PR-A1 merges; expect
   `site/docs/antoine/reference/` to appear in the resulting bot PR.
3. **PR-D1 "file upstream AFI-support issues"** — use the
   `communicate` skill to file on:
   - `agentculture/culture` (reopen if a prior issue exists)
   - `agentculture/agex-cli` (separate from the already-filed
     teardown issues #44/#45)
   - `agentculture/agentirc`
   - `agentculture/steward`

   Body template: short, includes a link to katvan's `pull` command
   so upstream knows what contract to implement. Sign `- katvan
   (Claude)`.

**No PR-C (hand-authored pages for non-CLI siblings) — all already
exist.**

## Phase 3 — generalize SKILL.md fallback

Defer. agex-cli remains the only sibling using
`src/<pkg>/commands/<verb>/SKILL.md`. No second user to justify
generalization yet. Reassess if culture or agentirc adopt the same
shape upstream as a faster path than implementing `learn --json`.

## Verification after Phase 2

1. `bundle exec jekyll build --strict_front_matter` — clean.
2. `htmlproofer --disable-external --allow-hash-href` — 0 failures.
3. Manual `workflow_dispatch` on `reference-sync.yml` after PR-A1 →
   antoine installs; after PR-B1 → antoine reference appears.
4. `katvan overview --json` reports antoine as `pull-reference` and
   the resulting `site/docs/antoine/reference/` is non-empty.
