#!/usr/bin/env python3
"""Minimal AFI-compatible binary used by katvan pull tests."""
from __future__ import annotations

import json
import sys

_LEARN = {"name": "fakecli", "summary": "A fake sibling CLI for tests.", "nouns": ["thing"]}
_EXPLAIN = {
    "thing": {"verbs": ["do"], "summary": "A thing you can do."},
    "thing/do": {"summary": "Do the thing.", "args": [{"name": "name", "required": True}]},
}


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "learn":
        if "--json" in argv:
            print(json.dumps(_LEARN, sort_keys=True))
        return 0
    if argv and argv[0] == "explain":
        path = "/".join(a for a in argv[1:] if not a.startswith("--"))
        payload = _EXPLAIN.get(path, {})
        if "--json" in argv:
            print(json.dumps(payload, sort_keys=True))
        return 0
    print("usage: fakecli learn|explain [...]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
