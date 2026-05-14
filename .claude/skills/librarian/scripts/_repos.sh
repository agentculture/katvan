#!/usr/bin/env bash
# _repos.sh — shared helper for the librarian skill. SOURCE this, do not
# execute it. Parses site/_data/agentculture_repos.yml (the sibling-repo
# registry) and exposes a couple of lookup functions the overview / pull /
# doctor scripts build on.
#
# Provided functions:
#   librarian_registry_path        echo the absolute path to the registry YAML
#   librarian_repos                emit one line per repo: "<id>\t<docs_mode>\t<local_path>"
#                                  local_path is /home/spark/git/<id> if that dir
#                                  exists, else the empty string
#   librarian_classify <id>        echo the docs_mode for <id> (pull|self-published|
#                                  skip), or "unknown" + return 1 if not in registry
#   librarian_local_path <id>      echo /home/spark/git/<id> if checked out, else ""
#
# YAML parsing is delegated to python3 (stdlib only — a minimal line-oriented
# parser; PyYAML is used when present but is NOT required).

# Resolve the skill's scripts dir, then the repo root, then the registry path.
_LIBRARIAN_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_LIBRARIAN_REPO_ROOT="$(cd "$_LIBRARIAN_SCRIPTS_DIR/../../../.." && pwd)"
_LIBRARIAN_REGISTRY="$_LIBRARIAN_REPO_ROOT/site/_data/agentculture_repos.yml"

# Where sibling repos are expected to be checked out locally.
: "${LIBRARIAN_SIBLINGS_ROOT:=/home/spark/git}"

librarian_registry_path() {
    printf '%s\n' "$_LIBRARIAN_REGISTRY"
}

# Emit "<id>\t<docs_mode>" for every registry entry. python3 stdlib only.
_librarian_parse_registry() {
    if [[ ! -f "$_LIBRARIAN_REGISTRY" ]]; then
        echo "_repos.sh: registry not found: $_LIBRARIAN_REGISTRY" >&2
        return 1
    fi
    python3 - "$_LIBRARIAN_REGISTRY" <<'PY'
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    raw = fh.read()

entries = []
cur = None

# Try PyYAML first — accurate, but optional.
try:
    import yaml  # noqa: F401
    data = yaml.safe_load(raw)
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "id" in item:
                entries.append((str(item["id"]), str(item.get("docs_mode", "skip"))))
except Exception:
    entries = []

# Fallback: hand-rolled line-oriented parse (no PyYAML).
if not entries:
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("- id:"):
            if cur is not None:
                entries.append(cur)
            rid = stripped.split(":", 1)[1].strip().strip("'\"")
            cur = [rid, "skip"]
        elif cur is not None and stripped.startswith("docs_mode:"):
            cur[1] = stripped.split(":", 1)[1].strip().strip("'\"")
    if cur is not None:
        entries.append(cur)

for rid, mode in entries:
    print(f"{rid}\t{mode}")
PY
}

librarian_local_path() {
    local id="$1"
    local candidate="$LIBRARIAN_SIBLINGS_ROOT/$id"
    if [[ -d "$candidate" ]]; then
        printf '%s\n' "$candidate"
    else
        printf '%s\n' ""
    fi
}

# Emit "<id>\t<docs_mode>\t<local_path>" per repo.
librarian_repos() {
    local id mode local_path
    while IFS=$'\t' read -r id mode; do
        [[ -z "$id" ]] && continue
        local_path="$(librarian_local_path "$id")"
        printf '%s\t%s\t%s\n' "$id" "$mode" "$local_path"
    done < <(_librarian_parse_registry)
}

# Classify a single repo id. Echoes the docs_mode; returns 1 (and echoes
# "unknown") if the id is not in the registry.
librarian_classify() {
    local want="$1" id mode
    while IFS=$'\t' read -r id mode; do
        if [[ "$id" == "$want" ]]; then
            printf '%s\n' "$mode"
            return 0
        fi
    done < <(_librarian_parse_registry)
    printf '%s\n' "unknown"
    return 1
}
