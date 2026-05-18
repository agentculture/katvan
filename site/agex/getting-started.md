---
title: Getting started
parent: agex
sites: [culture]
permalink: /agex/getting-started/
nav_order: 2
---

# Getting started

## Install

```bash
uv tool install agex-cli   # recommended
# or
pipx install agex-cli
```

## First commands

```bash
agex explain agex                       # self-describing
agex overview --agent claude-code       # snapshot of this project
agex learn --agent claude-code          # lesson menu
agex learn introspect --agent claude-code
```

## As an agent

You almost never run `agex` yourself. Your human installs it and an agent-authored skill wraps each command. Start with `agex learn introspect --agent <your-backend>` to learn how to discover what your runtime exposes.

## Supported backends

| Backend | Status |
|---|---|
| `claude-code` | Full (overview, learn, gamify, hook). |
| `codex` | Stub probe; most commands emit an "unsupported" notice linking to the issue tracker. |
| `copilot` | Stub probe; same. |
| `acp` | Stub probe; same. |

Unsupported is a **first-class success** (exit 0 with a markdown notice pointing to a GitHub issue), not a failure.
