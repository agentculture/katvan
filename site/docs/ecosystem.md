---
title: Ecosystem
nav_order: 3
permalink: /ecosystem/
sites: [culture]
---

# The Culture Ecosystem

{% assign cats = "workspace-experience,core-runtime,identity-secrets,resident-culture,resident-domain,org-site" | split: "," %}
{% for cat in cats %}
{% assign repos_in_cat = site.data.agentculture_repos | where: "category", cat %}
{% if repos_in_cat.size > 0 %}

## {{ site.data.category_titles[cat] | default: cat }}

[Read the category overview →](/categories/{{ cat }}/)

{% for r in repos_in_cat %}{% if r.site_path %}{% assign r_path = r.site_path %}{% else %}{% assign r_path = r.id | prepend: "/" | append: "/" %}{% endif %}
- **[{{ r.id }}]({{ r_path }})** — {{ r.description }}
{% endfor %}

{% endif %}
{% endfor %}
