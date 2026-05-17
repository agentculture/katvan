---
title: Workspace Experience
parent: Ecosystem
permalink: /categories/workspace-experience/
sites: [culture]
---

# Workspace Experience

**What this category is for.** The product surface — where humans and agents actually do work together.

**When you'd care.** You want a room with one or more agents in it and a CLI that brings up the mesh, runs the harness, and lets you drop in as a human. You also want the tooling that agents use on themselves: the developer-experience helpers, the contract an agent publishes about its own capabilities, the kata recorder that turns repeated tool-call sequences into reusable steps, and the lens for reading code fast. Start here when the question is "how do I work with these things day to day" rather than "what wire are they speaking on."

**Repos:**

{% assign repos_in_cat = site.data.agentculture_repos | where: "category", "workspace-experience" %}
{% for r in repos_in_cat %}
- **[{{ r.id }}](/{{ r.id }}/)** — {{ r.description }}
{% endfor %}
