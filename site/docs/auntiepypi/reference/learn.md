---
title: auntiepypi learn
parent: auntiepypi reference
sites: [culture]
---

# `auntiepypi learn`

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
      "summary": "Composite: packages dashboard + detected servers. TARGET drills into one detection, flavor, or package. --proc opts into /proc scan."
    },
    {
      "path": [
        "doctor"
      ],
      "summary": "Diagnose declared inventory; --apply to act (start servers, delete half-supervised). Use --decide for ambiguous duplicates."
    },
    {
      "path": [
        "up"
      ],
      "summary": "Start a server. Bare form starts auntie's own first-party PEP 503 simple-index; <name> targets one declared server; --all aggregates the first-party server with every supervised declaration."
    },
    {
      "path": [
        "down"
      ],
      "summary": "Stop a server. Same target shape as up; PID-tracked for managed_by=command and managed_by=auntie."
    },
    {
      "path": [
        "restart"
      ],
      "summary": "Restart a server. Atomic for systemd-user; stop+start for command and the first-party server. Re-spawn uses current pyproject config."
    },
    {
      "path": [
        "publish"
      ],
      "summary": "Upload a wheel/sdist to the configured local index. Requires publish_users allowlist; reads $AUNTIE_PUBLISH_USER / _PASSWORD or prompts."
    },
    {
      "path": [
        "whoami"
      ],
      "summary": "Report configured PyPI / TestPyPI / local index."
    }
  ],
  "exit_codes": {
    "0": "success / dry-run / ambiguous --decide deferred / unknown TARGET",
    "1": "configuration or usage error",
    "2": "--apply ran but at least one actionable server is still not up"
  },
  "explain_pointer": "auntie explain <path>",
  "json_support": true,
  "package": "auntiepypi",
  "planned": [],
  "purpose": "CLI and agent for managing PyPI packages; surfaces remote (pypi.org) package data and a detect-only view of locally running PyPI servers.",
  "tool": "auntie",
  "version": "0.8.4"
}
```
