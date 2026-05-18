# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/). As of the
unreleased entry below, katvan ships the `katvan` Python package; earlier
`0.x` versions are documentation milestones rather than published
artifacts.

## [Unreleased]

## [0.2.8] — 2026-05-18

### Changed

- `site/_data/agentculture_repos.yml`: flip `antoine` from
  `docs_mode: skip` to `docs_mode: pull-reference`. Its CLI ships
  AFI `learn --json` + `explain --json` today (verified by live
  invocation), so the nightly cron now syncs antoine's reference
  alongside the other pull-reference siblings.

### Added

- `site/docs/antoine/reference/`: initial reference pull from
  `antoine-cli` 0.11.0 (greenfield status — `learn` is the only
  noun; `explain` returns the greenfield message).
- `site/docs/antoine/index.md`: trailing `[Reference →]` link,
  matching the convention used by every other pull-reference
  sibling.

## [0.2.7] — 2026-05-18

### Changed

- `site/_data/agentculture_repos.yml`: schema header documents the
  optional `package:` override for siblings whose PyPI name diverges
  from their repo id (the field was already in use for agentirc but
  undocumented), and adds the missing third `docs_mode: pull` value
  that the librarian skill supports.
- `.github/workflows/reference-sync.yml`: the install loop now reads
  `package or id` per pull-reference entry, so a future flip of a
  diverging-name sibling (antoine → antoine-cli is queued in this
  PR) installs cleanly without further workflow edits.

### Added

- `site/_data/agentculture_repos.yml`: `antoine` entry gains
  `binary: antoine` and `package: antoine-cli`. Still `docs_mode:
  skip` for now; flip to `pull-reference` is a separate one-line PR
  once this one lands.

## [0.2.6] — 2026-05-18

### Fixed

- `katvan/cli/_commands/doctor.py`: extract `"index.md"` literal into a
  module-level `_INDEX_MD` constant. Resolves SonarCloud's
  duplicate-literal finding on the `_check_index` + `_check_reference`
  pair landed in 0.2.5.

## [0.2.5] — 2026-05-18

### Added

- Site: absorbed `agex-cli`'s standalone Jekyll docs site into
  katvan. `culture.dev/agex/` is now served from katvan's main
  build as plain paths inside the same site — no separate
  `_config.agex.yml`, no separate Cloudflare project, no path-
  routing rule. Prose pages (`/agex/`, `/agex/getting-started/`,
  `/agex/skill-sources/`) are hand-imported; per-command pages
  under `/agex/commands/<verb>/` are rendered from
  `agex-cli/src/agent_experience/commands/*/SKILL.md` by
  `scripts/sync_agex_skills.py`, refreshed by the nightly
  `reference-sync.yml` cron.
- `scripts/sync_agex_skills.py` + `tests/unit/test_sync_agex_skills.py`
  (11 tests, stdlib-only renderer).
- `tests/conftest.py` adds `scripts/` to `sys.path` so non-package
  script modules are importable from unit tests.

### Removed

- `site/docs/agex-cli/index.md` (the marketing-rebuild placeholder
  overview); inbound internal links repointed to `/agex/`. No
  redirect — this is a renovation, not a migration.

## [0.2.4] — 2026-05-18

### Fixed

- Site: rewrote the 7 broken internal links in the three vendored
  pages (`attention`, `coverage-baseline`, `architecture/shared-vs-cited`)
  whose repo-relative paths (`../pyproject.toml`,
  `superpowers/specs/…`, `../../CLAUDE.md#citation-pattern`) carried
  over from the original culture-repo import. Each now resolves to an
  absolute GitHub URL on `agentculture/culture`.
- CI: dropped the file-scoped `--ignore-files` workaround and the
  `continue-on-error: true` flag from the html-proofer step in
  `docs-check.yml`. The link check is now a hard gate.

## [0.2.3] — 2026-05-18

### Fixed

- Site: repaired broken internal links flagged by Google Search Console.
  Footer dropped the non-existent `/reference/cli/devex/` mention and
  re-pointed `/ecosystem-map/` (404) → `/ecosystem/`. The 21
  `docs/<repo>/index.md` overview pages had a `[Reference →](reference/)`
  link resolving to `/<repo>/reference/`, but the real refs live at
  `/docs/<repo>/reference/` — rewrote the 8 with a companion, removed
  the dead line from the 13 without. Home-page pills dropped two
  unbuilt `/docs/persistent-agents/` and `/docs/works-with-your-stack/`
  hrefs; layout now omits "Learn more →" when `pill.href` is absent.

### Added

- `_includes/head_custom.html` now documents the `canonical_url:`
  frontmatter escape hatch (jekyll-seo-tag honors it natively) for
  future per-page canonical overrides.
- CI: advisory `html-proofer` step in `docs-check.yml` catches broken
  internal links at PR time. Three vendored pages with repo-relative
  paths from sibling imports are ignored at file level until the
  librarian import learns to rewrite them.

## [0.2.2] — 2026-05-18

### Fixed

- Left navigation now renders on the landing page at `/`. The home
  layout used to be a standalone `<html>` document that bypassed the
  just-the-docs `default` layout; it is now nested under `default` so
  the sidebar matches every doc page.

## [0.2.0] — 2026-05-18

### Added

- Three new verbs implementing the culture.dev marketing rebuild: `overview`
  (per-category registry summary), `pull` (AFI-only reference sync —
  invokes each `pull-reference` sibling's binary with `learn --json` +
  `explain --json` and writes deterministic markdown into
  `site/docs/<id>/reference/`), and `doctor` (CI gate for culture.dev IA
  health — every registered repo must have a hand-authored `index.md` and,
  for `pull-reference` repos, a synced reference tree).
- `repos.entries()` helper that returns full registry rows as dicts
  (existing `repos()` only yielded `(id, mode, local_path)`).
- `site/_data/style.yml` — voice and naming pin for all hand-authored
  culture.dev copy.
- `site/_data/landing.yml` — hero, three capability pills, and why-band
  copy consumed by the new `home` layout.
- Marketing-shaped `site/_layouts/home.html` (4 bands) + landing-band SCSS
  in `site/_sass/custom/custom.scss`.
- `site/docs/quickstart.md`, `site/docs/why.md` (manifesto), and
  `site/docs/ecosystem.md` plus 6 category overview pages under
  `site/docs/categories/`.
- 21 per-repo `site/docs/<id>/index.md` pages, one for every registered
  repo.
- `.github/workflows/reference-sync.yml` — bot-PR workflow (nightly cron +
  `workflow_dispatch`) that pulls and opens a PR when reference content
  changes.
- `site/_includes/analytics.html` — Plausible include (no-op until
  `analytics_host` / `analytics_domain` are uncommented in
  `_config.culture.yml`).

### Changed

- `site/_data/agentculture_repos.yml` trued up to 21 repos. `docs_mode`
  collapsed to `pull-reference` / `skip`; `self-published` removed.
- `.github/workflows/docs-check.yml` extended: installs katvan, runs
  `katvan pull --all` (tolerant of missing sibling binaries), then
  `katvan doctor` as a hard gate before the Jekyll build.

### Removed

- 67 pre-rebuild files under `site/docs/` superseded by the new IA
  (per-repo `index.md` pages, category overviews, and the manifesto).
  Six files were kept and reorganised under `/architecture/` as
  contributor-facing reference.

## [0.1.0] — earlier

### Added

- The `katvan` Python CLI (PyPI package `katvan`) — scaffolded by
  `afi-cli`, phase 2 of migrating the `librarian` skill into a real
  installable CLI. Ships the `katvan/` package: CLI plumbing
  (`_errors` / `_output`, argparse with structured-error routing), the
  universal `learn` / `explain` verbs, and two ported helper modules —
  `repos.py` (from the skill's `_repos.sh`; stdlib-only line-oriented
  YAML parse, path-agnostic registry walk-up, `KATVAN_SIBLINGS_ROOT`
  override) and `frontmatter.py` (from `_frontmatter.py`, near-verbatim,
  with the core extracted into a callable `inject()` library function).
  Packaging is `pyproject.toml` (hatchling, zero runtime deps); CI is
  `.github/workflows/tests.yml` + `publish.yml` mirroring `afi-cli`
  (pytest + coverage-fed SonarCloud scan; TestPyPI on PR, PyPI
  trusted-publishing on push to main). The `librarian`
  `_frontmatter.py` logic finally gets real unit tests. The docs verbs
  (`overview` / `pull` / `doctor`) land in a follow-up release.
- SonarCloud scan on PR + push to main, and `sonar-project.properties`
  to drive it. Closes the gap where the vendored `cicd` skill's
  `status` / `await` extensions expected a Sonar scan that wasn't being
  produced. The scan now runs inside `.github/workflows/tests.yml`
  (coverage-fed) — the original standalone `sonarcloud.yml` workflow
  has been removed, and `sonar-project.properties` narrowed from
  whole-repo to the `katvan` package with `sonar.tests`,
  `sonar.python.version`, and `sonar.python.coverage.reportPaths` wired
  in. The scan still gates on `env.SONAR_TOKEN != ''` so a missing
  secret no-ops rather than failing PRs.
- `site/` — the culture.dev Jekyll site, migrated from
  `agentculture/culture` (issue #1, Phase 0a). Behavior-preserving
  move: config, theme, data, assets, and the `docs/` content tree
  copied verbatim; `docs/superpowers/` and `docs/resources/` left in
  culture (excluded from the build there, not migrated). Built green
  by the new `docs-check` workflow.
- `site/sitemap.html`, `site/sitemap-main.html`,
  `site/sitemap-agentirc.html`, `site/robots.txt`, `site/favicon.ico` —
  site-infrastructure files that publish `/sitemap.xml`,
  `/sitemap-main.xml`, `/agentirc/sitemap.xml`, `/robots.txt`, and
  `/favicon.ico`. Missed by the PR 2 inventory (whose parity check only
  diffed `*.html` outputs); a full-output diff against culture's build
  caught the gap. culture-repo cruft that also leaks into culture's
  build (`CHANGELOG.md`, `SECURITY.md`, `coverage.xml`,
  `sonar-project.properties`, `dist/*`) is intentionally not migrated.

## [0.1.0] - 2026-05-12

### Added

- `.claude/skills/cicd/` vendored from `agentculture/steward` 0.12.0.
  Thin delegate to `agex pr` (lint / open / read / reply / delta) plus
  two upstream extensions (`status`, `await`) for SonarCloud gating
  and unresolved-thread tracking. Closes
  [#2](https://github.com/agentculture/katvan/issues/2) (stale 0.9.x
  brief, superseded) and
  [#3](https://github.com/agentculture/katvan/issues/3) (current
  0.12.0 brief).
- `.claude/skills/communicate/` vendored from
  `agentculture/steward`'s `communicate` skill (issue I/O backed by
  `agtag` >=0.1). Cross-repo issue post / comment / fetch and Culture
  mesh messaging. Closes
  [#4](https://github.com/agentculture/katvan/issues/4).
- `culture.yaml` declaring `suffix: katvan` — drives auto-signature
  resolution for both skills' GitHub I/O (signed `- katvan (Claude)`).
- `docs/skill-sources.md` provenance ledger recording the two
  vendored skills, their upstream, and the identifier-only
  adaptations applied.

### Conventions

- Adopt the AgentCulture **cite, don't import** vendoring pattern.
- SKILL.md prose mentions of the consuming repo (this one) read
  `katvan`; mentions that cite steward as the upstream are preserved
  verbatim.
