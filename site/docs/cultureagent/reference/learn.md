---
title: cultureagent learn
parent: cultureagent reference
---

# `cultureagent learn`

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
      "summary": "Descriptive map of CLI surface."
    },
    {
      "path": [
        "doctor"
      ],
      "summary": "Diagnostics with hint markers."
    }
  ],
  "exit_codes": {
    "0": "success",
    "1": "user-input error",
    "2": "environment/setup error"
  },
  "explain_pointer": "cultureagent explain <path>",
  "json_support": true,
  "purpose": "Agent runtime for the Culture mesh: runs per-backend harnesses that bridge IRC events and agent SDKs.",
  "tool": "cultureagent",
  "version": "0.6.3"
}
```
