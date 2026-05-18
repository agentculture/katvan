---
title: learn
parent: Commands
nav_order: 50
sites: [culture]
permalink: /agex/commands/learn/
---

# `agex learn [topic] --agent <backend>`

Without a topic, lists the lessons available for your backend. With a topic, teaches it — emits a markdown lesson body plus inline skill-template code blocks you can write into your project.

## From your shell tool

```bash
agex learn --agent claude-code
agex learn introspect --agent claude-code
```

## Notes

- Lessons gated on a backend feature (e.g., `gamify` needs hooks) may still appear in the list, but they are not currently annotated as unsupported in the menu — Phase 8 adds that capability-based routing.
- v0.1 emits inline code blocks only. A future `--write` flag is tracked as an open issue.
