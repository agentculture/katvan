---
title: gamify
parent: Commands
nav_order: 30
sites: [culture]
permalink: /agex/commands/gamify/
---

# `agex gamify --agent <backend>` / `agex gamify --uninstall --agent <backend>`

## What it does

Writes backend-native hook fragments (each tagged with a stable `agex:*` ID) that call `agex hook write <event>` on PostToolUse, UserPromptSubmit, and Stop events. Agent-authored skills (e.g., `levelup`) read the accumulated data via `agex hook read`.

## Why it's safe

- Idempotent: re-running is a no-op.
- Reversible: `--uninstall` removes exactly the `agex:*` fragments; user-authored hooks are untouched.
- Calling `agex gamify` explicitly is the confirmation — no separate prompt.

## Unsupported backends

If your backend doesn't support hooks, you get a markdown notice + issue link instead.

## From your shell tool

```bash
agex gamify --agent claude-code
# ... use your runtime for a while ...
agex hook read --agent claude-code
# ... later, to undo:
agex gamify --uninstall --agent claude-code
```
