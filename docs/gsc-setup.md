# Google Search Console setup

One-time human steps to enable `katvan gsc` against the live `culture.dev`
property. Re-run only if the service account is rotated or the property is
re-created.

## Prerequisites

- Owner-level access to the GSC property `https://culture.dev/` (or
  rights to be added as a user).
- A Google Cloud project where a service account can be created. A
  brand-new project works fine; we use this for no other API.

## Steps

### 1. Verify the site with Google Search Console

1. Go to https://search.google.com/search-console.
2. Add a property of type **URL prefix**: `https://culture.dev/`.
3. Choose the **HTML tag** verification method. Copy the `content="..."`
   value (the verification code).
4. In this repo, edit `site/_config.culture.yml`, uncomment the
   `google_site_verification` line, and set it to your verification
   code.
5. Commit, merge, and let CI publish the site. Once live, return to
   GSC and click **Verify**.

### 2. Enable the Search Console API

1. Open https://console.cloud.google.com and select (or create) a
   project.
2. Navigate to **APIs & Services → Library**.
3. Find **Google Search Console API** and click **Enable**.

### 3. Create a service account

1. **APIs & Services → Credentials → Create credentials → Service account**.
2. Give it a descriptive name (e.g. `katvan-gsc-reader`). No project-level
   roles are required.
3. After creation, click into the account → **Keys → Add key → Create new
   key → JSON**. Save the JSON file somewhere private.

### 4. Grant the service account on the GSC property

1. Back in https://search.google.com/search-console, select the
   `https://culture.dev/` property.
2. **Settings → Users and permissions → Add user**.
3. Paste the service account's email (looks like
   `katvan-gsc-reader@<project>.iam.gserviceaccount.com`).
4. Permission: **Restricted** (read-only is sufficient for our scope).

### 5. Configure the CLI

Export the credential path in whichever shell or service runs `katvan`:

```sh
export KATVAN_GSC_CREDENTIALS=/absolute/path/to/sa.json
```

Optionally override the site URL for testing against a staging property:

```sh
export KATVAN_GSC_SITE=https://staging.example.com/
```

Default is `https://culture.dev/`.

### 6. Smoke test

```sh
katvan gsc sitemaps
```

Expected: a row per submitted sitemap with last-download timestamps and
error / warning counts. If `errors=0 warnings=0`, indexing health is
nominal.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `error: KATVAN_GSC_CREDENTIALS env var is not set` | Step 5 not run in this shell. |
| `error: KATVAN_GSC_CREDENTIALS file not found: ...` | Path typo or the key was moved. |
| HTTP 403 from any subcommand | Step 4 was skipped, or the SA email was added to the wrong property. |
| HTTP 401 | The key has been disabled or the project's API is disabled. |
| `katvan gsc doctor` reports `crawl_errors` | Investigate via `katvan gsc inspect <url>` — usually 5xx from the live site. |
