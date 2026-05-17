---
title: tipalti
parent: Resident Domain
nav_order: 4
permalink: /tipalti/
sites: [culture]
---

# tipalti

**What it is.** An experimental integration agent that wraps the Tipalti
payables API for use from the Culture mesh.

**Why you'd reach for it.** Finance ops needs an agent that can read
Tipalti invoice state, post a status into a channel, and file the
follow-up tasks without anyone clicking through the vendor UI. `tipalti`
is the worked example of an external-service-serving agent: one
integration, one room, scoped credentials via `shushu`. Early-stage;
read-only by default.

**Where it sits.** *Resident Domain.* A domain-serving agent — the
external-finance-API domain. Related: [shushu](/shushu/),
[office-agent](/office-agent/).

[Reference →](reference/)
