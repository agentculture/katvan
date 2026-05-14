# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/). This
project does not yet ship a Python package, so the versions below are
documentation milestones rather than published artifacts; CI version
gating arrives when/if katvan grows a packaging story.

## [Unreleased]

### Added

- `.github/workflows/sonarcloud.yml` and `sonar-project.properties` —
  SonarCloud scan on PR + push to main. Closes the gap where the
  vendored `cicd` skill's `status` / `await` extensions expected a
  Sonar scan that wasn't being produced. Scan-only (no pytest /
  coverage) to match the current greenfield-repo posture documented in
  `.claude/skills/cicd/SKILL.md`; the workflow gates on
  `env.SONAR_TOKEN != ''` so a missing secret no-ops rather than
  failing PRs.
- `site/` — the culture.dev Jekyll site, migrated from
  `agentculture/culture` (issue #1, Phase 0a). Behavior-preserving
  move: config, theme, data, assets, and the `docs/` content tree
  copied verbatim; `docs/superpowers/` and `docs/resources/` left in
  culture (excluded from the build there, not migrated). Built green
  by the new `docs-check` workflow.

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
