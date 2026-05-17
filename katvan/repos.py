"""Sibling-repo registry — ported from the librarian skill's ``_repos.sh``.

Parses ``site/_data/agentculture_repos.yml`` (the sibling-repo registry that
drives katvan's docs verbs) and exposes lookup helpers the overview / pull /
doctor verbs build on.

Public surface
--------------
- :func:`registry_path` — absolute path to the registry YAML.
- :func:`repos` — iterate ``(id, docs_mode, local_path)`` per registry entry.
- :func:`classify` — the ``docs_mode`` for one repo id (``unknown`` if absent).
- :func:`local_path` — the local checkout path for one repo id (``""`` if not
  checked out).
- :func:`set_siblings_root` / :func:`siblings_root` — override / read where
  sibling repos are expected to be checked out locally.

YAML parsing is **stdlib only** — a minimal line-oriented parser, matching
the hand-rolled fallback the bash helper used. PyYAML is *not* a dependency.

Path resolution differs deliberately from the bash original: ``_repos.sh``
hardcoded the repo root and ``/home/spark/git``. This port walks up from the
current working directory to find the repo root, and reads the siblings root
from ``$KATVAN_SIBLINGS_ROOT`` (default: the parent of the discovered repo
root). Callers may also override it programmatically via
:func:`set_siblings_root` — PR 2's verbs thread a ``--siblings-root`` flag
through this way.
"""

from __future__ import annotations

import argparse
import functools
import os
import sys
from pathlib import Path
from typing import Iterator

from katvan.cli._errors import EXIT_ENV_ERROR, EXIT_USER_ERROR, KatvanError

# Relative location of the registry within a katvan checkout.
_REGISTRY_REL = Path("site/_data/agentculture_repos.yml")

# Programmatic override for the siblings root. ``None`` means "not set" —
# fall back to ``$KATVAN_SIBLINGS_ROOT`` then the repo root's parent.
_siblings_root_override: Path | None = None


def set_siblings_root(path: str | os.PathLike[str] | None) -> None:
    """Override where sibling repos are expected to be checked out locally.

    Pass ``None`` to clear the override and fall back to
    ``$KATVAN_SIBLINGS_ROOT`` / the repo root's parent. PR 2's verbs call
    this to honour a ``--siblings-root`` flag.
    """
    global _siblings_root_override
    _siblings_root_override = Path(path) if path is not None else None


# Memoization note: ``_find_repo_root`` and ``_parse_registry`` are wrapped
# with ``functools.lru_cache`` — the repo root and the registry contents are
# stable for the life of a process, and PR 2's verbs loop ``classify()`` over
# every repo, so without caching that would be O(n^2) file reads. The
# siblings-root (``siblings_root()`` / ``local_path()`` / ``set_siblings_root()``)
# is deliberately NOT cached: it is intentionally mutable at runtime, and
# nothing the caches hold depends on it, so ``set_siblings_root()`` stays
# effective even after the registry/root have been cached.
@functools.lru_cache(maxsize=None)
def _find_repo_root(start: Path | None = None) -> Path:
    """Walk up from ``start`` (default CWD) to a dir containing the registry."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / _REGISTRY_REL).is_file():
            return candidate
    raise KatvanError(
        code=EXIT_ENV_ERROR,
        message=(f"could not find {_REGISTRY_REL} in any parent of {here}"),
        remediation="run katvan from within a katvan checkout (the repo with site/)",
    )


def registry_path() -> Path:
    """Return the absolute path to ``site/_data/agentculture_repos.yml``.

    Raises :class:`KatvanError` (exit 2, environment error) if no katvan
    checkout is found by walking up from the current working directory.
    """
    return _find_repo_root() / _REGISTRY_REL


def siblings_root() -> Path:
    """Return the directory where sibling repos are expected locally.

    Precedence: explicit :func:`set_siblings_root` override >
    ``$KATVAN_SIBLINGS_ROOT`` > the parent directory of the discovered repo
    root.
    """
    if _siblings_root_override is not None:
        return _siblings_root_override
    env = os.environ.get("KATVAN_SIBLINGS_ROOT")
    if env:
        return Path(env)
    return _find_repo_root().parent


@functools.lru_cache(maxsize=None)
def _parse_registry(path: Path) -> tuple[tuple[str, str], ...]:
    """Return ``(id, docs_mode)`` for every registry entry.

    Hand-rolled line-oriented parse — stdlib only, no PyYAML. Mirrors the
    fallback parser in ``_repos.sh``: a ``- id:`` line opens an entry, a
    following column-0 ``docs_mode:`` line sets its mode (default ``skip``).

    Memoized on ``path`` — see the note above :func:`_find_repo_root`. The
    result is a tuple (not a list) so it is hashable and safe to cache.

    Raises :class:`KatvanError` if the file has non-comment content but the
    parser still yields zero entries — a parse failure (e.g. block-style
    YAML) that would otherwise masquerade as a legitimately empty registry.
    A file with only comments / blank lines yields zero entries without error.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as err:
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=f"registry not readable: {path}: {err}",
            remediation="check the file exists and is readable",
        ) from err

    entries: list[tuple[str, str]] = []
    has_content = False
    cur: list[str] | None = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        has_content = True
        if stripped.startswith("- id:"):
            if cur is not None:
                entries.append((cur[0], cur[1]))
            rid = stripped.split(":", 1)[1].strip().strip("'\"")
            cur = [rid, "skip"]
        elif cur is not None and stripped.startswith("docs_mode:"):
            cur[1] = stripped.split(":", 1)[1].strip().strip("'\"")
    if cur is not None:
        entries.append((cur[0], cur[1]))

    if not entries and has_content:
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=(
                f"registry parsed zero entries from {path} — expected '- id:' "
                "entries; the file may be malformed or in an unsupported YAML style"
            ),
            remediation="check the registry uses inline '- id: <name>' entry openers",
        )
    return tuple(entries)


def local_path(repo_id: str) -> str:
    """Return the local checkout path for ``repo_id``, or ``""`` if absent.

    The candidate is ``<siblings_root>/<repo_id>``; it is returned only when
    that directory actually exists.
    """
    candidate = siblings_root() / repo_id
    return str(candidate) if candidate.is_dir() else ""


def repos() -> Iterator[tuple[str, str, str]]:
    """Yield ``(id, docs_mode, local_path)`` for every registry entry.

    ``local_path`` is ``<siblings_root>/<id>`` when that directory exists,
    else the empty string — matching ``_repos.sh``'s ``librarian_repos``.
    """
    for rid, mode in _parse_registry(registry_path()):
        if not rid:
            continue
        yield rid, mode, local_path(rid)


@functools.lru_cache(maxsize=None)
def _parse_entries(path: Path) -> tuple[dict[str, str], ...]:
    """Return a tuple of full-entry dicts for every registry row.

    Extends :func:`_parse_registry`'s line-oriented parser to capture every
    scalar field (``id``, ``category``, ``maturity``, ``docs_mode``,
    ``description``, ``package``, ``binary``, ``docs``, ``install``,
    ``caveat``) on the entry. List-valued fields (e.g. ``related``) are
    skipped — the overview verb only needs scalars, and bringing in PyYAML
    just to parse them would violate the stdlib-only invariant.

    Memoized on ``path`` for the same reasons as :func:`_parse_registry`.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as err:
        raise KatvanError(
            code=EXIT_ENV_ERROR,
            message=f"registry not readable: {path}: {err}",
            remediation="check the file exists and is readable",
        ) from err

    # Scalar fields we care about. Anything else (e.g. ``related:`` which is
    # a YAML list) is ignored — the line-oriented parser doesn't grok lists,
    # and the overview verb does not need them.
    _SCALAR_FIELDS = (
        "category", "maturity", "docs_mode", "description",
        "package", "binary", "docs", "install", "caveat",
    )

    entries: list[dict[str, str]] = []
    has_content = False
    cur: dict[str, str] | None = None
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        has_content = True
        if stripped.startswith("- id:"):
            if cur is not None:
                entries.append(cur)
            rid = stripped.split(":", 1)[1].strip().strip("'\"")
            cur = {"id": rid, "docs_mode": "skip"}
        elif cur is not None:
            for field in _SCALAR_FIELDS:
                prefix = f"{field}:"
                if stripped.startswith(prefix):
                    value = stripped.split(":", 1)[1].strip().strip("'\"")
                    # Skip list-valued lines like ``related: [a, b]`` —
                    # caller doesn't need them and our stripping would
                    # leave brackets in the value.
                    if value.startswith("["):
                        break
                    cur[field] = value
                    break
    if cur is not None:
        entries.append(cur)

    if not entries and has_content:
        raise KatvanError(
            code=EXIT_USER_ERROR,
            message="registry has content but parsed zero entries",
            remediation=(
                "check YAML formatting — entries must start with '- id: <id>'"
            ),
        )
    return tuple(entries)


def entries() -> list[dict[str, str]]:
    """Return a list of full-entry dicts for every registry row.

    Each dict carries at least ``id`` and ``docs_mode`` (defaulting to
    ``"skip"`` if absent); other scalar fields (``category``, ``maturity``,
    ``description``, ``package``, ``binary``, ``docs``, ``install``,
    ``caveat``) are present when set on the entry. The overview verb groups
    on ``category`` and surfaces ``id`` + ``description``.
    """
    return [dict(e) for e in _parse_entries(registry_path())]


def classify(repo_id: str) -> str:
    """Return the ``docs_mode`` for ``repo_id``.

    One of ``pull`` / ``self-published`` / ``skip`` for a registered repo, or
    ``"unknown"`` if the id is not in the registry. (The bash original also
    signalled this via a non-zero return code; the Python port surfaces it
    purely through the ``"unknown"`` sentinel.)
    """
    for rid, mode in _parse_registry(registry_path()):
        if rid == repo_id:
            return mode
    return "unknown"


def main(argv: list[str] | None = None) -> int:
    """Tiny CLI shim so ``python -m katvan.repos`` is inspectable.

    With no args, prints the ``id<TAB>docs_mode<TAB>local_path`` table — the
    same shape ``_repos.sh``'s ``librarian_repos`` emitted.
    """
    parser = argparse.ArgumentParser(
        prog="katvan.repos",
        description="Inspect the AgentCulture sibling-repo registry.",
    )
    parser.add_argument(
        "--registry-path",
        action="store_true",
        help="Print the absolute registry path and exit.",
    )
    parser.add_argument(
        "--classify",
        metavar="REPO_ID",
        help="Print the docs_mode for REPO_ID and exit.",
    )
    args = parser.parse_args(argv)

    try:
        if args.registry_path:
            print(registry_path())
            return 0
        if args.classify:
            mode = classify(args.classify)
            print(mode)
            # The library ``classify()`` returns the ``"unknown"`` sentinel,
            # but the CLI shim mirrors ``_repos.sh``'s ``librarian_classify``,
            # which exited non-zero for an unregistered repo id.
            return EXIT_USER_ERROR if mode == "unknown" else 0
        for rid, mode, path in repos():
            print(f"{rid}\t{mode}\t{path}")
    except KatvanError as err:
        sys.stderr.write(f"error: {err.message}\n")
        if err.remediation:
            sys.stderr.write(f"hint: {err.remediation}\n")
        return err.code
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
