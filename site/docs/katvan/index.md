---
title: katvan
parent: Resident Culture
nav_order: 5
permalink: /katvan/
sites: [culture]
---

# katvan

**What it is.** The maintainer of culture.dev — surveys, pulls, and
doctors sibling-repo docs from a single workstation.

**Why you'd reach for it.** Every sibling repo ships its own docs, and
someone has to keep the umbrella site in sync without hand-copying
markdown. `katvan overview` reports which repos are fresh, `katvan pull`
syncs reference content via the sibling's AFI binary, and `katvan
doctor` fails CI when a registered repo is missing its page. Runs as a
CLI; also drives the docs-check workflow.

**Where it sits.** *Resident Culture.* The site's resident docs agent.
Related: [steward](/steward/), [cultureflare](/cultureflare/).

[Reference →](reference/)
