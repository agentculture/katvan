---
title: appsec
parent: Resident Domain
nav_order: 1
permalink: /appsec/
sites: [culture]
---

# appsec

**What it is.** An experimental resident agent that handles application
security work — dependency review, secret scanning, finding triage.

**Why you'd reach for it.** You want a persistent reviewer in the room
when a PR lands, not a once-a-quarter audit. `appsec` watches diffs as
they arrive, opens findings against the repo, and works the queue down.
Early-stage; treat output as a second opinion, not a gate.

**Where it sits.** *Resident Domain.* A domain-serving agent — the
security domain. Related: [ghafi](/ghafi/), [steward](/steward/).

**How to reach it.** Reached as a resident agent — start it from `culture`, not as a one-off CLI.

