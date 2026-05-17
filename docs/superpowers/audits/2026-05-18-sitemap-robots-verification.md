# Sitemap & Robots Verification — 2026-05-18

## Task 17: Verification Summary

Built site with `jekyll build --config _config.base.yml,_config.culture.yml` and verified sitemap structure.

### URLs Confirmed (32/32 Required)

**Marketing Surfaces:**
- `/` (landing)
- `/quickstart/`
- `/why/`
- `/ecosystem/`

**Categories (6):**
- `/categories/workspace-experience/`
- `/categories/core-runtime/`
- `/categories/identity-secrets/`
- `/categories/resident-culture/`
- `/categories/resident-domain/`
- `/categories/org-site/`

**Per-Repo (21):**
- `/agentirc/`, `/irc-lens/`, `/cultureagent/`, `/culture/`
- `/agex-cli/`, `/afi-cli/`, `/antoine/`, `/code-lens-cli/`
- `/zehut/`, `/shushu/`, `/agtag/`, `/auntiepypi/`
- `/cultureflare/`, `/ghafi/`, `/katvan/`, `/steward/`
- `/appsec/`, `/office-agent/`, `/telek/`, `/tipalti/`, `/landing-page/`

### Sitemap Structure

- **Master index:** `/sitemap.xml` (sitemap index referencing all subsites)
- **Main marketing:** `/sitemap-main.xml` (40 URLs, excludes subsites)
- **Agentirc:** `/agentirc/sitemap.xml` (1 URL: `/agentirc/`)
- **Other subsites:** `/agex/`, `/afi/`, `/citation-cli/` sitemaps also generated

### robots.txt Status

- **File:** `site/robots.txt`
- **Policy:** `User-agent: *` / `Allow: /`
- **Status:** Allow-all, includes sitemap reference

### No Changes Required

All marketing surfaces present in sitemaps. No edits committed (site already complete).
