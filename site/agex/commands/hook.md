---
title: hook
parent: Commands
nav_order: 40
sites: [culture]
permalink: /agex/commands/hook/
---

# `agex hook write <event> [key=value ...]` / `agex hook read --agent <backend>`

## `write`

Called by installed hooks (see `agex gamify`, Phase 7). Appends a JSON line to `.agex/data/<event>.json`. Silent. Safe for concurrent invocation (file locking via `portalocker`).

```bash
agex hook write post-tool-use tool=Read
```

## `read`

Renders tracked events as a markdown table. Prints the source JSON path for deeper inspection.

```bash
agex hook read --agent claude-code
```

## Notes

- Event names are free-form; conventional names: `post-tool-use`, `user-prompt`, `stop`, `sessions`.
- Extra positional `key=value` pairs are captured into the payload. Empty keys (e.g., `=foo`) are dropped.
- Timestamp (`ts`) is attached automatically; a positional `ts=<value>` overrides it (useful for replays).
- The positional `<event>` name is authoritative — it always wins over any `event=...` pair in args.
- Malformed JSON lines in `.agex/data/*.json` (e.g., from a partial write) are skipped with a warning on `hook read`, not raised.
