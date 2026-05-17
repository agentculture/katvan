---
title: ghafi learn
parent: ghafi reference
sites: [culture]
---

# `ghafi learn`

```json
{
  "auth": {
    "env_vars": [
      "GITHUB_TOKEN",
      "GH_TOKEN"
    ],
    "org_extra_scopes": [
      "admin:org"
    ],
    "required_scopes": [
      "repo",
      "admin:repo_hook"
    ]
  },
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
        "whoami"
      ],
      "summary": "Verify GITHUB_TOKEN against GET /user."
    },
    {
      "path": [
        "repo",
        "create"
      ],
      "summary": "Create a GitHub repo (dry-run by default; --apply commits)."
    },
    {
      "path": [
        "repo",
        "scaffold"
      ],
      "summary": "Shell out to `afi cli cite` to drop the python-cli template."
    },
    {
      "path": [
        "repo",
        "env"
      ],
      "summary": "Create a Trusted-Publishing environment (pypi or testpypi)."
    }
  ],
  "exit_codes": {
    "0": "success",
    "1": "user-input error",
    "2": "environment/setup error",
    "3": "authentication error",
    "4": "upstream API error"
  },
  "explain_pointer": "ghafi explain <path> (e.g. 'ghafi explain repo create')",
  "json_support": true,
  "purpose": "Bootstrap and manage AgentCulture sibling repositories on GitHub: repo creation with workflow permissions, afi-cli scaffolding, and Trusted-Publishing environments.",
  "tool": "ghafi",
  "trusted_publishing_docs": "https://docs.pypi.org/trusted-publishers/",
  "version": "0.0.2"
}
```
