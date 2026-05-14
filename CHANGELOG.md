# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/). As of the
unreleased entry below, katvan ships the `katvan` Python package; earlier
`0.x` versions are documentation milestones rather than published
artifacts.

## [Unreleased]

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
