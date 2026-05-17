---
title: Existing site/docs/ audit — pre-rebuild
date: 2026-05-17
status: draft
owner: katvan
related: docs/superpowers/plans/2026-05-17-culture-dev-marketing-rebuild.md
---

# Existing site/docs/ audit — 2026-05-17

Audit of every file under `site/docs/` against the new IA defined in
`docs/superpowers/specs/2026-05-17-culture-dev-marketing-rebuild-design.md`.

Per file, one decision:

- **keep** — content folds into the new IA unchanged (reachable, not nav-promoted).
- **fold** — content has reusable prose that should merge into a new
  hand-authored page (target named in Notes).
- **retire** — superseded by the new IA, nothing salvageable.
- **defer** — context insufficient; flag for human review.

When in doubt between fold and retire, decision is **fold** — Task 13 can
still discard during application.

73 files in scope (`find site/docs -type f \( -name "*.md" -o -name
"*.html" -o -name "*.yaml" \) | wc -l = 73`). No file is deleted, moved,
or rewritten by this task — Task 13 applies these decisions.

## Decisions

| File | Decision | Target / Notes |
|---|---|---|
| site/docs/README.md | retire | Stale internal "Docs Rules" listing dual-site assumptions (culture.dev + agentirc.dev). New IA is single-site; rules are obsolete. |
| site/docs/attention.md | keep | Internal architecture/feature note (Dynamic Attention Levels, culture feature). Reachable under `/architecture/` per spec ("/architecture/, /attention/, /coverage-baseline/" are explicitly reachable-not-promoted in the spec). |
| site/docs/coverage-baseline.md | keep | Internal contributor doc; explicitly listed in spec as reachable-not-promoted. |
| site/docs/architecture/shared-vs-cited.md | keep | Internal architecture note; spec names this kind of file as the kept example for `/architecture/`. |
| site/docs/agentirc/index.md | fold | Target: `/docs/agentirc/index.md` (per-repo "what / why / where" page in new IA). Existing hero copy + supporting prose can salvage into the new template. |
| site/docs/agentirc/architecture-overview.md | fold | Target: `/docs/agentirc/index.md` "where it sits" + linked deep-dive. Long architecture prose; deep technical content is in-repo at agentirc, but the marketing-grade "what it is" intro is salvageable. |
| site/docs/agentirc/audit.md | retire | Detailed audit-log telemetry feature doc. Belongs in the agentirc repo's `docs/`, not on the marketing site. Reference content for this will come from `agentirc learn`/`explain` via `katvan pull` (or, if agentirc isn't `pull-reference`, sibling repo's docs/). |
| site/docs/agentirc/bots.md | retire | Same rationale as audit.md — feature reference owned by the agentirc repo's docs, not the marketing site. |
| site/docs/agentirc/events.md | retire | Feature reference — sibling repo's docs/. |
| site/docs/agentirc/harness-telemetry.md | retire | Feature reference — sibling repo's docs/. |
| site/docs/agentirc/otelcol-template.yaml | retire | Template config artifact. Belongs in the agentirc repo, not the marketing site. |
| site/docs/agentirc/peek-clients.md | retire | Feature reference — sibling repo's docs/. |
| site/docs/agentirc/telemetry.md | retire | Feature reference — sibling repo's docs/. |
| site/docs/agentirc/why-agentirc.md | fold | Target: `/docs/agentirc/index.md` ("why you'd reach for it" paragraph). Concise, marketing-grade — directly reusable. |
| site/docs/culture/index.md | fold | Target: landing `/` (hero band) + `/docs/culture/index.md`. Existing hero copy is the old headline; new headline is locked ("The professional workspace for humans and AI agents") and supersedes. Some prose ("Persistent rooms. Real colleagues...") salvageable. |
| site/docs/culture/agent-lifecycle.md | fold | Target: `/docs/culture/index.md` "where it sits" or a category overview page. Contains DaRIA-walkthrough; long. Some emoji per-section — voice rules forbid emoji on culture.dev, will need scrubbing in Task 13. |
| site/docs/culture/choose-a-harness.md | fold | Target: `/ecosystem/` Core Runtime category overview page or `/docs/culture/index.md`. Comparison-style content fits an ecosystem context. |
| site/docs/culture/ecosystem-map.md | fold | Target: `/ecosystem/` page (spec band 3 + expanded ecosystem page). Closely mirrors the new ecosystem-band content; prose directly reusable. |
| site/docs/culture/features.md | fold | Target: capability-pill deep-link pages OR `/docs/culture/index.md`. The feature-grouping concept overlaps the three capability pills but isn't a one-to-one match — leave Task 13 to cherry-pick. |
| site/docs/culture/mental-model.md | fold | Target: `/why/` manifesto. Spaces / membership / persistence framing belongs in the Organic Development argument. |
| site/docs/culture/operate.md | retire | Stub page that just lists links to reference/server/*. Superseded by per-repo `/docs/culture/` page + auto-pulled reference. |
| site/docs/culture/patterns.md | fold | Target: `/why/` manifesto. Pattern-language framing supports the OD argument; prose reusable. |
| site/docs/culture/quickstart.md | fold | Target: `/quickstart/` (anchor copy artifact #3). Existing content is the prior quickstart — must merge into the new ~150-word version. Task 13 must reconcile with the new locked artifact authored in Task 8. |
| site/docs/culture/reflective-development.md | fold | Target: `/why/` manifesto. "Reflective Development" is core to the Organic Development pitch. |
| site/docs/culture/vision.md | fold | Target: `/why/` manifesto (anchor copy artifact #4). Prose is closest to manifesto voice already; primary fold candidate. |
| site/docs/culture/vision-patterns-index.md | retire | Stub index page for a "Vision & Patterns" subsection that doesn't exist in the new IA. |
| site/docs/culture/what-is-culture.md | fold | Target: landing `/` hero supporting sentence + `/docs/culture/index.md` "what it is" sentence. Tight definition prose — salvageable. |
| site/docs/reference/index.md | retire | Top-level "Reference" stub. New IA has per-repo `/docs/<repo>/reference/` (auto-pulled), no central /reference/ hub. |
| site/docs/reference/console.md | retire | Legacy TUI console note, marked "preserved for historical reference." The current console reference will be pulled into `/docs/irc-lens/reference/` (or wherever irc-lens lives). Nothing salvageable for marketing. |
| site/docs/reference/architecture/index.md | retire | Stub. See `/architecture/` note: internal arch pages survive at `/architecture/` per spec, but this `reference/architecture/index.md` stub is duplicate scaffolding. |
| site/docs/reference/architecture/agent-harness-spec.md | keep | Internal architecture spec — exactly the kind of doc the spec lists under `/architecture/` (reachable, not promoted). Task 13 should relocate to `/architecture/agent-harness-spec.md`. |
| site/docs/reference/architecture/layers.md | keep | Internal architecture (5-layer model). Same rationale as agent-harness-spec.md — move under `/architecture/`. |
| site/docs/reference/architecture/subsites.md | keep | Internal architecture pattern doc (sub-site reference scaffold). Move under `/architecture/`. |
| site/docs/reference/architecture/threads.md | keep | Internal architecture / protocol doc on conversation threads. Move under `/architecture/`. |
| site/docs/reference/cli/index.md | retire | Stub for old central CLI hub. Superseded by per-repo `/docs/<repo>/reference/` (auto-pulled from `<binary> learn/explain`). |
| site/docs/reference/cli/afi.md | retire | CLI reference for afi-cli — will be replaced by `/docs/afi-cli/reference/` auto-pulled from `afi learn/explain` (afi-cli is `pull-reference` per spec). |
| site/docs/reference/cli/agent-systemd.md | retire | CLI reference fragment — will be auto-pulled into `/docs/culture/reference/` from `culture learn/explain`. |
| site/docs/reference/cli/commands.md | retire | Top-level culture CLI page — auto-pulled into `/docs/culture/reference/`. |
| site/docs/reference/cli/console.md | retire | CLI reference for `culture console` — auto-pulled. |
| site/docs/reference/cli/devex.md | retire | CLI reference for `culture devex` / agex passthrough — auto-pulled (agex-cli is `pull-reference`). |
| site/docs/reference/harnesses/index.md | retire | Reference hub stub. New IA: harness-specific content lives under each harness's per-repo `/docs/<repo>/` page (claude harness, codex harness, etc. — likely folded into culture or cultureagent per-repo pages). |
| site/docs/reference/harnesses/claude.md | fold | Target: `/docs/cultureagent/index.md` or `/docs/culture/index.md` "where it sits" — the harness lives in cultureagent per spec. Some prose ("daemon that turns Claude Code into IRC-native") salvageable for the per-repo "what" sentence. |
| site/docs/reference/harnesses/codex.md | fold | Target: same as claude.md (cultureagent per-repo page). |
| site/docs/reference/harnesses/copilot.md | fold | Target: same as claude.md. |
| site/docs/reference/harnesses/acp.md | fold | Target: same as claude.md. |
| site/docs/reference/server/index.md | fold | Target: `/docs/agentirc/index.md` "what it is" / `/docs/culture/index.md`. Tight intro prose ("custom async Python IRCd built from scratch ... ~4,300 lines") is high-quality marketing-grade prose; reuse. |
| site/docs/reference/server/architecture.md | retire | Code-level startup-sequence internals. Belongs in the agentirc repo's docs/, not the marketing site. |
| site/docs/reference/server/config.md | retire | Server config reference — auto-pulled from `culture learn/explain` (or agentirc's binary). |
| site/docs/reference/server/deployment.md | retire | Deployment instructions — auto-pulled from `culture learn/explain`. |
| site/docs/reference/server/security.md | retire | Security-scanning setup specific to the culture repo's CI. Belongs in the culture repo's CONTRIBUTING.md / repo docs. |
| site/docs/shared/concepts/index.md | retire | Stub for shared-site concepts hub. Old dual-site (culture + agentirc) framing; new IA has one site. |
| site/docs/shared/concepts/federation.md | fold | Target: `/why/` manifesto (federation is core to "why a mesh") OR `/docs/agentirc/index.md` "where it sits." Marketing-quality definition prose. |
| site/docs/shared/concepts/harnesses.md | fold | Target: `/docs/cultureagent/index.md` "what it is" intro + capability-pill deep-link. |
| site/docs/shared/concepts/humans-and-agents.md | fold | Target: `/why/` manifesto. "Humans and agents as first-class participants" is the headline thesis ("workspace for humans and AI agents"). |
| site/docs/shared/concepts/persistence.md | fold | Target: capability-pill deep-link page for "Persistent agents" (pill 1 per spec) + `/why/` manifesto (persistence is one of the four manifesto pillars). |
| site/docs/shared/concepts/rooms.md | fold | Target: capability-pill deep-link for "Persistent agents" / "IRC-native mesh" + `/docs/agentirc/index.md`. Concrete protocol-level content. |
| site/docs/shared/demos/magic-demo.md | defer | Walkthrough demo. Could fold into `/quickstart/` (asciinema content) or retire if the new quickstart's ~30s asciinema cast supersedes. Need to know whether the hero band's asciinema will be re-recorded fresh (likely yes per spec — "~30s asciinema cast of two agents talking in a channel") — if so, retire; if the existing cast or its script is reused, fold. Flag for human review in Task 13. |
| site/docs/shared/guides/index.md | retire | Stub. New IA: `/quickstart/` is the one promoted guide; there's no top-level "/guides/" subtree. |
| site/docs/shared/guides/first-session.md | fold | Target: `/quickstart/` (anchor copy artifact #3). Some commands and walkthrough beats salvageable into the new ~150-word version. |
| site/docs/shared/guides/join-as-human.md | fold | Target: `/quickstart/` extension or `/docs/culture/index.md` "where it sits." Specific to one path (human joining); could be a quickstart variant. |
| site/docs/shared/guides/local-setup.md | fold | Target: `/quickstart/` prerequisites section. |
| site/docs/shared/guides/multi-machine.md | fold | Target: `/docs/culture/index.md` "what it is" or `/docs/agentirc/index.md` "where it sits" — federation is a culture/agentirc capability. Also feeds capability-pill 2 ("IRC-native mesh") deep-link. |
| site/docs/shared/use-cases-index.md | fold | Target: `/why/` manifesto (use cases ground the OD argument in real scenarios) OR a single "Use cases" gallery page reachable from `/ecosystem/`. Index-only — Task 13 may collapse with retire of the children. |
| site/docs/shared/use-cases/01-pair-programming.md | fold | Target: `/why/` (1-2 sentence story embedded) or retire if not used. Strong narrative material but ~10 of these is long-form content; the spec doesn't carve out a use-cases subtree. Salvage one or two paragraph-length stories. |
| site/docs/shared/use-cases/02-code-review-ensemble.md | fold | Same rationale as 01-pair-programming.md. |
| site/docs/shared/use-cases/03-cross-server-delegation.md | fold | Same. |
| site/docs/shared/use-cases/04-knowledge-propagation.md | fold | Same. |
| site/docs/shared/use-cases/05-the-observer.md | fold | Same. |
| site/docs/shared/use-cases/06-cross-server-ops.md | fold | Same. |
| site/docs/shared/use-cases/07-supervisor-intervention.md | fold | Same. |
| site/docs/shared/use-cases/08-apps-as-agents.md | fold | Same. |
| site/docs/shared/use-cases/09-research-swarm.md | fold | Same. |
| site/docs/shared/use-cases/10-agent-lifecycle.md | fold | Same. The agent-lifecycle story also overlaps with `culture/agent-lifecycle.md` — Task 13 should reconcile both into a single "lifecycle" narrative if used. |

## Decision tally

- keep: 6
- fold: 35
- retire: 31
- defer: 1
- **total: 73** (matches `wc -l /tmp/existing_docs.txt`)

## Cross-cutting notes for Task 13

1. **Emoji scrub.** Existing `culture/agent-lifecycle.md` contains emoji
   section headers; voice rules ban emoji on culture.dev. Any fold that
   keeps those headers must scrub.
2. **Use-cases consolidation.** 10 use-case files exist plus a use-cases
   index plus a `culture/agent-lifecycle.md` covering similar ground. The
   new IA has no `/use-cases/` subtree promoted. Task 13 should pick at
   most a handful of paragraph-length stories for the manifesto / ecosystem
   page and retire the rest.
3. **Quickstart reconciliation.** Three files feed `/quickstart/`:
   `culture/quickstart.md`, `shared/guides/first-session.md`,
   `shared/guides/local-setup.md`. The new quickstart is locked at ~150
   words (anchor copy artifact #3) and is authored fresh in Task 8.
   Task 13 cherry-picks command lines / prereq snippets, does NOT merge
   prose wholesale.
4. **Architecture relocation.** Four `keep` files under
   `site/docs/reference/architecture/` should be moved to `/architecture/`
   in Task 13 to match the spec's IA (`/architecture/` is the named
   reachable-not-promoted internal subtree). The two `keep` files at
   `site/docs/attention.md` and `site/docs/coverage-baseline.md` are
   already at root and stay (or move to `/attention/`, `/coverage-baseline/`
   per their existing permalinks).
5. **The single `defer`** is `shared/demos/magic-demo.md` — its disposition
   depends on whether the new hero asciinema cast (Task 11) reuses any of
   its content.

## Application log (Task 13, 2026-05-18)

Decisions applied in five commits on `feat/culture-dev-marketing-rebuild`.
Of the 73 in-scope files, the new IA pages locked in Tasks 7-12 turned out
to be tight enough that almost every "fold" decision was discharged as
"retire" under the audit's "be ruthless" rule. The new `/why/`,
`/quickstart/`, `/ecosystem/`, per-repo `/docs/<id>/`, and category pages
already say what the old long-form pages were saying, with better voice.

| Commit | Group | Files | Net |
|---|---|---|---|
| `90328c0` | Retire agentirc feature reference pages | 7 | -1207 |
| `591f6cb` | Retire central `/reference/` hub and stubs | 14 | -2046 |
| `dbe88aa` | Promote `/architecture/*` + retire stubs | 14 | +59/-107 |
| `d05f8a0` | Retire superseded `culture/*` deep-dives | 10 | -1091 |
| `b8209a9` | Retire remaining fold-source pages | 27 | -4662 |

Decision-by-decision outcome:

- **6 keep** — all 6 honored. The 4 under `reference/architecture/` were
  moved to `/architecture/` (per spec); `attention.md` and
  `coverage-baseline.md` stay at root with their existing permalinks.
  All 6 picked up proper frontmatter (the 3 that lacked it: `attention`,
  `coverage-baseline`, `shared-vs-cited`). Added `architecture/index.md`
  as a parent landing page for the subtree.
- **35 fold** — discharged as: 0 fold-into-existing, 35 retire. Rationale
  on every culture/* and shared/* file: prose is longer / weaker / has
  emoji / duplicates the new locked copy. The new `culture/index.md`,
  `agentirc/index.md`, and `cultureagent/index.md` already supersede the
  old long-form prose. The single fold that genuinely had unique prose
  (`reference/server/index.md`: "custom async Python IRCd ... ~4,300
  lines") was retired rather than degrade the tight new agentirc/index.md
  by appending implementation trivia.
- **31 retire** — all 31 honored.
- **1 defer** (`shared/demos/magic-demo.md`) — flipped to **retire**. The
  Task 11 hero band is authoring a fresh asciinema cast; the old walkthrough
  is not reused.

Cross-cutting outcomes:

- The `/quickstart/` permalink conflict between `docs/culture/quickstart.md`
  and `docs/quickstart.md` is gone — the old file was retired (Task 8's new
  copy is authoritative).
- Build is clean: `bundle exec jekyll build` produces no permalink conflicts
  and no real errors. One pre-existing-style Liquid warning was fixed by
  wrapping a `<project>` placeholder in `{% raw %}` in `architecture/subsites.md`.
- `katvan doctor` shows only the expected baseline FAILs: 9 `missing
  site/docs/<repo>/reference/index.md` for `pull-reference` repos that
  haven't been pulled in CI yet (`afi-cli`, `agex-cli`, `agtag`,
  `auntiepypi`, `code-lens-cli`, `culture`, `cultureagent`, `ghafi`,
  `irc-lens`). All WARNs are sibling-repo README link-back issues
  (Task 18 / 19, not Task 13).
- The empty `site/docs/reference/` and `site/docs/shared/` directory trees
  were removed entirely once their last files were retired.

No file remains with a "defer" decision unresolved. No file from the audit
was missed; no new files appeared in `site/docs/` since the audit was
taken.

## Coordination issues filed (2026-05-18)

Filed from inside `/home/spark/git/katvan` via `agtag issue post` (auto-signs
as `- katvan (Claude)`). No duplicates detected at file time. All 20 sibling
repos in the registry needed a README backlink issue; `katvan` itself
skipped per Task 18 spec.

### Jekyll teardown (Part A)
- agentculture/afi-cli#20 — teardown Jekyll
- agentculture/agex-cli#44 — teardown Jekyll

### README backlinks (Part B)
- agentculture/agentirc#30 — README link
- agentculture/irc-lens#45 — README link
- agentculture/cultureagent#29 — README link
- agentculture/culture#400 — README link
- agentculture/agex-cli#45 — README link
- agentculture/afi-cli#21 — README link
- agentculture/antoine#26 — README link
- agentculture/code-lens-cli#5 — README link
- agentculture/zehut#17 — README link
- agentculture/shushu#15 — README link
- agentculture/agtag#12 — README link
- agentculture/auntiepypi#23 — README link
- agentculture/cultureflare#37 — README link
- agentculture/ghafi#8 — README link
- agentculture/steward#37 — README link
- agentculture/appsec#10 — README link
- agentculture/office-agent#64 — README link
- agentculture/telek#2 — README link
- agentculture/tipalti#8 — README link
- agentculture/landing-page#3 — README link
- katvan — skipped (this repo; handled via the rebuild PR itself, not a self-issue)

No errors encountered.
