#!/usr/bin/env python3
"""_frontmatter.py — inject Jekyll frontmatter into a pulled sibling-repo doc.

The librarian skill's `pull` verb pipes every `.md` file from a sibling
repo's `docs/` tree through this script before writing it under
`site/docs/<repo>/`. Sibling docs are raw markdown — most have no
frontmatter at all — but every page on the culture.dev multi-site build
needs at minimum a `sites:` key (see site/docs/README.md rule 7).

Usage:
    _frontmatter.py --repo <id> --rel-path <path/within/docs.md> < in.md > out.md

Logic:
  * Parse an existing `---\\n...\\n---` frontmatter block if present.
    Minimal hand-rolled line-oriented parser — stdlib only, NO PyYAML.
  * Merge in defaults ONLY for keys that are absent (never clobber):
      sites:      -> [culture]
      title:      -> derived from the first `# H1` in the body; omitted
                     if there is no H1 (doctor flags this as `no-h1`)
      permalink:  -> /<repo>/<rel-path sans .md>/  (always trailing slash)
      nav_order:  -> N if the filename has a numeric prefix like `01-foo.md`,
                     else omitted
  * Emit `---\\n<merged frontmatter>\\n---\\n<original body>`. The body is
    preserved byte-for-byte.

Directly testable: feed stdin, check stdout.
"""

import argparse
import re
import sys

# Keys we emit in a stable order so output is deterministic and reviewable.
_KEY_ORDER = ["title", "sites", "permalink", "nav_order"]


def split_frontmatter(text):
    """Return (frontmatter_lines, body).

    frontmatter_lines is the list of raw lines between the `---` fences
    (empty list if there is no frontmatter block). body is everything
    after the closing fence, byte-for-byte (or the whole input if there
    was no block).
    """
    # A frontmatter block must start on the very first line with `---`.
    if not text.startswith("---\n") and text != "---\n" and not text.startswith("---\r\n"):
        return [], text

    lines = text.split("\n")
    # lines[0] is the opening `---`. Find the closing fence.
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fm_lines = lines[1:idx]
            # Body is everything after the closing fence. Rejoin with \n;
            # the opening `---` consumed exactly one leading newline.
            body = "\n".join(lines[idx + 1:])
            return fm_lines, body
    # No closing fence — treat the whole thing as body (malformed block).
    return [], text


def parse_frontmatter_keys(fm_lines):
    """Return the set of top-level keys present in the frontmatter block.

    We only need to know which keys EXIST (so we never clobber them), not
    their values — so this is a deliberately shallow parse: a line that
    starts in column 0 with `key:` registers `key`. Nested/list lines
    (indented, or starting with `-`) are ignored.
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
    """First `# H1` in the body, with the leading `# ` stripped. None if absent."""
    for line in body.split("\n"):
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return None


def derive_nav_order(rel_path):
    """N if the filename has a numeric prefix like `01-foo.md`, else None."""
    filename = rel_path.rsplit("/", 1)[-1]
    m = re.match(r"^0*(\d+)[-_]", filename)
    if m:
        return int(m.group(1))
    return None


def build_permalink(repo, rel_path):
    """/<repo>/<rel-path sans .md>/ — always a trailing slash."""
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


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inject Jekyll frontmatter into a pulled sibling-repo doc."
    )
    parser.add_argument("--repo", required=True, help="sibling repo id, e.g. ghafi")
    parser.add_argument(
        "--rel-path",
        required=True,
        help="path of the file within the sibling's docs/ dir, e.g. guides/intro.md",
    )
    args = parser.parse_args(argv)

    text = sys.stdin.read()
    fm_lines, body = split_frontmatter(text)
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
        injected["permalink"] = build_permalink(args.repo, args.rel_path)
    if "nav_order" not in existing_keys:
        nav = derive_nav_order(args.rel_path)
        if nav is not None:
            injected["nav_order"] = nav

    # Assemble the merged frontmatter: existing lines verbatim, then the
    # injected defaults in stable key order.
    merged = list(fm_lines)
    for key in _KEY_ORDER:
        if key in injected:
            merged.append(render_value(key, injected[key]))

    out = "---\n" + "\n".join(merged) + "\n---\n" + body
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
