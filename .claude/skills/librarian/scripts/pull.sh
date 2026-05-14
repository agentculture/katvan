#!/usr/bin/env bash
set -euo pipefail

# pull.sh — sync one sibling repo's docs/ tree into site/docs/<repo>/,
# injecting Jekyll frontmatter into every markdown file along the way.
#
# Source resolution:
#   * local /home/spark/git/<repo>/docs/ if the sibling is checked out
#     (default ref = current checkout; --ref reads via `git -C ... show`)
#   * else `gh api repos/agentculture/<repo>/contents/docs?ref=<ref>`
#     recursively
#
# Each `.md` file is piped through _frontmatter.py --repo <id> --rel-path
# <rel>; non-markdown files (images etc.) are copied verbatim. A manifest
# is written to site/docs/<repo>/.katvan-pull.json.
#
# pull.sh NEVER commits — it leaves changes in the working tree. Hand off
# to the cicd skill for the PR.
#
# Usage:
#   pull.sh --repo <id> [--ref <branch-or-sha>] [--dry-run] [--json]
#
# Exit codes: 0 ok / 1 user error (bad or ineligible repo) /
#             2 env error (gh not authed when remote mode is needed)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_repos.sh
source "$SCRIPT_DIR/_repos.sh"

REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SITE_DOCS="$REPO_ROOT/site/docs"
FRONTMATTER="$SCRIPT_DIR/_frontmatter.py"

usage() {
    echo "Usage: pull.sh --repo <id> [--ref <branch-or-sha>] [--dry-run] [--json]" >&2
    exit 2
}

REPO=""
REF=""
DRY_RUN=0
JSON=0

require_value() {
    if [[ $# -lt 2 || -z "$2" ]]; then
        echo "Missing value for $1" >&2; usage
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)    require_value "$@"; REPO="$2"; shift 2 ;;
        --ref)     require_value "$@"; REF="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --json)    JSON=1; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown flag: $1" >&2; usage ;;
    esac
done

[[ -z "$REPO" ]] && usage

# --- Classify and gate ------------------------------------------------
MODE="$(librarian_classify "$REPO" || true)"
case "$MODE" in
    pull)
        : ;;
    self-published)
        echo "✗ $REPO is docs_mode: self-published — it ships its own Jekyll site." >&2
        echo "  culture.dev links out to it; librarian does not pull it. Nothing to do." >&2
        exit 1 ;;
    skip)
        echo "✗ $REPO is docs_mode: skip — reference/system docs or already migrated." >&2
        echo "  librarian leaves it alone. Nothing to do." >&2
        exit 1 ;;
    unknown|*)
        echo "✗ $REPO is not in the registry (site/_data/agentculture_repos.yml)." >&2
        echo "  Add an entry with a docs_mode: key before pulling." >&2
        exit 1 ;;
esac

LOCAL_PATH="$(librarian_local_path "$REPO")"
DEST="$SITE_DOCS/$REPO"

# --- Stage the source docs into a tempdir -----------------------------
# Both local and remote modes populate $STAGE/<rel> so the rest of the
# script is source-agnostic.
STAGE="$(mktemp -d -t librarian-pull-"$REPO".XXXXXX)"
cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

SOURCE_KIND=""
RESOLVED_REF=""
# Count of source files that failed to stage (git show / curl / gh api).
# Any non-zero value makes the pull "partial": the manifest is stamped,
# a loud warning prints, and the script exits non-zero.
STAGE_FAILURES=0

if [[ -n "$LOCAL_PATH" && -d "$LOCAL_PATH/.git" ]]; then
    SOURCE_KIND="local"
    if [[ ! -d "$LOCAL_PATH/docs" ]] && [[ -z "$REF" ]]; then
        echo "✗ $LOCAL_PATH/docs does not exist — nothing to pull." >&2
        exit 1
    fi
    if [[ -n "$REF" ]]; then
        RESOLVED_REF="$(git -C "$LOCAL_PATH" rev-parse --verify "$REF" 2>/dev/null || true)"
        if [[ -z "$RESOLVED_REF" ]]; then
            echo "✗ ref '$REF' not found in $LOCAL_PATH" >&2
            exit 1
        fi
        # Enumerate docs/ files at that ref and extract each via git show.
        while IFS= read -r path; do
            [[ -z "$path" ]] && continue
            rel="${path#docs/}"
            mkdir -p "$STAGE/$(dirname "$rel")"
            if ! git -C "$LOCAL_PATH" show "$RESOLVED_REF:$path" > "$STAGE/$rel" 2>/dev/null; then
                echo "  warn: could not extract $path@$REF" >&2
                rm -f "$STAGE/$rel"
                STAGE_FAILURES=$((STAGE_FAILURES + 1))
            fi
        done < <(git -C "$LOCAL_PATH" ls-tree -r --name-only "$RESOLVED_REF" -- docs/ 2>/dev/null)
    else
        RESOLVED_REF="$(git -C "$LOCAL_PATH" rev-parse HEAD 2>/dev/null || echo "working-tree")"
        # Copy the working-tree docs/ verbatim.
        if [[ -d "$LOCAL_PATH/docs" ]]; then
            ( cd "$LOCAL_PATH/docs" && find . -type f -print0 ) \
                | while IFS= read -r -d '' rel; do
                    rel="${rel#./}"
                    mkdir -p "$STAGE/$(dirname "$rel")"
                    cp "$LOCAL_PATH/docs/$rel" "$STAGE/$rel"
                done
        fi
    fi
else
    SOURCE_KIND="remote"
    if ! command -v gh >/dev/null 2>&1; then
        echo "✗ $REPO is not checked out under $LIBRARIAN_SIBLINGS_ROOT and gh is not on PATH." >&2
        echo "  Install gh + authenticate, or check the sibling repo out locally." >&2
        exit 2
    fi
    if ! gh auth status >/dev/null 2>&1; then
        echo "✗ $REPO needs remote fetch but gh is not authenticated (gh auth login)." >&2
        exit 2
    fi
    API_REF="${REF:-}"
    REF_QS=""
    [[ -n "$API_REF" ]] && REF_QS="?ref=$API_REF"
    # Resolve the commit sha for the manifest: latest commit touching docs/.
    # -X GET keeps -f params in the query string (a bare -f forces POST).
    COMMITS_ARGS=(api -X GET "repos/agentculture/$REPO/commits"
                  -f "path=docs" -f "per_page=1")
    [[ -n "$API_REF" ]] && COMMITS_ARGS+=(-f "sha=$API_REF")
    RESOLVED_REF="$(gh "${COMMITS_ARGS[@]}" --jq '.[0].sha' 2>/dev/null || true)"
    [[ -z "$RESOLVED_REF" ]] && RESOLVED_REF="${API_REF:-HEAD}"
    # Recursively walk docs/ via the contents API.
    remote_walk() {
        local subpath="$1"
        local listing
        listing="$(gh api "repos/agentculture/$REPO/contents/${subpath}${REF_QS}" 2>/dev/null || true)"
        [[ -z "$listing" ]] && return 0
        # Each entry: type + path + download_url.
        while IFS=$'\t' read -r etype epath edl; do
            [[ -z "$etype" ]] && continue
            if [[ "$etype" == "dir" ]]; then
                remote_walk "$epath"
            elif [[ "$etype" == "file" ]]; then
                rel="${epath#docs/}"
                mkdir -p "$STAGE/$(dirname "$rel")"
                if [[ -n "$edl" && "$edl" != "null" ]]; then
                    if ! curl -fsSL "$edl" -o "$STAGE/$rel" 2>/dev/null; then
                        echo "  warn: could not download $epath" >&2
                        rm -f "$STAGE/$rel"
                        STAGE_FAILURES=$((STAGE_FAILURES + 1))
                    fi
                else
                    if ! gh api "repos/agentculture/$REPO/contents/${epath}${REF_QS}" \
                            --jq '.content' 2>/dev/null | base64 -d > "$STAGE/$rel"; then
                        echo "  warn: could not fetch $epath" >&2
                        rm -f "$STAGE/$rel"
                        STAGE_FAILURES=$((STAGE_FAILURES + 1))
                    fi
                fi
            fi
        done < <(printf '%s' "$listing" \
                   | python3 -c 'import json,sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = []
if isinstance(data, dict):
    data = [data]
for e in data:
    print("\t".join([e.get("type",""), e.get("path",""), e.get("download_url") or ""]))')
    }
    remote_walk "docs"
fi

# --- Compute plan: adds / updates / removes ---------------------------
# Source files (relative paths under docs/).
mapfile -t SRC_FILES < <(cd "$STAGE" && find . -type f -print 2>/dev/null | sed 's|^\./||' | sort)

if [[ ${#SRC_FILES[@]} -eq 0 ]]; then
    # No files staged. If that's because every source file failed to
    # stage (vs. the source genuinely having no docs), it's a partial /
    # failed pull — exit 2 (env/transient), not 1 (user error).
    if [[ "$STAGE_FAILURES" -gt 0 ]]; then
        echo "✗ pull FAILED — all $STAGE_FAILURES source file(s) failed to stage." >&2
        echo "  Nothing was written. Re-run once the source is reachable." >&2
        exit 2
    fi
    echo "✗ no files found under $REPO's docs/ (ref: ${REF:-default}). Nothing to pull." >&2
    exit 1
fi

# Existing destination files (excluding the manifest itself).
EXISTING=()
if [[ -d "$DEST" ]]; then
    mapfile -t EXISTING < <(cd "$DEST" && find . -type f -print 2>/dev/null \
        | sed 's|^\./||' | grep -v '^\.katvan-pull\.json$' | sort)
fi

ADDS=()
UPDATES=()
for rel in "${SRC_FILES[@]}"; do
    if [[ -f "$DEST/$rel" ]]; then
        UPDATES+=("$rel")
    else
        ADDS+=("$rel")
    fi
done

REMOVES=()
for rel in "${EXISTING[@]:-}"; do
    [[ -z "$rel" ]] && continue
    found=0
    for s in "${SRC_FILES[@]}"; do
        [[ "$s" == "$rel" ]] && { found=1; break; }
    done
    [[ "$found" -eq 0 ]] && REMOVES+=("$rel")
done

# Emit a JSON report. Plan arrays are passed via newline-delimited
# tempfiles so we never have to splice bash arrays into a python heredoc.
emit_json_report() {
    local dry="$1"
    local adds_f updates_f removes_f
    adds_f="$(mktemp)"; updates_f="$(mktemp)"; removes_f="$(mktemp)"
    printf '%s\n' "${ADDS[@]:-}"    | grep -v '^$' > "$adds_f"    || true
    printf '%s\n' "${UPDATES[@]:-}" | grep -v '^$' > "$updates_f" || true
    printf '%s\n' "${REMOVES[@]:-}" | grep -v '^$' > "$removes_f" || true
    python3 - "$REPO" "${REF:-default}" "$RESOLVED_REF" "$SOURCE_KIND" \
              "$DEST" "$dry" "$adds_f" "$updates_f" "$removes_f" <<'PY'
import json, sys
repo, ref, sha, kind, dest, dry, adds_f, updates_f, removes_f = sys.argv[1:10]
def load(path):
    with open(path, encoding="utf-8") as fh:
        return [l.rstrip("\n") for l in fh if l.strip()]
print(json.dumps({
    "repo": repo,
    "ref": ref,
    "sha": sha,
    "source": kind,
    "dest": dest,
    "dry_run": (dry == "1"),
    "adds": load(adds_f),
    "updates": load(updates_f),
    "removes": load(removes_f),
}, indent=2))
PY
    rm -f "$adds_f" "$updates_f" "$removes_f"
}

# --- Dry-run: report the plan, write nothing --------------------------
if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ "$JSON" -eq 1 ]]; then
        emit_json_report 1
    else
        echo "Pull plan for $REPO (source: $SOURCE_KIND, ref: ${REF:-default}, sha: ${RESOLVED_REF:0:12})"
        echo "  dry-run — nothing will be written."
        echo
        echo "  ADD     (${#ADDS[@]}):"
        for f in "${ADDS[@]:-}"; do [[ -n "$f" ]] && echo "    + $f"; done
        echo "  UPDATE  (${#UPDATES[@]}):"
        for f in "${UPDATES[@]:-}"; do [[ -n "$f" ]] && echo "    ~ $f"; done
        echo "  REMOVE  (${#REMOVES[@]}):"
        for f in "${REMOVES[@]:-}"; do [[ -n "$f" ]] && echo "    - $f"; done
    fi
    exit 0
fi

# --- Apply: write files + manifest ------------------------------------
mkdir -p "$DEST"

# Remove orphaned destination files first.
for rel in "${REMOVES[@]:-}"; do
    [[ -z "$rel" ]] && continue
    rm -f "$DEST/$rel"
done

# Write each source file. .md -> through _frontmatter.py; everything else
# verbatim. Record source sha256 for the manifest.
MANIFEST_ENTRIES=()
for rel in "${SRC_FILES[@]}"; do
    src="$STAGE/$rel"
    dst="$DEST/$rel"
    mkdir -p "$(dirname "$dst")"
    sha256="$(python3 -c 'import hashlib,sys
with open(sys.argv[1],"rb") as f: print(hashlib.sha256(f.read()).hexdigest())' "$src")"
    if [[ "$rel" == *.md ]]; then
        python3 "$FRONTMATTER" --repo "$REPO" --rel-path "$rel" < "$src" > "$dst"
    else
        cp "$src" "$dst"
    fi
    MANIFEST_ENTRIES+=("$rel"$'\t'"$sha256")
done

# Write site/docs/<repo>/.katvan-pull.json. The entry list goes via a
# tempfile passed as argv — a heredoc-driven `python3 -` consumes stdin
# for the heredoc, so a piped-in entry list would be silently dropped.
MANIFEST="$DEST/.katvan-pull.json"
ENTRIES_FILE="$(mktemp)"
printf '%s\n' "${MANIFEST_ENTRIES[@]}" > "$ENTRIES_FILE"
python3 - "$REPO" "${REF:-default}" "$RESOLVED_REF" "$MANIFEST" "$ENTRIES_FILE" "$STAGE_FAILURES" <<'PY'
import json, sys, datetime
repo, ref, sha, manifest_path, entries_path, stage_failures = sys.argv[1:7]
files = []
with open(entries_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        path, digest = line.split("\t", 1)
        files.append({"path": path, "source_sha256": digest})
files.sort(key=lambda e: e["path"])
doc = {
    "repo": repo,
    "ref": ref,
    "sha": sha,
    "pulled_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    # A partial pull (one or more source files failed to stage) is an
    # incomplete sync — flag it so downstream tooling and humans don't
    # mistake it for a clean snapshot. False on a clean pull.
    "partial": int(stage_failures) > 0,
    "files": files,
}
with open(manifest_path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
rm -f "$ENTRIES_FILE"

# --- Report -----------------------------------------------------------
if [[ "$JSON" -eq 1 ]]; then
    emit_json_report 0
else
    echo "Pulled $REPO docs into $DEST"
    echo "  source: $SOURCE_KIND   ref: ${REF:-default}   sha: ${RESOLVED_REF:0:12}"
    echo "  added:   ${#ADDS[@]}"
    echo "  updated: ${#UPDATES[@]}"
    echo "  removed: ${#REMOVES[@]}"
    echo "  manifest: $MANIFEST"
    echo
    echo "Changes are in the working tree — pull.sh never commits."
    echo "Hand off to the cicd skill to open the PR."
fi

# A partial pull is a silently-incomplete sync if we let it exit 0 — so
# warn loudly and exit 2 (environment/transient error). The manifest
# already carries "partial": true.
if [[ "$STAGE_FAILURES" -gt 0 ]]; then
    echo >&2
    echo "WARNING: pull was PARTIAL — $STAGE_FAILURES file(s) failed to stage." >&2
    echo "  The manifest is stamped \"partial\": true. Re-run the pull once the" >&2
    echo "  source is reachable; do not treat this sync as complete." >&2
    exit 2
fi

exit 0
