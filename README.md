# katvan

Home of the **culture.dev** documentation site, and the `katvan` CLI that
maintains it.

The Jekyll project lives under [`site/`](site/) — config, theme, data,
assets, and the docs content tree. Repo-root [`docs/`](docs/) is
katvan's own internal documentation (skill provenance, design specs),
not part of the published site.

## The `katvan` CLI

`katvan` is a Python CLI that maintains the docs of sibling AgentCulture
repos under one roof on the culture.dev site — surveying which siblings
are synced and fresh, pulling their raw-markdown `docs/` trees into
`site/docs/<repo>/` with Jekyll frontmatter injected, and diagnosing doc
defects. It is the `librarian` skill's logic, migrating into a real
installable CLI.

```bash
uv tool install katvan
```

Verbs available today:

- `katvan learn` — structured self-teaching prompt for agent consumers
  (supports `--json`).
- `katvan explain <path>` — markdown docs for any noun/verb path
  (supports `--json`).

The docs verbs — `overview`, `pull`, and `doctor` — land in a later
release, ported from the `librarian` skill.

## Build the site locally

```bash
cd site
bundle install
bundle exec jekyll serve --config _config.base.yml,_config.culture.yml
```

CI builds the site on every PR via `.github/workflows/docs-check.yml`.

Migration design and implementation plan:
`docs/superpowers/specs/2026-05-14-culture-site-migration-design.md`
and `docs/superpowers/plans/2026-05-14-culture-site-migration.md`.
