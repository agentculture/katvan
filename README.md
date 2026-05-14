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

Migration design and implementation plan:
`docs/superpowers/specs/2026-05-14-culture-site-migration-design.md`
and `docs/superpowers/plans/2026-05-14-culture-site-migration.md`.
