---
title: culture.dev marketing rebuild — design
date: 2026-05-17
status: draft
owner: katvan
supersedes: docs/superpowers/specs/2026-05-14-culture-site-migration-design.md
---

# culture.dev marketing rebuild — design

## Goal

Rebuild [culture.dev](https://culture.dev) as the AgentCulture org's
storefront — the single deployed surface that markets the `culture`
product and the broader Organic Development framework to developers
building agentic systems.

The job is **positioning**, not documentation. The 20 sibling repos in
the `agentculture/` GitHub org are inventory, not the menu. Each one
gets a stable, well-written page on the site; the landing experience
sells the product.

## Audience and conversion

- **Primary reader:** a developer who already believes AI agents
  matter and is shopping for tooling.
- **Conversion:** `uv tool install culture` followed by `culture start`,
  and joining the mesh. A copyable install command is on every
  high-traffic page.
- **Secondary reader:** a tech lead or founder evaluating "a workspace
  for humans and AI agents" as a real idea. Their conversion is reading
  the manifesto and reaching out / starring. The landing page lets them
  reach the manifesto in one click without diluting the dev path.

## Headline and voice

**Headline (locked):** *The professional workspace for humans and AI
agents.*

**Voice rules:**

- Confident, not breathless. No "revolutionary," "seamlessly,"
  "powered by AI."
- Technical-as-default. Real commands, real binaries, real protocols.
- One claim per sentence. Cut hedges.
- Show, then frame. Command first, prose second.
- No anthropomorphism inflation. Agents are processes that hold
  context.
- No emoji on culture.dev.
- Verbs over nouns. Numbers when they exist.
- Second person on landing; third person in docs.
- Every page has exactly one primary action.

**Naming convention:**

- Org: **AgentCulture** (one word, capitalized).
- Product: `culture` (lowercase, code-style).
- Mesh: the **Culture mesh**.

These are pinned in a `site/_data/style.yml` style note and referenced
by all anchor copy.

## Information architecture

### Top nav (fixed, four items)

`Quickstart` · `Docs` · `Ecosystem` · `Why`

Plus a small GitHub icon link. No mega-menu.

### Landing page (`/`) — four bands, single scroll

1. **Hero band.** Headline, one supporting sentence, copyable
   `uv tool install culture` block, copyable `culture start` second
   command, ~30s asciinema cast of two agents talking in a channel.
   One primary CTA only.
2. **Three-pill capabilities band.** *Persistent agents · IRC-native
   mesh · Works with your stack.* Each pill: title + 2-sentence
   paragraph + "Learn more →" deep link. No screenshots.
3. **Ecosystem band.** Registry categories as cards (not a table).
   Card order is conversion-shaped, not alphabetical — the first
   three cards are always:
   1. Workspace Experience (culture, agex-cli, afi-cli)
   2. Core Runtime (agentirc, irc-lens)
   3. Identity & Secrets (zehut, shushu)

   The remaining cards (Resident Culture, Resident Domain, Org Site)
   follow, in that order. Each card lists its repos as chips linking
   to the per-repo page.

   **Category assignments for the 7 unregistered repos** (`agtag`,
   `antoine`, `appsec`, `code-lens-cli`, `cultureagent`, `katvan`,
   plus reconciliation of `cultureflare`/`cfafi`) are made during the
   registry true-up (migration step 1), not pre-decided here. If
   Resident Culture grows past ~6 entries during true-up, consider
   splitting it (e.g. *Resident Culture* vs. *Resident Tooling*)
   rather than shipping a 10-chip card.
4. **Why band.** One short paragraph framing Organic Development,
   "Read the manifesto →" link to `/why/`.

### Subtree

- `/quickstart/` — single page, top of funnel. Install, start, join a
  channel, talk to an agent.
- `/docs/` — conceptual prose, authored in katvan. Sub-IA mirrors the
  registry categories, but with marketing-grade overview pages, not a
  directory.
- `/docs/<repo>/` — per-repo page for all 20 repos. Hand-authored top
  section (*what it is*, *why you'd reach for it*, *where it sits*),
  then auto-pulled `/reference/` from `<repo> learn` + `explain`.
- `/ecosystem/` — same content as the landing band, expanded; the
  directory view for readers who want it.
- `/why/` — the manifesto. Organic Development, persistence,
  all-backends, agent-first.

### Internal pages (reachable, not promoted)

`/architecture/`, `/attention/`, `/coverage-baseline/` etc. — for
contributors, not first-time readers. Indexable but absent from the
top nav.

## Content model

| Content | Source | How it reaches culture.dev |
|---|---|---|
| Landing, capability pages, manifesto, category overviews | `katvan/site/` markdown, hand-authored | Native Jekyll build |
| Per-repo *what / why* prose | `katvan/site/docs/<repo>/index.md`, hand-authored | Native |
| Per-repo CLI reference | Sibling repo's `<binary> learn` + `<binary> explain` output | `katvan pull` writes `site/docs/<repo>/reference/` |
| Sibling README | Sibling repo (unchanged) | Not pulled. README links out to `https://culture.dev/<repo>/` |
| Sibling `docs/` trees | Sibling repos (unchanged, still maintained) | Not pulled. They serve in-repo technical readers, not the marketing site |

**Source separation.** Sibling `docs/` directories remain live, owned
by their repos, and serve a different audience (the in-repo technical
reader) from culture.dev (marketing + canonical concept + machine
reference). No deprecation markers, no freeze.

### Registry true-up

`site/_data/agentculture_repos.yml` becomes authoritative for all 20
public repos:

- **Add:** `agtag`, `antoine`, `appsec`, `code-lens-cli`,
  `cultureagent`, `katvan`.
- **Reconcile:** `cultureflare` (live) and `cfafi` (registry). Pick
  one slug; update the other side.
- **Collapse `docs_mode`** to two values:
  - `pull-reference` — sibling has an AFI-compatible binary; `katvan
    pull` syncs its CLI reference into `site/docs/<repo>/reference/`.
  - `skip` — no automated sync; the per-repo page on culture.dev is
    entirely hand-authored. (Daemons like `agentirc`, services like
    `shushu`, domain agents like `office-agent` fall here.)
- **Remove** `self-published` — no sibling deploys its own site
  anymore.

### `katvan` CLI narrowing

`katvan` keeps `learn` / `explain` / `overview` / `doctor`. The `pull`
verb is rewritten:

- **Old:** copy sibling `docs/` markdown into `site/docs/<repo>/` with
  Jekyll frontmatter injected.
- **New:** invoke each registered sibling's binary with `learn --json`
  + `explain --json` and render to deterministic markdown under
  `site/docs/<repo>/reference/`. No frontmatter injection drift, no
  freeform prose, smaller blast radius.

`doctor` is extended to require, for every registered repo:

1. A hand-authored `site/docs/<repo>/index.md`.
2. A successful reference sync where `docs_mode: pull-reference`.
3. A README link from the sibling repo back to
   `https://culture.dev/<repo>/`.

Doctor failures fail CI on katvan PRs.

## Anchor copy artifacts

Five pieces of writing get authored from scratch; everything else
derives from them.

1. **Headline + supporting sentence** (~25 words). Headline locked.
2. **Three capability pills** (~40 words each). The three things a dev
   needs to believe in 15 seconds.
3. **Quickstart page** (~150 words, interleaved with 4–5 commands).
   Zero-to-talking-to-an-agent in under two minutes.
4. **Manifesto** (~600 words) at `/why/`. The Organic Development
   argument — why a mesh, why IRC, why persistence, why all-backends.
   Longest piece of writing on the site; sets the brand.
5. **Per-repo "what & why"** (~80–120 words × 20). Same three-part
   template each time: *what it is* (one sentence), *why you'd reach
   for it* (one paragraph), *where it sits* (category and 1–2 related
   repos).

## Build and deploy

**Single Jekyll project, single deploy.** `katvan/site/` remains the
only build, using existing `_config.base.yml` + `_config.culture.yml`.
No new framework, CMS, or design system overhaul.

### CI pipeline

On PR and on push to `main` in katvan:

1. `uv tool install katvan` in the runner.
2. `katvan pull --all` — invokes registered sibling binaries and
   writes `site/docs/<repo>/reference/` deterministically. Reference
   sync output is committed in-tree (not a build-time side effect).
3. `bundle exec jekyll build --config _config.base.yml,_config.culture.yml --strict_front_matter`.
4. `katvan doctor` against the built site. Failures fail CI.

On `main`: same pipeline plus deploy step. Existing GitHub Pages
target stays; no new infrastructure.

### Reference sync cadence

- Bot-PR workflow: a sibling release triggers a `workflow_dispatch`
  hook in katvan; the bot opens a PR with the updated reference
  output. **A human reviews the diff before it ships.** No auto-merge.
- Nightly cron as a fallback for repos without release hooks.
- Sibling releases never block culture.dev builds.

### Sibling Jekyll site teardown

User executes the teardown. Design assumes done. After cut-over,
external inbound links to retired sibling Pages URLs 404. No redirect
layer is added — traffic is low and the repo set is finite.

### DNS / Cloudflare

No change. `cfafi` / `cultureflare` owns the edge; culture.dev →
GitHub Pages stays as-is.

### Analytics

**Self-hosted Plausible** on culture.dev only. Measure: landing →
quickstart conversion, landing → manifesto conversion, install-command
copy events. No per-page funnels in v1.

### Search

Jekyll's built-in `site.posts` / `site.pages` is enough for v1. Add a
small client-side fuzzy index over `site/docs/**/*.md` titles +
summaries only if content exceeds ~30 pages.

### Robots / sitemap

Existing `sitemap.html` / `sitemap-main.html` regenerates per build.
`/architecture/` and other internal pages remain indexable but absent
from nav. No AI-crawler exclusions.

### Versioning

Site is unversioned (latest only). Per-repo reference reflects the
latest released CLI.

## Migration order

The implementation plan will detail each; this is the shape.

1. **Registry true-up PR.** Add the 7 unregistered repos, reconcile
   `cultureflare`/`cfafi`, collapse `docs_mode` to `pull-reference` /
   `skip`, drop `self-published`. No site changes yet.
2. **Narrow `katvan pull`.** Rewrite the verb to invoke
   `<binary> learn/explain --json` and emit deterministic markdown.
   Delete old freeform pull code. Update `doctor`.
3. **Author the five anchor copy artifacts.** Headline, supporting
   sentence, three pills, quickstart, manifesto, per-repo template.
   Real copy on a content branch.
4. **Build the new IA.** Landing page (4 bands), `/quickstart/`,
   `/why/`, `/ecosystem/`, 6 category overview pages, 20 per-repo
   `index.md` pages from the template. Old `site/docs/<repo>/`
   freeform content is removed in the same PR.
5. **CI: reference sync + doctor gate.** Add the bot-PR workflow that
   runs `katvan pull --all` on a cadence + the doctor check on every
   PR.
6. **Analytics + sitemap.** Wire Plausible (self-hosted), regenerate
   sitemap, confirm robots.
7. **Sibling-side coordination.** Open a tracking issue per sibling
   whose Jekyll deploy is being shut down (user executes teardown).
   Update each sibling README to point its "Docs" link at
   `https://culture.dev/<repo>/`.
8. **File OOS tracking issues in katvan** (see below).
9. **Cut-over.** Merge, deploy, watch.

## Out of scope (tracked separately)

The implementation plan files one tracking issue in katvan per OOS
surface, each with a one-paragraph brief, so the work isn't lost:

- **Visual / design uplift.** Typography, color, layout polish beyond
  the existing theme. Plain Jekyll + current theme is the v1 contract.
- **Sibling Jekyll teardown.** User executes; this issue documents
  the surfaces and tracks confirmation per sibling.
- **Tutorials beyond quickstart.** A learning track for the dev who
  finished quickstart.
- **Blog / changelog / case studies.** A regular publishing cadence.
- **Comparison-vs-X pages.** Positioning against neighbors.
- **Public roadmap.** What's next, when, why.
- **Docs versioning.** Latest-only is v1.
- **Per-page A/B testing or growth experiments.**
- **AI-crawler controls, paid SEO, link-building campaigns.**

Also out of scope (no issue filed):

- The `landing-page` repo (stays as its own deployment).
- Repo structural changes (merges, splits, renames) — not driven by
  this design. In-flight renames (e.g. `cultureflare`→`cfafi`) are
  tracked in the registry true-up but executed elsewhere.
- Any change to the `culture` repo itself.

## Definition of "damn great"

The rebuild ships when all five hold:

1. A dev reading `/` for the first time can install and start culture
   inside 60 seconds without leaving the page.
2. A team-lead reader can get from `/` to the manifesto in one click
   and read it in under 3 minutes.
3. Every one of the 20 repos has a stable, discoverable, well-written
   page at `culture.dev/<repo>/`.
4. The site builds, deploys, and reference-syncs without human
   intervention beyond reviewing bot PRs.
5. Voice is consistent across all hand-authored pages — a stranger
   couldn't tell which were written first.
