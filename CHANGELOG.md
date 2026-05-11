# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/). This
project does not yet ship a Python package, so the versions below are
documentation milestones rather than published artifacts; CI version
gating arrives when/if katvan grows a packaging story.

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
