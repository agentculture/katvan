---
title: Resident Domain
parent: Ecosystem
permalink: /categories/resident-domain/
sites: [culture]
---

# Resident Domain

**What this category is for.** Agents that integrate with external services or run domain-specific operations.

**When you'd care.** You want an agent that books meeting rooms, an agent that triages security findings, an agent that moderates a Telegram community, an agent that reconciles vendor payments. These are worked examples of a resident agent pointed at a single domain — the shape you copy when you build your own. They share the runtime and identity of the rest of the mesh, but their value lives in the integration: a calendar API, an appsec scanner, a Telegram bot, a Tipalti tenant. Read these when you are about to write the next one and want a reference for what "good" looks like.

**Repos:**

{% assign repos_in_cat = site.data.agentculture_repos | where: "category", "resident-domain" %}
{% for r in repos_in_cat %}
- **[{{ r.id }}](/{{ r.id }}/)** — {{ r.description }}
{% endfor %}
