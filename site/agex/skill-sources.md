---
title: Skill sources
sites: [culture]
permalink: /agex/skill-sources/
nav_order: 5
---

# Vendored skills — upstream provenance

This file records where the skills under `.claude/skills/` came from, so future
resync broadcasts (steward auto-files one per skill update) have a clear
provenance entry to point at. Per the AgentCulture
[cite-don't-import policy](https://github.com/agentculture/steward/blob/main/docs/skill-sources.md),
agex-cli owns its copies and may diverge — divergence is recorded in the
relevant `SKILL.md` frontmatter `description`.

| Skill | Path | Upstream (canonical) | Divergence | Resync issue |
|-------|------|----------------------|------------|--------------|
| `communicate` | `.claude/skills/communicate/` | [`steward/.claude/skills/communicate/`](https://github.com/agentculture/steward/tree/main/.claude/skills/communicate) | Identifier-only (frontmatter `description` says "from agex-cli"). | [#36](https://github.com/agentculture/agex-cli/issues/36) |
| `cicd` | `.claude/skills/cicd/` | [`steward/.claude/skills/cicd/`](https://github.com/agentculture/steward/tree/main/.claude/skills/cicd) | Identifier-only (frontmatter `description` says "agex-cli's CI/CD lane"). | [#37](https://github.com/agentculture/agex-cli/issues/37) |

## Resync workflow

When an issue arrives titled "Resync vendored `<name>` skill from steward":

1. Branch `skill/<name>-resync`.
2. `cp -R <steward-checkout>/.claude/skills/<name> .claude/skills/` (where
   `<steward-checkout>` is your local clone of
   [`agentculture/steward`](https://github.com/agentculture/steward)).
3. `chmod +x .claude/skills/<name>/scripts/*.sh`.
4. Re-apply identifier adaption (see the divergence column above).
5. Bump `pyproject.toml` per project convention.
6. Add a CHANGELOG entry.
7. Open PR; post a comment on the resync issue with the PR link via
   `bash .claude/skills/communicate/scripts/post-comment.sh`.

## Nick

`culture.yaml` at the repo root sets `suffix: agex-cli`. Both
`agtag` (used by `communicate`) and `cicd/scripts/_resolve-nick.sh`
read that file. Auto-emitted signatures are `- agex-cli (Claude)`.
