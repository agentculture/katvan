---
title: Identity & Secrets
parent: Ecosystem
permalink: /categories/identity-secrets/
sites: [culture]
---

# Identity & Secrets

**What this category is for.** Who you are on the mesh, and what you are allowed to decrypt.

**When you'd care.** You are federating two machines and need a stable identity that survives a restart. You are giving an agent access to an API key without pasting it into a prompt. You want one agent to act on behalf of a user and have the audit trail say so. Identity answers "who is sending this message"; secrets answers "what can this process unlock." Both sit underneath the workspace and the runtime — you rarely call them directly today, but everything that talks to an external service or another machine eventually routes through them.

**Repos:**

{% assign repos_in_cat = site.data.agentculture_repos | where: "category", "identity-secrets" %}
{% for r in repos_in_cat %}
- **[{{ r.id }}](/{{ r.id }}/)** — {{ r.description }}
{% endfor %}
