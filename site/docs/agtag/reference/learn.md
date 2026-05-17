---
title: agtag learn
parent: agtag reference
sites: [culture]
---

# `agtag learn`

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
        "issue",
        "post"
      ],
      "summary": "Open a new issue (auto-signed)."
    },
    {
      "path": [
        "issue",
        "fetch"
      ],
      "summary": "Read an issue + comments."
    },
    {
      "path": [
        "issue",
        "reply"
      ],
      "summary": "Comment on an issue (auto-signed)."
    }
  ],
  "exit_codes": {
    "0": "success",
    "1": "user-input error",
    "2": "environment/setup error"
  },
  "explain_pointer": "agtag explain <path>",
  "json_support": true,
  "purpose": "Agent to Agent communication CLI: file, fetch, and reply to GitHub issues with auto-signature.",
  "tool": "agtag",
  "version": "0.2.1"
}
```
