---
title: afi-cli
parent: Workspace Experience
nav_order: 2
permalink: /afi-cli/
---

# afi-cli

**What it is.** The Agent-First Interface — the contract a CLI publishes
about itself so agents can read it without scraping `--help` text.

**Why you'd reach for it.** You're building a tool that agents will call,
and you want them to learn it the same way they learn every other
AFI-compatible binary: `learn --json`, `explain --json`. `afi-cli` ships
the contract, validates it, and gives you a working harness to attach.
Today it's exposed inside `culture` as `culture afi`; a `culture contract`
alias is planned.

**Where it sits.** *Workspace Experience.* The contract layer the lens
tools read from. Related: [culture](/culture/), [code-lens-cli](/code-lens-cli/).

[Reference →](reference/)
