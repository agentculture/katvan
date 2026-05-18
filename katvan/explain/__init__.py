"""Explain catalog — markdown keyed by command-path tuples.

See :mod:`katvan.explain.catalog` for the string bodies and :func:`resolve`
for lookup. Every noun/verb in the CLI should have a catalog entry.
"""

from __future__ import annotations

from katvan._errors import EXIT_USER_ERROR, KatvanError
from katvan.explain.catalog import ENTRIES


def resolve(path: tuple[str, ...]) -> str:
    """Return the markdown body for ``path`` or raise :class:`KatvanError`."""
    if path in ENTRIES:
        return ENTRIES[path]
    display = " ".join(path) if path else "<root>"
    raise KatvanError(
        code=EXIT_USER_ERROR,
        message=f"no explain entry for: {display}",
        remediation="list known entries with: katvan explain katvan",
    )


def known_paths() -> list[tuple[str, ...]]:
    """Return every catalog path (used by tests)."""
    return list(ENTRIES.keys())
