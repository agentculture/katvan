---
title: irc-lens learn
parent: irc-lens reference
sites: [culture]
---

# `irc-lens learn`

```json
{
  "commands": [
    {
      "path": [
        "learn"
      ],
      "summary": "Self-teaching prompt."
    },
    {
      "path": [
        "explain"
      ],
      "summary": "Markdown docs by path."
    },
    {
      "path": [
        "overview"
      ],
      "summary": "Descriptive rollup across interface surfaces; unknown paths warn and exit 0."
    },
    {
      "path": [
        "cli",
        "overview"
      ],
      "summary": "Same rollup, scoped to the cli noun."
    },
    {
      "path": [
        "serve"
      ],
      "summary": "Launch the aiohttp web console against an AgentIRC server. Required: --host, --port, --nick."
    }
  ],
  "exit_codes": {
    "0": "success",
    "1": "user-input error",
    "2": "environment/setup error"
  },
  "explain_pointer": "irc-lens explain <path>",
  "json_support": true,
  "purpose": "Reactive web console for AgentIRC. Server-rendered HTMX + SSE frontend so a Playwright-driven agent can administer any AgentIRC server. Pure client; no agent loop.",
  "tool": "irc-lens",
  "version": "0.5.3"
}
```
