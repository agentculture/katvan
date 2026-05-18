---
title: code-lens-cli
parent: Workspace Experience
nav_order: 5
permalink: /code-lens-cli/
sites: [culture]
---

# code-lens-cli

**What it is.** A Lens CLI for reading code quickly — symbol search,
structural views, summaries — built on `afi-cli` and `kata-cli`.

**Why you'd reach for it.** Your agent is staring at a 200k-line repo and
about to grep its way through. `code-lens` returns a structural read in
one call: entry points, public API, related files, recent churn. Faster
than ripgrep, narrower than reading the whole tree.

**Where it sits.** *Workspace Experience.* The read-side companion to the
afi contract. Related: [afi-cli](/afi-cli/), [irc-lens](/irc-lens/).

**How to reach it.** Direct entry point — agents call it from the command line like ripgrep.

[Reference →](/docs/code-lens-cli/reference/)
