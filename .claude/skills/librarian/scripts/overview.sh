#!/usr/bin/env bash
set -euo pipefail

# overview.sh — survey the sync state of every sibling repo's docs.
#
# Read-only. For each registry repo (or just --repo <id>):
#   * classify it (pull / self-published / skip)
#   * for `pull` repos:
#       - is site/docs/<repo>/ present?            (synced)
#       - does .katvan-pull.json's sha match the
#         sibling's latest commit touching docs/?  (fresh)
#       - how many synced files lack a `sites:` key (frontmatter health)
#   * self-published / skip repos: just listed with their mode label
#
# Output: a human-readable table; --json emits a structured array.
# Always exits 0.
#
# Usage:
#   overview.sh [--json] [--repo <id>]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_repos.sh
source "$SCRIPT_DIR/_repos.sh"

REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SITE_DOCS="$REPO_ROOT/site/docs"

usage() {
    echo "Usage: overview.sh [--json] [--repo <id>]" >&2
    exit 2
}

JSON=0
ONLY_REPO=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)  JSON=1; shift ;;
        --repo)
            if [[ $# -lt 2 || -z "$2" ]]; then
                echo "Missing value for --repo" >&2; usage
            fi
            ONLY_REPO="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown flag: $1" >&2; usage ;;
    esac
done

# Latest sibling commit sha touching doc/, via local git or `gh api`.
# Echoes the sha (or "" if it can't be determined).
sibling_docs_sha() {
    local id="$1" local_path="$2" sha=""
    if [[ -n "$local_path" && -d "$local_path/.git" ]]; then
        sha="$(git -C "$local_path" log -1 --format=%H -- docs/ 2>/dev/null || true)"
    elif command -v gh >/dev/null 2>&1; then
        sha="$(gh api "repos/agentculture/$id/commits?path=docs&per_page=1" \
                 --jq '.[0].sha' 2>/dev/null || true)"
    fi
    printf '%s\n' "$sha"
}

# Read the recorded sha from site/docs/<repo>/.katvan-pull.json (or "").
manifest_sha() {
    local id="$1" manifest="$SITE_DOCS/$1/.katvan-pull.json"
    [[ -f "$manifest" ]] || { printf '%s\n' ""; return 0; }
    python3 - "$manifest" <<'PY' 2>/dev/null || printf '%s\n' ""
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        print(json.load(fh).get("sha", "") or "")
except Exception:
    print("")
PY
}

# Count .md files under site/docs/<repo>/ that lack a top-level `sites:` key.
count_missing_sites() {
    local dir="$1" missing=0 f
    [[ -d "$dir" ]] || { printf '%s\n' 0; return 0; }
    while IFS= read -r -d '' f; do
        if ! grep -qE '^sites:' "$f"; then
            missing=$((missing + 1))
        fi
    done < <(find "$dir" -name '*.md' -type f -print0 2>/dev/null)
    printf '%s\n' "$missing"
}

# Collect rows. Each row is: id|mode|synced|fresh|files|findings
ROWS=()

while IFS=$'\t' read -r id mode local_path; do
    [[ -z "$id" ]] && continue
    if [[ -n "$ONLY_REPO" && "$id" != "$ONLY_REPO" ]]; then
        continue
    fi

    synced="-"
    fresh="-"
    files="-"
    findings=""

    if [[ "$mode" == "pull" ]]; then
        dir="$SITE_DOCS/$id"
        if [[ -d "$dir" ]]; then
            synced="yes"
            files="$(find "$dir" -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')"
            recorded="$(manifest_sha "$id")"
            latest="$(sibling_docs_sha "$id" "$local_path")"
            if [[ -z "$recorded" ]]; then
                fresh="?"
                findings="no-manifest"
            elif [[ -z "$latest" ]]; then
                fresh="?"
                findings="source-unreachable"
            elif [[ "$recorded" == "$latest" ]]; then
                fresh="yes"
            else
                fresh="no"
                findings="stale-vs-source"
            fi
            missing="$(count_missing_sites "$dir")"
            if [[ "$missing" -gt 0 ]]; then
                [[ -n "$findings" ]] && findings="$findings; "
                findings="${findings}${missing} missing sites:"
            fi
        else
            synced="no"
            files="0"
            findings="not-pulled"
        fi
    fi

    ROWS+=("$id|$mode|$synced|$fresh|$files|$findings")
done < <(librarian_repos)

if [[ ${#ROWS[@]} -eq 0 ]]; then
    if [[ -n "$ONLY_REPO" ]]; then
        echo "No registry entry for repo: $ONLY_REPO" >&2
    else
        echo "No repos found in registry." >&2
    fi
    exit 0
fi

if [[ "$JSON" -eq 1 ]]; then
    # Build a JSON array with python3 from the collected rows. Rows go via
    # a tempfile passed as argv — a heredoc-driven `python3 -` would
    # otherwise consume stdin and ignore a pipe.
    ROWS_FILE="$(mktemp)"
    printf '%s\n' "${ROWS[@]}" > "$ROWS_FILE"
    python3 - "$ROWS_FILE" <<'PY'
import json, sys
out = []
with open(sys.argv[1], encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        rid, mode, synced, fresh, files, findings = line.split("|", 5)
        out.append({
            "repo": rid,
            "docs_mode": mode,
            "synced": synced,
            "fresh": fresh,
            "files": (int(files) if files.isdigit() else None),
            "findings": [f.strip() for f in findings.split(";") if f.strip()],
        })
print(json.dumps(out, indent=2))
PY
    rm -f "$ROWS_FILE"
    exit 0
fi

# Human-readable table.
printf '%-14s  %-15s  %-7s  %-6s  %-6s  %s\n' \
    "REPO" "MODE" "SYNCED" "FRESH" "FILES" "FINDINGS"
printf '%-14s  %-15s  %-7s  %-6s  %-6s  %s\n' \
    "----" "----" "------" "-----" "-----" "--------"
for row in "${ROWS[@]}"; do
    IFS='|' read -r id mode synced fresh files findings <<< "$row"
    printf '%-14s  %-15s  %-7s  %-6s  %-6s  %s\n' \
        "$id" "$mode" "$synced" "$fresh" "$files" "$findings"
done

exit 0
