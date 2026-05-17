---
title: afi-cli learn
parent: afi-cli reference
---

# `afi learn`

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
      "summary": "Markdown docs by noun/verb path."
    },
    {
      "path": [
        "overview"
      ],
      "summary": "Rollup across interface surfaces."
    },
    {
      "path": [
        "doctor"
      ],
      "summary": "Self-diagnose afi's install or audit a target CLI; --fix applies auto-fixable remediations."
    },
    {
      "path": [
        "cli",
        "cite"
      ],
      "summary": "Emit CLI reference drop."
    },
    {
      "path": [
        "cli",
        "doctor"
      ],
      "summary": "Audit a CLI against the rubric (replaces `cli verify`)."
    },
    {
      "path": [
        "cli",
        "verify"
      ],
      "summary": "Deprecated alias for `cli doctor` (removed in v0.6.0)."
    },
    {
      "path": [
        "cli",
        "overview"
      ],
      "summary": "Read-only snapshot of a target CLI."
    }
  ],
  "exit_codes": {
    "0": "success",
    "1": "user-input error",
    "2": "environment/setup error"
  },
  "explain_pointer": "afi explain <path> (e.g. 'afi explain cli doctor')",
  "json_support": true,
  "purpose": "Generate and verify agent-first interfaces for CLIs (and later MCP + HTTP).",
  "tool": "afi",
  "version": "0.7.0"
}
```
