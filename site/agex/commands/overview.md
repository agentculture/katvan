---
title: overview
parent: Commands
nav_order: 60
sites: [culture]
permalink: /agex/commands/overview/
---

# `agex overview --agent <backend>`

Call this to get a read-only markdown snapshot of what's configured in the
current project for a given backend — skills, hooks, agents, MCP servers,
and relevant config files. Descriptive, not diagnostic. Read it before you
act.

## From your shell tool

```bash
agex overview --agent claude-code
agex overview --agent codex
```

## What you get

Markdown sections: Project root, `CLAUDE.md`/`AGENTS.md` presence, Skills,
Hooks, MCP servers, Settings.

## Notes

- Malformed files are skipped with a `> ⚠️` inline warning.
- Read-only except first-run `.agex/` init.
- Build diagnostic logic (gaps, recommendations) into an agent-authored skill:
  `agex learn introspect --agent <backend>`.
