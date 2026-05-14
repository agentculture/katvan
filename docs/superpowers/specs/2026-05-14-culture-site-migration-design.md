# Migrate culture.dev Jekyll site into katvan — Phase 0a

**Date:** 2026-05-14
**Issue:** [agentculture/katvan#1](https://github.com/agentculture/katvan/issues/1)
**Status:** Design approved — pending implementation plan

## Context

culture.dev's Jekyll docs site currently lives bundled inside
`agentculture/culture`, alongside the Python agent runtime. Issue #1
(Phase 0a) moves the site into katvan so that:

- culture's repo can shed its Ruby/Jekyll tooling and focus on Python
- katvan owns culture.dev end-to-end (link audits, freshness checks,
  search wiring) without coordinating with culture's release cadence
- the same pattern repeats later for sibling-repo sites

**Hard invariant — the site must not go dark.** This phase only stands
up a *green build* of the site inside katvan. It does **not** touch
production. Cloudflare repointing (Pages source repo, Workers/redirect
rules) and culture's Phase 1 deletion PR are separate, later briefs,
gated on katvan posting a "ready" signal with a green-build SHA.

This is a **behavior-preserving move**: no content rewrites, no new or
removed pages, no restructuring beyond what the new repo layout forces.

## Key decisions

Settled during brainstorming (issue #1's brief left these open or, in
one case, got a fact wrong):

1. **`docs/superpowers/` and `docs/resources/` are NOT migrated.** They
   stay in culture. The issue brief claimed they "are in the build —
   neither is excluded"; this is factually wrong — culture's
   `_config.base.yml` `exclude:` list contains both. They are not
   published today, and we are not copying them. A pushback comment
   will be filed on issue #1 noting the correction.
2. **Two-increment phased migration**, landed as two PRs (toolchain,
   then content) — de-risks the Ruby/Bundler/just-the-docs toolchain
   separately from the ~131-file content drop.
3. **Site config keeps the name `_config.culture.yml`.** Configs are
   named by the *site* they build, not the repo. This scales cleanly
   when more sites arrive.
4. **The whole Jekyll project lives under `site/`.** Repo-root `docs/`
   stays katvan's *internal* repo docs (skill ledger, design specs).
   The Jekyll build root is `site/`; culture's `docs/` content tree is
   reparented verbatim to `site/docs/`.

## Target layout

```
katvan/
├── docs/                       # katvan internal repo docs (NOT the site)
│   ├── skill-sources.md
│   └── superpowers/specs/      # katvan design docs incl. this file
├── site/                       # Jekyll build root
│   ├── _config.base.yml
│   ├── _config.culture.yml
│   ├── _data/
│   │   ├── sites.yml
│   │   ├── agentculture_repos.yml
│   │   └── culture_subcommands.yml
│   ├── _includes/
│   │   ├── head_custom.html
│   │   ├── repo_table.html
│   │   └── subcommand_table.html
│   ├── _sass/
│   │   ├── color_schemes/      # dark-terminal.scss, anthropic.scss
│   │   └── custom/custom.scss
│   ├── assets/images/          # favicons, apple-touch-icon, og-*, IMG_3183.png
│   ├── docs/                   # culture's docs/ tree, verbatim
│   │                           #   minus docs/superpowers/ + docs/resources/
│   ├── Gemfile
│   └── Gemfile.lock
├── .github/workflows/docs-check.yml
├── .gitignore                  # + Jekyll entries
├── README.md                   # updated to describe the site
├── CHANGELOG.md
├── culture.yaml                # unchanged
├── LICENSE                     # unchanged
├── sonar-project.properties    # unchanged
└── .claude/                    # unchanged
```

## Increment 1 — toolchain (PR 1)

Branch: `docs/site-toolchain`.

**Copy into `site/` (byte-for-byte from `../culture`):**

- `_config.base.yml`, `_config.culture.yml`
- `Gemfile`, `Gemfile.lock`
- `_includes/` (3 files)
- `_sass/` (`color_schemes/`, `custom/`)
- `assets/` (`images/` — favicons, og images, `IMG_3183.png`)
- `_data/` (`sites.yml`, `agentculture_repos.yml`,
  `culture_subcommands.yml`)

**Adapt `site/_config.base.yml` — trim the `exclude:` list only.**
culture's list names Python directories (`culture/`, `server/`,
`clients/`, `protocol/`, `tests/`, `packages/`, `scripts/`,
`plugins/`, `pyproject.toml`, `uv.lock`, `__pycache__/`,
`culture.yaml`, `CLAUDE.md`, `.github/`, `.claude/`, `.superpowers/`,
`README.md`, `LICENSE`, `.gitignore`) that do not exist under `site/`,
plus `docs/superpowers/` and `docs/resources/` which we are not
copying. Trim to the entries that are still meaningful under `site/`:

```yaml
exclude:
  - Gemfile
  - Gemfile.lock
  - _site/
  - _site_culture/
```

This is a config edit, not a content change — it does not alter *what
gets published*. Every removed entry pointed at a path that does not
exist in `site/`.

**Add a stub homepage** `site/docs/index.md`:

```markdown
---
title: Culture
permalink: /
---

Stub homepage — replaced with culture's real `docs/culture/index.md`
in Increment 2.
```

Increment 1 only needs to prove the toolchain builds; the real
homepage (which uses custom SCSS classes and includes) lands with the
content tree in Increment 2.

**Add `.github/workflows/docs-check.yml`** — adapted from culture's:

- Triggers: `pull_request` + `push` to `main`
- `ruby/setup-ruby` @ Ruby 3.3, `bundler-cache: true`,
  `working-directory: site` (so it finds `site/Gemfile`)
- Build step runs in `site/`:
  `bundle exec jekyll build --config _config.base.yml,_config.culture.yml -d _site_culture`
  with `JEKYLL_ENV: production`
- Job/step names renamed culture → katvan; no deploy step (Cloudflare
  Pages handles deploy post-cutover — out of scope)

**Update `.gitignore`** — add Jekyll build artefacts:

```
site/_site/
site/_site_culture/
site/.jekyll-cache/
site/vendor/
```

**Increment 1 done when:** `cd site && bundle install && bundle exec
jekyll build --config _config.base.yml,_config.culture.yml -d
_site_culture` exits 0 locally, and CI `docs-check` is green on PR 1.

## Increment 2 — content (PR 2)

Branch: `docs/site-content`.

- Copy culture's `docs/` tree into `site/docs/` **verbatim**,
  **excluding** `docs/superpowers/` and `docs/resources/`. Everything
  else under `docs/` comes across unchanged: `agentirc/`,
  `architecture/`, `culture/`, `reference/`, `shared/`,
  `attention.md`, `coverage-baseline.md`, `README.md`.
- Replace the stub `site/docs/index.md` with culture's real
  `docs/culture/index.md` (it carries `permalink: /`).
- Update repo-root `README.md` to describe katvan as the home of the
  culture.dev site (and future sibling sites).
- Update `CHANGELOG.md`.

**Increment 2 done when:** the full build is green (local + CI), page
parity holds (see Verification), and the homepage / `/agentirc/` /
nav / search / theme all render. This is the **"ready" milestone**.

## Behavior-preserving guarantees

- **Permalinks** are declared in page frontmatter — reparenting the
  tree under `site/` does not change any URL.
- **`jekyll-relative-links`** resolves links relative to each file's
  location. The whole tree moves together, so intra-doc links still
  resolve.
- **`_data/`, `_includes/`, `_sass/`, `assets/`, `Gemfile.lock`** are
  copied byte-for-byte — same templates, same locked gem versions.
- **Build command** is unchanged except for running inside `site/`.
  Output dir stays `_site_culture` (now `site/_site_culture`).
- **`_config.base.yml`** — only the `exclude:` list is trimmed of dead
  entries; nothing that affects published output changes.

## Out of scope

- **Cloudflare** — Pages source-repo repoint, Workers/redirect rules,
  production domain wiring. Separate brief on `agentculture/cloudflare`.
- **culture's Phase 1 deletion PR** — culture files it after katvan
  signals ready.
- **Content rewrites** — none. Behavior-preserving move only.
- **`docs/superpowers/` and `docs/resources/`** — stay in culture.
- **Multi-site future** — the user's longer-term intent is to *merge*
  sibling-repo sites into this one site (cultureagent, daria, steward
  content becoming path-prefixed subtrees under `site/docs/`, the way
  `/agentirc/` already is). This spec does not design that; it only
  establishes the `site/` home that makes it possible later.
- **katvan product features** — link audits, freshness checks, search
  index tuning. Future work, separate specs.

## Verification — the "ready" gate

1. **Build:** `cd site && bundle install && bundle exec jekyll build
   --config _config.base.yml,_config.culture.yml -d _site_culture`
   with `JEKYLL_ENV=production` → exits 0, no errors or warnings about
   missing files.
2. **Page parity:** count generated `.html` files in
   `site/_site_culture`; compare against a fresh build of culture's
   site with `docs/superpowers/` and `docs/resources/` excluded. The
   page set must match — same pages, no additions, no removals.
3. **Visual spot-check:** `bundle exec jekyll serve` and confirm:
   homepage `/`, `/agentirc/`, sidebar nav tree, search box, a
   `/reference/` page, and the `dark-terminal` theme all render as on
   culture.dev today.
4. **CI:** `docs-check` workflow green on PR 2.
5. **Signal ready:** post a one-line reply on issue #1 with the SHA of
   the green-build commit, signed `- katvan (Claude)`. That is
   culture's go-signal to file the Phase 1 cutover PR and the
   `agentculture/cloudflare` brief.

## Files referenced

Source (read-only, `../culture`):

- `_config.base.yml`, `_config.culture.yml`, `Gemfile`, `Gemfile.lock`
- `_includes/`, `_sass/`, `_data/`, `assets/`
- `docs/` (the content tree)
- `.github/workflows/docs-check.yml`

Target (`katvan`):

- `site/` (new — entire Jekyll project)
- `.github/workflows/docs-check.yml` (new)
- `.gitignore` (edit — add Jekyll artefacts)
- `README.md`, `CHANGELOG.md` (edit, Increment 2)
