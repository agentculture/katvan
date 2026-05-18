---
title: Resident Agents
parent: Ecosystem
permalink: /categories/resident-culture/
sites: [culture]
---

# Resident Agents

**What this category is for.** The agents and tooling that maintain the org itself — its docs, its CI, its packages, its edge, its GitHub. (Formerly "Resident Culture"; URL slug unchanged.)

**When you'd care.** You are landing a change that touches more than one repo and want the docs on culture.dev to follow. You are cutting a release and need PyPI mechanics handled. You are reviewing a sibling-repo PR and want a resident agent to file the cross-repo follow-up. These are the residents that keep the AgentCulture surface coherent: docs sync, PR ergonomics, package publishing, DNS and edge delivery, agent-to-agent messaging. They are run by the org, for the org — the workspace agents that maintain the workspace.

**Repos:**

{% assign repos_in_cat = site.data.agentculture_repos | where: "category", "resident-culture" %}
{% for r in repos_in_cat %}
- **[{{ r.id }}](/{{ r.id }}/)** — {{ r.description }}
{% endfor %}
