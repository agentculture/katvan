# Google Search Console integration

**Status:** approved (brainstorm), pending implementation plan
**Issue:** [agentculture/katvan#26](https://github.com/agentculture/katvan/issues/26)
**Date:** 2026-05-18

## Goal

Verify the `culture.dev` site with Google Search Console (GSC) and expose
GSC's indexing-health data as a `katvan gsc` CLI verb so agents can read
indexing issues directly instead of going through the GSC web UI.

## Scope

In scope:

- One-time site verification of `https://culture.dev/` as a URL-prefix
  property, via Jekyll meta tag.
- A read-only `katvan gsc` verb namespace with three subcommands:
  `sitemaps`, `inspect`, `doctor`.
- Service-account authentication, configured via environment variables.
- Unit tests with mocked GSC responses.
- Setup docs for the one-time human steps.

Out of scope (explicit non-goals for v1):

- Search Analytics endpoint (impressions, clicks, queries). The verb
  namespace leaves room for a future `katvan gsc traffic`.
- Auto-filing GitHub issues when GSC reports problems. A future
  scheduled job could call `katvan gsc doctor` and open issues; not now.
- Bulk URL-inspection state caching / `--since` flag. The site is small
  enough that re-inspecting from scratch is fine.
- Write operations against GSC (submitting sitemaps, requesting indexing).
  Scope stays read-only.

## Site verification

Replace the commented stub at `site/_config.culture.yml:31`:

```yaml
# Uncomment after registering at https://search.google.com/search-console
# google_site_verification: "YOUR_CODE_HERE"
```

with the real verification code emitted by GSC. Property type:
**URL-prefix** for `https://culture.dev/`. Single-host site, so this
covers everything served from that origin and avoids the DNS TXT
configuration a Domain property would require.

If the Jekyll theme in use does not natively emit a
`google-site-verification` meta tag from this config key, add one in
`site/_includes/head_custom.html` (or the equivalent customization
slot for the theme). The implementation plan resolves which.

## CLI surface

New top-level verb namespace, alongside the existing `learn` and
`explain` verbs:

```
katvan gsc sitemaps           [--json]
katvan gsc inspect <url>      [--json]
katvan gsc doctor             [--json]
```

Default output is human-readable text/table. `--json` returns a
normalized JSON struct suitable for agent consumption.

### `katvan gsc sitemaps`

- Calls `webmasters.sitemaps.list(siteUrl=$KATVAN_GSC_SITE)`.
- One row per submitted sitemap: path, `lastSubmitted`, `lastDownloaded`,
  `isPending`, `errors`, `warnings`, and per-content-type submitted /
  indexed counts.
- Exit code `0` always — this is a status read; errors in the sitemaps
  themselves are data, not CLI failures.
- `--json` emits the normalized `sitemaps[]` array (ISO timestamps,
  ints for numeric fields).

### `katvan gsc inspect <url>`

- Calls `urlInspection.index.inspect` with `inspectionUrl=<url>` and
  `siteUrl=$KATVAN_GSC_SITE`.
- Validates `<url>` is under `$KATVAN_GSC_SITE` before calling — cheap
  pre-flight failure for typos.
- Extracts the interesting fields from the response:
  `indexStatusResult.verdict`, `coverageState`, `lastCrawlTime`,
  `robotsTxtState`, `pageFetchState`, `googleCanonical`, `userCanonical`,
  plus `mobileUsabilityResult.verdict` and `richResultsResult.verdict`
  when present.
- `--json` returns the normalized struct.

### `katvan gsc doctor`

- HTTP-fetches `$KATVAN_GSC_SITE.rstrip('/') + '/sitemap.xml'`, parses,
  collects every `<loc>`. If the top-level document is a sitemap index,
  descend one level. Jekyll's plugin emits a flat sitemap today, but
  the parser handles both shapes.
- Inspects each URL serially. No concurrency in v1 — keeps us comfortably
  under per-minute and per-day GSC quotas for a sub-100-URL site.
- Groups results by problem class:
  - `not_indexed` — `verdict ≠ PASS`
  - `crawl_errors` — `pageFetchState ≠ SUCCESSFUL`
  - `mobile_issues` — `mobileUsabilityResult.verdict ≠ PASS`
  - `canonical_mismatch` — `googleCanonical ≠ userCanonical`
- Default output: markdown-shaped text report (agent can paste into an
  issue verbatim).
- `--json` returns full per-URL inspection structs keyed by URL plus a
  `summary` block with per-class counts.
- Exit code: `0` if every URL is `PASS`, `1` if any URL has a problem.
  Lets a future cron / CI loop detect "something to do" without parsing
  output.

## Auth & configuration

**Method:** Google Cloud service account with the
`https://www.googleapis.com/auth/webmasters.readonly` scope.

**Environment variables:**

| Var | Required | Default | Purpose |
|---|---|---|---|
| `KATVAN_GSC_CREDENTIALS` | yes | — | Absolute path to SA JSON key |
| `KATVAN_GSC_SITE` | no | `https://culture.dev/` | Verified property URL |

No CLI flags for credentials or site — env-only. Keeps verb signatures
clean and matches how an agent will invoke them.

Missing or unreadable `KATVAN_GSC_CREDENTIALS` produces a clear error
pointing at the setup docs. No silent fallback to ADC.

**One-time human setup** (documented in `docs/gsc-setup.md`, not
automated):

1. Create or reuse a Google Cloud project.
2. Enable the Search Console API in that project.
3. Create a service account, download its JSON key.
4. In GSC, add the service account's email as a user on the
   `https://culture.dev/` property (Viewer is sufficient).
5. Set `KATVAN_GSC_CREDENTIALS` to the key path.

## Code layout

```
katvan/
  cli/
    _commands/
      gsc.py           # argparse wiring for the gsc verb + subcommands
  gsc/
    __init__.py        # public surface used by cli/_commands/gsc.py
    client.py          # SA auth + thin GSC API client wrapper
    sitemaps.py        # sitemaps subcommand logic
    inspect.py         # inspect subcommand logic
    doctor.py          # doctor composite
    formatters.py      # text + JSON output helpers
```

The `katvan/gsc/` package is parallel to existing `katvan/explain/`.
CLI wiring lives in `katvan/cli/_commands/gsc.py` alongside the other
verbs, using argparse (matching the existing pattern in that directory).
`gsc` is the first verb with subcommands; the file uses
`argparse`'s subparsers to wire `sitemaps`, `inspect`, and `doctor`
under a single verb.

**Naming note.** `katvan gsc doctor` shares the word "doctor" with the
existing top-level `katvan doctor` (sibling-repo doc defects). The two
have parallel semantics — "scan for problems and report" — but operate
on disjoint targets. Treating this as a feature, not a collision.

**New dependencies** (added to `pyproject.toml`):

- `google-api-python-client`
- `google-auth`

Sitemap fetch reuses whichever HTTP client the codebase already
uses (the implementation plan picks the exact import).

**Client wrapper retry policy:**

- Retries 5xx and 429 with exponential backoff, 3 attempts.
- 401 / 403 bubble up immediately with a message instructing the user
  to check the SA grant on the GSC property.
- Quota exhaustion mid-`doctor` → partial report, exit code `1`, error
  block in the output listing remaining un-inspected URLs.

## Testing

- Unit tests per subcommand, mocked at the `googleapiclient` Resource
  layer (`MagicMock`). No live API calls in tests, ever.
- JSON response fixtures under `tests/fixtures/gsc/`:
  - `sitemaps-list.json`
  - `url-inspection-pass.json`
  - `url-inspection-not-indexed.json`
  - `url-inspection-crawl-error.json`
- `doctor` tests use a fake sitemap.xml fixture and parameterize over
  "all pass → exit 0" vs "one URL fails → exit 1" vs "sitemap index →
  descend one level".
- One auth test: `client.build_client()` raises a clear error when
  `KATVAN_GSC_CREDENTIALS` is unset. No test exercises real credential
  loading; CI never sees an SA key.

## Documentation

Two doc updates:

- `README.md` — add `gsc` to the verbs list, link to the setup guide.
- `docs/gsc-setup.md` (new, repo-root `docs/`, **not** the published
  site) — text-only walkthrough of the one-time human setup listed
  above. Text only; screenshots of the GSC UI rot too quickly to be
  worth maintaining.

## Risks & open questions resolved during brainstorm

- **Theme verification-tag emission.** Whether the current Jekyll theme
  auto-emits a `google-site-verification` meta tag from the config key
  is unverified. Fallback: add the meta tag manually in
  `_includes/head_custom.html`. Implementation plan picks the path
  after checking the theme.
- **Sitemap index vs flat sitemap.** Jekyll emits flat today, but the
  parser is written to descend one level so a future switch doesn't
  break `doctor`.
- **Quota.** GSC URL Inspection API allows ~2000 calls/day. Today's
  `culture.dev` sitemap is well under 100 URLs, so a daily `doctor` run
  uses <5% of quota.
