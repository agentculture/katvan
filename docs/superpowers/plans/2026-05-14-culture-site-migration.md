# culture.dev Site Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the culture.dev Jekyll docs site out of `agentculture/culture` into `agentculture/katvan`, behavior-preserving, as two PRs (toolchain, then content), with a green CI build.

**Architecture:** The entire Jekyll project lives under `site/` in katvan; repo-root `docs/` stays katvan-internal. PR 1 copies Jekyll config/theme/data/assets + a stub homepage + CI workflow, proving the Ruby/Bundler/just-the-docs toolchain builds green in isolation. PR 2 copies culture's `docs/` content tree verbatim (minus `superpowers/` and `resources/`), swaps in the real homepage, and reaches the "ready" milestone.

**Tech Stack:** Jekyll 4.3, just-the-docs ~0.10, Ruby 3.3, Bundler, GitHub Actions (`ruby/setup-ruby`).

**Source repo (read-only):** `/home/spark/git/culture`
**Target repo:** `/home/spark/git/katvan`
**Spec:** `docs/superpowers/specs/2026-05-14-culture-site-migration-design.md`

**Branch flow:** This plan and the spec live on branch `docs/culture-site-migration`. PR 1 branches from it (so spec+plan ride along into PR 1). PR 2 branches from `main` after PR 1 merges.

---

## Pre-flight: file existence check

- [ ] **Step 1: Confirm source files exist**

Run:
```bash
ls /home/spark/git/culture/_config.base.yml \
   /home/spark/git/culture/_config.culture.yml \
   /home/spark/git/culture/Gemfile \
   /home/spark/git/culture/Gemfile.lock \
   /home/spark/git/culture/.github/workflows/docs-check.yml
ls -d /home/spark/git/culture/_includes /home/spark/git/culture/_sass \
      /home/spark/git/culture/_data /home/spark/git/culture/assets \
      /home/spark/git/culture/docs
```
Expected: every path lists without error. If any is missing, STOP — the spec's inventory is stale; re-explore `../culture` before continuing.

---

# PR 1 — Toolchain

Branch: `docs/site-toolchain` (from `docs/culture-site-migration`). PR targets `main`.

### Task 1: Create the toolchain branch

**Files:** none (git only)

- [ ] **Step 1: Branch from the planning-docs branch**

Run:
```bash
cd /home/spark/git/katvan
git checkout docs/culture-site-migration
git checkout -b docs/site-toolchain
```
Expected: `Switched to a new branch 'docs/site-toolchain'`

### Task 2: Copy Jekyll config, theme, data, and assets into `site/`

**Files:**
- Create: `site/_config.base.yml`, `site/_config.culture.yml`
- Create: `site/Gemfile`, `site/Gemfile.lock`
- Create: `site/_includes/` (head_custom.html, repo_table.html, subcommand_table.html)
- Create: `site/_sass/` (color_schemes/dark-terminal.scss, color_schemes/anthropic.scss, custom/custom.scss)
- Create: `site/_data/` (sites.yml, agentculture_repos.yml, culture_subcommands.yml)
- Create: `site/assets/` (images/ — favicons, og images, IMG_3183.png)

- [ ] **Step 1: Copy the files byte-for-byte**

Run:
```bash
cd /home/spark/git/katvan
mkdir -p site
cp /home/spark/git/culture/_config.base.yml    site/
cp /home/spark/git/culture/_config.culture.yml site/
cp /home/spark/git/culture/Gemfile             site/
cp /home/spark/git/culture/Gemfile.lock        site/
cp -r /home/spark/git/culture/_includes        site/
cp -r /home/spark/git/culture/_sass            site/
cp -r /home/spark/git/culture/_data            site/
cp -r /home/spark/git/culture/assets           site/
```

- [ ] **Step 2: Verify the tree landed**

Run:
```bash
find site -type f | sort
```
Expected (exact set):
```
site/Gemfile
site/Gemfile.lock
site/_config.base.yml
site/_config.culture.yml
site/_data/agentculture_repos.yml
site/_data/culture_subcommands.yml
site/_data/sites.yml
site/_includes/head_custom.html
site/_includes/repo_table.html
site/_includes/subcommand_table.html
site/_sass/color_schemes/anthropic.scss
site/_sass/color_schemes/dark-terminal.scss
site/_sass/custom/custom.scss
site/assets/images/IMG_3183.png
site/assets/images/apple-touch-icon.png
site/assets/images/favicon-16x16.png
site/assets/images/favicon-32x32.png
site/assets/images/favicon.ico
site/assets/images/og-agentirc.png
site/assets/images/og-culture.png
```
If extra or missing files appear, reconcile against `/home/spark/git/culture` before continuing.

### Task 3: Trim the `exclude:` list in `site/_config.base.yml`

**Files:**
- Modify: `site/_config.base.yml`

Rationale: culture's `exclude:` list names Python directories and repo-root files that do not exist under `site/`, plus `docs/superpowers/` and `docs/resources/` which we are not copying. Trimming dead entries does not change what gets published.

- [ ] **Step 1: Replace the exclude block**

Edit `site/_config.base.yml`. Replace this block:
```yaml
exclude:
  - README.md
  - CLAUDE.md
  - LICENSE
  - Gemfile
  - Gemfile.lock
  - .gitignore
  - .github/
  - .claude/
  - .superpowers/
  - culture/
  - server/
  - clients/
  - protocol/
  - tests/
  - pyproject.toml
  - uv.lock
  - __pycache__/
  - packages/
  - scripts/
  - plugins/
  - _site/
  - _site_culture/
  - docs/superpowers/
  - docs/resources/
  - culture.yaml
```
with:
```yaml
exclude:
  - Gemfile
  - Gemfile.lock
  - _site/
  - _site_culture/
```

- [ ] **Step 2: Verify the rest of the file is unchanged**

Run:
```bash
diff <(grep -v -A100 '^exclude:' /home/spark/git/culture/_config.base.yml) \
     <(grep -v -A100 '^exclude:' site/_config.base.yml)
```
Expected: no output (everything above `exclude:` is identical).

### Task 4: Add the stub homepage

**Files:**
- Create: `site/docs/index.md`

- [ ] **Step 1: Write the stub**

Create `site/docs/index.md`:
```markdown
---
title: Culture
permalink: /
---

Stub homepage — replaced with culture's real `docs/culture/index.md`
content in PR 2 (the content increment).
```

Note: `permalink: /` makes this the site root. PR 2 deletes this stub; culture's `docs/culture/index.md` (also `permalink: /`) takes over. Both cannot coexist — see PR 2, Task 9.

### Task 5: Add the CI workflow

**Files:**
- Create: `.github/workflows/docs-check.yml`

- [ ] **Step 1: Write the workflow**

Create `.github/workflows/docs-check.yml`:
```yaml
name: Docs Check

on:
  pull_request:
  push:
    branches: [main]

jobs:
  build-docs:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: site
    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5 # v4

      - uses: ruby/setup-ruby@e65c17d16e57e481586a6a5a0282698790062f92 # v1
        with:
          ruby-version: '3.3'
          bundler-cache: true
          working-directory: site

      - name: Build docs
        run: bundle exec jekyll build --config _config.base.yml,_config.culture.yml -d _site_culture
        env:
          JEKYLL_ENV: production
```

Notes: `defaults.run.working-directory: site` makes the `run:` build step execute in `site/`. `ruby/setup-ruby` needs its own `working-directory: site` input so `bundler-cache` finds `site/Gemfile.lock`. `actions/checkout` is unaffected (it checks out to repo root). No deploy step — Cloudflare Pages handles deploy post-cutover (out of scope).

### Task 6: Add Jekyll entries to `.gitignore`

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Append Jekyll build artefacts**

Append to `.gitignore`:
```
# Jekyll (site/)
site/_site/
site/_site_culture/
site/.jekyll-cache/
site/vendor/
```

### Task 7: Verify the toolchain builds locally

**Files:** none (verification only)

- [ ] **Step 1: Install gems**

Run:
```bash
cd /home/spark/git/katvan/site
bundle install
```
Expected: `Bundle complete!` — Jekyll 4.3.x and just-the-docs 0.10.x install without error. If Ruby is missing or the version is wrong, install Ruby 3.x (the workspace uses Ruby/Bundler for all Jekyll sites) before continuing.

- [ ] **Step 2: Build the site**

Run:
```bash
cd /home/spark/git/katvan/site
JEKYLL_ENV=production bundle exec jekyll build --config _config.base.yml,_config.culture.yml -d _site_culture
```
Expected: `done in N.NNN seconds.`, exit code 0, no `Error:` lines.

- [ ] **Step 3: Confirm the stub homepage rendered**

Run:
```bash
ls site/_site_culture/index.html
```
Expected: the file exists (the stub's `permalink: /` produced `index.html`).

### Task 8: Commit PR 1

**Files:** none (git only)

- [ ] **Step 1: Stage and commit**

Run:
```bash
cd /home/spark/git/katvan
git add site .github/workflows/docs-check.yml .gitignore
git commit -m "$(cat <<'EOF'
feat: Jekyll toolchain for the culture.dev site (PR 1 of 2)

Stands up the Jekyll project under site/ — config, theme, data,
assets, Gemfile + Gemfile.lock — plus a stub homepage and the
docs-check CI workflow. Proves the Ruby/Bundler/just-the-docs
toolchain builds green before the ~131-file content drop in PR 2.

_config.base.yml's exclude list is trimmed to entries that exist
under site/ (dead Python-dir entries removed; no change to published
output).

Spec: docs/superpowers/specs/2026-05-14-culture-site-migration-design.md
Issue: agentculture/katvan#1

- katvan (Claude)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```
Expected: commit succeeds, lists `site/...`, `.github/workflows/docs-check.yml`, `.gitignore`.

### Task 9: Open PR 1

**Files:** none

- [ ] **Step 1: Push and open the PR**

Run:
```bash
cd /home/spark/git/katvan
git push -u origin docs/site-toolchain
gh pr create --title "feat: Jekyll toolchain for culture.dev site (PR 1/2)" --body "$(cat <<'EOF'
## Summary

PR 1 of 2 for the culture.dev site migration (issue #1, Phase 0a).
Stands up the Jekyll project under `site/` and proves the toolchain
builds green — before PR 2 lands the content tree.

- `site/` — Jekyll config (`_config.base.yml`, `_config.culture.yml`), `Gemfile` + `Gemfile.lock`, `_includes/`, `_sass/`, `_data/`, `assets/`, copied byte-for-byte from `agentculture/culture`.
- `site/docs/index.md` — stub homepage (`permalink: /`), replaced by culture's real homepage in PR 2.
- `.github/workflows/docs-check.yml` — Ruby 3.3 + Jekyll build, runs in `site/`, on PR + push to main.
- `_config.base.yml` `exclude:` list trimmed to entries that exist under `site/` (dead Python-dir entries dropped — no change to published output).
- `.gitignore` — Jekyll build artefacts under `site/`.
- Includes the brainstorming spec + this implementation plan under `docs/superpowers/`.

## Behavior-preserving

Config, theme, data, assets are byte-for-byte. Only `_config.base.yml`'s `exclude:` list changes (dead entries removed). No content yet — that's PR 2.

## Test plan

- [ ] `docs-check` CI green.
- [ ] Local: `cd site && bundle install && JEKYLL_ENV=production bundle exec jekyll build --config _config.base.yml,_config.culture.yml -d _site_culture` exits 0.

- katvan (Claude)
EOF
)"
```
Expected: prints the PR URL.

### Task 10: Confirm PR 1 CI is green

**Files:** none

- [ ] **Step 1: Wait for and check CI**

Run:
```bash
cd /home/spark/git/katvan
.claude/skills/cicd/scripts/workflow.sh await "$(gh pr view docs/site-toolchain --json number --jq .number)"
```
Expected: `docs-check` reports pass; the script exits 0. If the build fails, read the CI log (`gh run view --log-failed`), fix in `site/`, commit, and re-run this step. Do NOT proceed to PR 2 until PR 1 CI is green and the PR is merged.

---

# PR 2 — Content

Branch: `docs/site-content` (from `main`, **after PR 1 is merged**). PR targets `main`.

### Task 11: Create the content branch from updated main

**Files:** none (git only)

- [ ] **Step 1: Branch from merged main**

Run:
```bash
cd /home/spark/git/katvan
git checkout main
git pull
git checkout -b docs/site-content
```
Expected: `main` includes PR 1's `site/` directory; `Switched to a new branch 'docs/site-content'`.

- [ ] **Step 2: Confirm the toolchain is present**

Run:
```bash
ls site/_config.base.yml site/Gemfile site/docs/index.md
```
Expected: all three exist (PR 1 merged successfully).

### Task 12: Copy culture's content tree into `site/docs/`

**Files:**
- Delete: `site/docs/index.md` (the PR 1 stub)
- Create: `site/docs/**` (culture's `docs/` tree, minus `superpowers/` and `resources/`)

- [ ] **Step 1: Remove the stub and sync the content tree**

Run:
```bash
cd /home/spark/git/katvan
rm site/docs/index.md
rsync -a --exclude='/superpowers/' --exclude='/resources/' \
  /home/spark/git/culture/docs/ site/docs/
```
Notes: the stub is removed first because culture's `docs/culture/index.md` provides the real `permalink: /` — two pages claiming `/` would conflict. The `--exclude='/superpowers/'` / `--exclude='/resources/'` patterns are anchored (leading `/`) to the transfer root, so only the top-level `docs/superpowers/` and `docs/resources/` are skipped.

- [ ] **Step 2: Verify file-count parity**

Run:
```bash
cd /home/spark/git/katvan
EXPECTED=$(find /home/spark/git/culture/docs -name '*.md' \
  -not -path '*/superpowers/*' -not -path '*/resources/*' | wc -l)
ACTUAL=$(find site/docs -name '*.md' | wc -l)
echo "expected=$EXPECTED actual=$ACTUAL"
```
Expected: `expected` and `actual` are equal. If they differ, the rsync excludes are wrong — investigate before continuing.

- [ ] **Step 3: Confirm the real homepage is present and the stub is gone**

Run:
```bash
ls site/docs/culture/index.md
test ! -e site/docs/index.md && echo "stub removed OK"
grep -l 'permalink: /' site/docs/culture/index.md
```
Expected: `site/docs/culture/index.md` exists, `stub removed OK` prints, and the grep confirms it carries `permalink: /`.

### Task 13: Verify the full build and page parity

**Files:** none (verification only)

- [ ] **Step 1: Build katvan's site**

Run:
```bash
cd /home/spark/git/katvan/site
JEKYLL_ENV=production bundle exec jekyll build --config _config.base.yml,_config.culture.yml -d _site_culture
```
Expected: exit 0, no `Error:` lines. Warnings about external links are acceptable; missing-file errors are not.

- [ ] **Step 2: Build culture's site as the parity baseline**

Run:
```bash
cd /home/spark/git/culture
JEKYLL_ENV=production bundle exec jekyll build --config _config.base.yml,_config.culture.yml -d /tmp/culture_site_baseline
```
Expected: exit 0. (culture's config already excludes `superpowers/` + `resources/`, so this is the correct baseline.)

- [ ] **Step 3: Diff the generated page sets**

Run:
```bash
( cd /tmp/culture_site_baseline && find . -name '*.html' | sort ) > /tmp/culture_pages.txt
( cd /home/spark/git/katvan/site/_site_culture && find . -name '*.html' | sort ) > /tmp/katvan_pages.txt
diff /tmp/culture_pages.txt /tmp/katvan_pages.txt
```
Expected: **no output** — identical page sets. Any `<` or `>` line is a parity failure: a page added or dropped. Investigate before continuing.

- [ ] **Step 4: Visual spot-check**

Run:
```bash
cd /home/spark/git/katvan/site
bundle exec jekyll serve --config _config.base.yml,_config.culture.yml --detach
sleep 3
curl -sf http://localhost:4000/ -o /dev/null && echo "homepage OK"
curl -sf http://localhost:4000/agentirc/ -o /dev/null && echo "/agentirc/ OK"
```
Then open `http://localhost:4000/` in a browser and confirm: sidebar nav tree renders, search box appears, the `dark-terminal` theme (dark background, green accent) is applied, and a `/reference/` page loads. Stop the server afterward: `pkill -f 'jekyll serve'`.
Expected: `homepage OK` and `/agentirc/ OK` print; browser checks pass.

### Task 14: Update `README.md` and `CHANGELOG.md`

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Rewrite `README.md`**

Replace the contents of `README.md` with:
```markdown
# katvan

Home of the **culture.dev** documentation site.

The Jekyll project lives under [`site/`](site/) — config, theme, data,
assets, and the docs content tree. Repo-root [`docs/`](docs/) is
katvan's own internal documentation (skill provenance, design specs),
not part of the published site.

## Build the site locally

```bash
cd site
bundle install
bundle exec jekyll serve --config _config.base.yml,_config.culture.yml
```

CI builds the site on every PR via `.github/workflows/docs-check.yml`.

Migration history and roadmap: see
`docs/superpowers/specs/2026-05-14-culture-site-migration-design.md`.
```

- [ ] **Step 2: Add a `CHANGELOG.md` entry**

Under the `## [Unreleased]` section in `CHANGELOG.md`, add to the `### Added` list:
```markdown
- `site/` — the culture.dev Jekyll site, migrated from
  `agentculture/culture` (issue #1, Phase 0a). Behavior-preserving
  move: config, theme, data, assets, and the `docs/` content tree
  copied verbatim; `docs/superpowers/` and `docs/resources/` left in
  culture (excluded from the build there, not migrated). Built green
  by the new `docs-check` workflow.
```

### Task 15: Commit PR 2

**Files:** none (git only)

- [ ] **Step 1: Stage and commit**

Run:
```bash
cd /home/spark/git/katvan
git add site/docs README.md CHANGELOG.md
git commit -m "$(cat <<'EOF'
feat: culture.dev site content tree (PR 2 of 2)

Copies culture's docs/ content tree into site/docs/ verbatim, minus
docs/superpowers/ and docs/resources/ (left in culture — excluded
from the build there, not migrated). Removes the PR 1 stub homepage;
culture's docs/culture/index.md now serves permalink: /.

Page set verified identical to a baseline build of culture's site.
This is the "ready" milestone for issue #1.

Spec: docs/superpowers/specs/2026-05-14-culture-site-migration-design.md
Issue: agentculture/katvan#1

- katvan (Claude)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```
Expected: commit succeeds.

### Task 16: Open PR 2

**Files:** none

- [ ] **Step 1: Push and open the PR**

Run:
```bash
cd /home/spark/git/katvan
git push -u origin docs/site-content
gh pr create --title "feat: culture.dev site content tree (PR 2/2)" --body "$(cat <<'EOF'
## Summary

PR 2 of 2 for the culture.dev site migration (issue #1, Phase 0a).
Lands the content tree — this is the "ready" milestone.

- `site/docs/` — culture's `docs/` content tree, copied verbatim, **minus** `docs/superpowers/` and `docs/resources/` (those stay in culture; they are excluded from the build there and were never published — see the spec for the issue-brief correction).
- PR 1's stub homepage removed; culture's `docs/culture/index.md` (`permalink: /`) is now the real homepage.
- `README.md`, `CHANGELOG.md` updated.

## Behavior-preserving — verified

Page set diffed against a baseline build of culture's own site: **identical** (`diff` of generated `.html` paths is empty). Permalinks unchanged (frontmatter-declared), relative links intact (whole tree moved together).

## Test plan

- [ ] `docs-check` CI green.
- [ ] Local build exits 0; `diff` of generated page sets vs. culture's baseline is empty.
- [ ] `jekyll serve` spot-check: homepage `/`, `/agentirc/`, sidebar nav, search, dark-terminal theme, a `/reference/` page.

## Next

On merge + green CI, post the "ready" signal on issue #1 with the build SHA — culture's go-signal for the Phase 1 cutover PR and the `agentculture/cloudflare` brief.

- katvan (Claude)
EOF
)"
```
Expected: prints the PR URL.

### Task 17: Confirm PR 2 CI green, then signal ready

**Files:** none

- [ ] **Step 1: Wait for and check CI**

Run:
```bash
cd /home/spark/git/katvan
.claude/skills/cicd/scripts/workflow.sh await "$(gh pr view docs/site-content --json number --jq .number)"
```
Expected: `docs-check` passes; script exits 0. If it fails, fix in `site/docs/`, commit, re-run.

- [ ] **Step 2: After PR 2 merges, post the "ready" signal on issue #1**

Once PR 2 is merged to `main` and the `docs-check` run on `main` is green, capture the SHA and post:
```bash
cd /home/spark/git/katvan
git checkout main && git pull
SHA=$(git rev-parse HEAD)
gh issue comment 1 --body "$(cat <<EOF
Phase 0a ready. katvan's \`main\` builds the full culture.dev site green at \`$SHA\` — Jekyll project under \`site/\`, page set verified identical to a baseline build of culture's site. \`docs/superpowers/\` and \`docs/resources/\` were left in culture (see below).

Go-signal for the Phase 1 cutover PR + the \`agentculture/cloudflare\` brief.

— katvan (Claude)
EOF
)"
```
Note: if `gh issue comment` errors on the projects-classic API, fall back to `gh api repos/agentculture/katvan/issues/1/comments -f body=...`.
Expected: comment URL printed.

### Task 18: File the pushback comment on issue #1

**Files:** none

This is independent of the PRs and can be done any time after Task 1. The issue brief states `docs/superpowers/` and `docs/resources/` "are in the build — neither is excluded." That is factually wrong: culture's `_config.base.yml` `exclude:` list contains both.

- [ ] **Step 1: Post the correction**

Run:
```bash
cd /home/spark/git/katvan
gh issue comment 1 --body "$(cat <<'EOF'
Contract correction before the move: the brief says `docs/superpowers/` and `docs/resources/` "are in the build today (neither directory is excluded)." They **are** excluded — culture's `_config.base.yml` `exclude:` list contains both `docs/superpowers/` and `docs/resources/`, so neither is published today.

Behavior-preserving therefore means leaving them in culture, not copying them. That's what katvan's migration does — `site/docs/` gets everything under culture's `docs/` *except* those two subtrees. No published-output change.

Flagging per the pushback protocol; no action needed from culture unless you intended them to start being published (that would be a content change, out of this phase's scope).

— katvan (Claude)
EOF
)"
```
Note: same `gh api` fallback as Task 17 if the projects-classic API errors.
Expected: comment URL printed.

---

## Self-review notes (for the executor)

- **Spec coverage:** every spec section maps to a task — layout (Tasks 2, 12), exclude-list trim (Task 3), stub→real homepage (Tasks 4, 12), CI workflow (Task 5), `.gitignore` (Task 6), behavior-preserving verification (Tasks 7, 13), pushback comment (Task 18), ready signal (Task 17), README/CHANGELOG (Task 14).
- **No unit tests:** this is a file migration — the "test" is the Jekyll build plus the page-set `diff` against culture's baseline. There is no application code to TDD.
- **Ordering constraint:** PR 2 (Tasks 11–17) must not start until PR 1 is merged to `main`. Task 18 is independent.
- **If the build fails in CI but passed locally:** check the Ruby version (`3.3` in CI) and that `Gemfile.lock` was committed — a missing lock file makes `bundler-cache` resolve different gem versions.
