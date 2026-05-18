"""Google Search Console integration: read-only indexing-health verbs.

Submodules:
    client     — service-account auth + thin GSC API wrapper.
    sitemaps   — ``katvan gsc sitemaps`` logic.
    inspect    — ``katvan gsc inspect <url>`` logic.
    doctor     — ``katvan gsc doctor`` composite.
    formatters — text + JSON output helpers shared across subcommands.
"""

from __future__ import annotations
