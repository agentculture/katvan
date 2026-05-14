"""Inject Jekyll frontmatter into a pulled sibling-repo doc.

Ported near-verbatim from the librarian skill's ``_frontmatter.py``. katvan's
``pull`` verb (landing in a later release) pipes every ``.md`` file from a
sibling repo's ``docs/`` tree through this module before writing it under
``site/docs/<repo>/``. Sibling docs are raw markdown — most have no
frontmatter at all — but every page on the culture.dev multi-site build
needs at minimum a ``sites:`` key.

Logic
-----
* Parse an existing ``---\\n...\\n---`` frontmatter block if present.
  Minimal hand-rolled line-oriented parser — stdlib only, NO PyYAML.
* Merge in defaults ONLY for keys that are absent (never clobber):

  - ``sites:``      → ``[culture]``
  - ``title:``      → derived from the first ``# H1`` in the body; omitted
    if there is no H1 (``doctor`` flags this as ``no-h1``)
  - ``permalink:``  → ``/<repo>/<rel-path sans .md>/`` (always trailing slash)
  - ``nav_order:``  → ``N`` if the filename has a numeric prefix like
    ``01-foo.md``, else omitted

* Emit ``---\\n<merged frontmatter>\\n---\\n<original body>``. The body is
  preserved byte-for-byte.

The core is exposed as :func:`inject` so callers (the future ``pull`` verb)
can use it directly as a library function. :func:`main` keeps the
stdin→stdout CLI behaviour so ``python -m katvan.frontmatter`` still works.
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import List

# Keys we emit in a stable order so output is deterministic and reviewable.
_KEY_ORDER = ["title", "sites", "permalink", "nav_order"]


def split_frontmatter(text, rel_path=None):
    """Return ``(frontmatter_lines, body, warning)``.

    ``frontmatter_lines`` is the list of raw lines between the ``---`` fences
    (empty list if there is no frontmatter block). ``body`` is everything
    after the closing fence, byte-for-byte (or the whole input if there was
    no block). ``warning`` is ``None`` normally, or a human-readable string
    when a malformed opener (no closing fence) was detected — callers may
    surface it however they like; :func:`main` writes it to stderr to
    preserve the original script's behaviour.
    """
    # A frontmatter block must start on the very first line with `---`.
    if not text.startswith("---\n") and text != "---\n" and not text.startswith("---\r\n"):
        return [], text, None

    lines = text.split("\n")
    # lines[0] is the opening `---`. Find the closing fence.
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fm_lines = lines[1:idx]
            # Body is everything after the closing fence. Slice it out of
            # the original `text` by string offset rather than rejoining
            # the split lines — rejoining would normalize CRLF to LF and
            # break the "byte-for-byte" guarantee. `lines[:idx+1]` is the
            # opening fence + frontmatter + closing fence; it was produced
            # by splitting on "\n", so re-joining on "\n" and adding back
            # the one trailing "\n" reconstructs the exact prefix length.
            prefix = "\n".join(lines[: idx + 1]) + "\n"
            body = text[len(prefix) :]
            return fm_lines, body, None
    # Opener with no closing fence — malformed. Surface a warning so the
    # operator sees it (otherwise the malformed text would silently be
    # treated as body and then re-wrapped in a fresh block, duplicating
    # it), and treat the whole input as body.
    where = rel_path if rel_path else "<stdin>"
    warning = (
        "katvan.frontmatter: warning: {}: frontmatter opener with no closing "
        "fence — treating whole file as body".format(where)
    )
    return [], text, warning


def parse_frontmatter_keys(fm_lines):
    """Return the set of top-level keys present in the frontmatter block.

    We only need to know which keys EXIST (so we never clobber them), not
    their values — so this is a deliberately shallow parse: a line that
    starts in column 0 with ``key:`` registers ``key``. Nested/list lines
    (indented, or starting with ``-``) are ignored.
    """
    keys = set()
    for line in fm_lines:
        if not line or line[0] in (" ", "\t", "-", "#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):", line)
        if m:
            keys.add(m.group(1))
    return keys


def derive_title(body):
    """First ``# H1`` in the body, leading ``# `` stripped. None if absent."""
    for line in body.split("\n"):
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return None


def derive_nav_order(rel_path):
    """N if the filename has a numeric prefix like ``01-foo.md``, else None."""
    filename = rel_path.rsplit("/", 1)[-1]
    m = re.match(r"^0*(\d+)[-_]", filename)
    if m:
        return int(m.group(1))
    return None


def build_permalink(repo, rel_path):
    """``/<repo>/<rel-path sans .md>/`` — always a trailing slash."""
    stem = rel_path
    if stem.endswith(".md"):
        stem = stem[:-3]
    stem = stem.strip("/")
    return f"/{repo}/{stem}/"


def render_value(key, value):
    """Render a single frontmatter line for an injected default."""
    if key == "sites":
        # value is a list of site ids.
        inner = ", ".join(value)
        return f"sites: [{inner}]"
    if key == "nav_order":
        return f"nav_order: {value}"
    # title / permalink: scalar. Quote titles that could confuse the parser.
    if key == "title":
        if re.search(r"[:#\[\]{}]", str(value)) or str(value) != str(value).strip():
            return 'title: "{}"'.format(str(value).replace('"', '\\"'))
        return f"title: {value}"
    return f"{key}: {value}"


def inject(text: str, repo: str, rel_path: str) -> tuple[str, List[str]]:
    """Inject Jekyll frontmatter defaults into ``text``.

    Returns ``(output, warnings)`` — ``output`` is the rewritten document
    (``---\\n<merged frontmatter>\\n---\\n<body>``), and ``warnings`` is a
    list of human-readable warning strings (empty when nothing was amiss; a
    malformed frontmatter opener produces one entry).

    This is the core of the module, callable as a plain library function.
    The merge is non-clobbering: an existing key is never overwritten, and
    the original body is preserved byte-for-byte.
    """
    warnings: List[str] = []
    fm_lines, body, warning = split_frontmatter(text, rel_path)
    if warning:
        warnings.append(warning)
    existing_keys = parse_frontmatter_keys(fm_lines)

    # Compute the defaults we would inject.
    injected = {}
    if "sites" not in existing_keys:
        injected["sites"] = ["culture"]
    if "title" not in existing_keys:
        title = derive_title(body)
        if title is not None:
            injected["title"] = title
        # else: omit — doctor will flag `no-h1`.
    if "permalink" not in existing_keys:
        injected["permalink"] = build_permalink(repo, rel_path)
    if "nav_order" not in existing_keys:
        nav = derive_nav_order(rel_path)
        if nav is not None:
            injected["nav_order"] = nav

    # Assemble the merged frontmatter: existing lines verbatim, then the
    # injected defaults in stable key order.
    merged = list(fm_lines)
    for key in _KEY_ORDER:
        if key in injected:
            merged.append(render_value(key, injected[key]))

    out = "---\n" + "\n".join(merged) + "\n---\n" + body
    return out, warnings


def main(argv=None):
    """stdin → stdout CLI shim, preserving ``_frontmatter.py``'s behaviour."""
    parser = argparse.ArgumentParser(
        prog="katvan.frontmatter",
        description="Inject Jekyll frontmatter into a pulled sibling-repo doc.",
    )
    parser.add_argument("--repo", required=True, help="sibling repo id, e.g. ghafi")
    parser.add_argument(
        "--rel-path",
        required=True,
        help="path of the file within the sibling's docs/ dir, e.g. guides/intro.md",
    )
    args = parser.parse_args(argv)

    text = sys.stdin.read()
    out, warnings = inject(text, args.repo, args.rel_path)
    for warning in warnings:
        sys.stderr.write(warning + "\n")
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
