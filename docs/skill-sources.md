# Skill sources — provenance ledger

Skills under `.claude/skills/` are **vendored** copies, not symlinks or
runtime dependencies. Each skill names its upstream below so future
re-syncs (and `steward announce-skill-update` broadcasts) know where
to look.

This follows the AgentCulture **cite, don't import** pattern: katvan
owns its copies and may diverge from upstream for repo-specific
reasons. When upstream changes, downstream copies do not auto-update —
re-vendor explicitly via the recipe in the broadcast brief.

## Vendored skills

| Skill | Upstream | Notes | Last synced |
|-------|----------|-------|-------------|
| `cicd` | `agentculture/steward` (`../steward/.claude/skills/cicd/`) — layered on `agex pr` (in `agentculture/agex-cli`) | Identifier-only adaptation: SKILL.md prose framing changed from "Steward edition" to "Katvan (vendored from steward)". No script changes; signature resolves from `culture.yaml` at runtime via `_resolve-nick.sh` (prints `katvan`). Closes [#2](https://github.com/agentculture/katvan/issues/2) (stale 0.9.x brief, superseded) and [#3](https://github.com/agentculture/katvan/issues/3) (0.12.0 brief). | 2026-05-12 (steward 0.12.0) |
| `communicate` | `agentculture/steward` (`../steward/.claude/skills/communicate/`) — issue I/O backed by `agtag` (>=0.1) | Identifier-only adaptation: SKILL.md prose mentions of "steward" as the consuming repo changed to "katvan" (the mesh-agent caveat, signature default, broadcast section); upstream citations preserved verbatim. Signature resolves from `culture.yaml`. Closes [#4](https://github.com/agentculture/katvan/issues/4). | 2026-05-12 |

## Vendoring policy

- **Cite, don't import.** Skills are copied into katvan, not symlinked
  or installed. Katvan owns and may modify its copies.
- **Re-sync explicitly.** Upstream changes do not propagate
  automatically. Watch for `steward announce-skill-update` broadcasts
  on this repo and re-vendor per the recipe in the brief.
- **Identifier-only adapts.** Where a SKILL.md mentions the
  *consumer* (e.g. "Steward's job is alignment", "in-steward issues"),
  swap in `katvan`. Leave references that *cite steward as the
  upstream* (e.g. "Renamed from `pr-review` in steward 0.7.0") intact
  — those are historical pointers, not consumer-identifiers.
- **No hard-coded signature literals.** Both vendored skills resolve
  the signature nick at runtime from `/culture.yaml` (`suffix:
  katvan`), with `agex --as NICK` / `agtag --as NICK` overrides
  available per call. If a future upstream re-introduces a hard-coded
  `- steward (Claude)` literal anywhere, change it to `- katvan
  (Claude)` and record the divergence in the row above.
- **Record divergence.** Any change beyond identifier-only goes in
  the row's "Notes" cell.

## Katvan-original skills

These skills were **authored in katvan** — they are not vendored from
anywhere. Katvan is the canonical upstream for them. If a sibling repo
adopts one, record the consumer in the `Downstream copies` cell so
future `steward announce-skill-update` broadcasts find them.

| Skill | Origin | Notes | Downstream copies |
|-------|--------|-------|-------------------|
| `librarian` | **katvan-original** (authored here; canonical-here) | Cross-repo docs maintenance for the culture.dev site: `overview` / `pull` / `doctor`. Pulls sibling repos' raw-markdown `docs/` into `site/docs/<repo>/` with Jekyll frontmatter injection; `doctor` files dedup'd issues on the source repos via the `communicate` skill's scripts. Depends on the `docs_mode:` key in `site/_data/agentculture_repos.yml` and the `communicate` skill. Phase 1 of a two-phase plan — Phase 2 migrates these scripts into a `katvan` Python CLI. | none yet |

## Downstream copies of katvan-owned skills

`librarian` (above) is katvan's first canonical skill — no sibling has
vendored it yet. When one does, add the consumer to its `Downstream
copies` cell so future broadcasts find it automatically.

## References

- AgentCulture skill supplier ledger (steward's authoritative map):
  <https://github.com/agentculture/steward/blob/main/docs/skill-sources.md>
- `steward announce-skill-update` — the broadcast verb that pings
  this repo when a vendored skill drifts.
