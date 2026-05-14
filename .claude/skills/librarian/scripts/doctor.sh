#!/usr/bin/env bash
set -euo pipefail

# doctor.sh — run the librarian check-set against every `pull`-mode sibling
# repo (or just --repo <id>), comparing site/docs/<repo>/ against the
# sibling source.
#
# Checks:
#   missing-frontmatter  sibling SOURCE file lacks sites:/title:   sibling  error
#   broken-internal-link a [..](..) link in site/docs/<repo>/      sibling  error
#                        whose target file doesn't exist
#   no-h1                a sibling source doc with no `# H1`        sibling  warning
#   stale-vs-source      .katvan-pull.json sha behind sibling's     katvan   warning
#                        latest docs/ commit
#   orphaned-file        file in site/docs/<repo>/ no longer in     katvan   warning
#                        the sibling source
#   drift                site/docs/<repo>/ content diverges from    katvan   warning
#                        source beyond frontmatter injection
#
# sibling-actionable findings  -> file/update ONE dedup'd GitHub issue per
#   (repo, check-id) on agentculture/<repo>. The issue body embeds an HTML
#   comment marker `<!-- katvan-doctor: <repo>/<check-id> -->`; before
#   filing, doctor searches the repo's open issues for that marker and
#   either comments on the match or files anew.
# katvan-actionable findings   -> printed locally only, never an issue.
#
# --dry-run: detect + print everything, including which issues WOULD be
#   filed/updated — file nothing.
#
# Output: per-repo findings table + filed/updated/skipped issue URLs;
#   --json emits a structured report.
# Exit 0 if no findings, 1 if any findings.
#
# Usage:
#   doctor.sh [--repo <id>] [--dry-run] [--json]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=_repos.sh
source "$SCRIPT_DIR/_repos.sh"

REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SITE_DOCS="$REPO_ROOT/site/docs"
FRONTMATTER="$SCRIPT_DIR/_frontmatter.py"
COMMUNICATE="$REPO_ROOT/.claude/skills/communicate/scripts"

usage() {
    echo "Usage: doctor.sh [--repo <id>] [--dry-run] [--json]" >&2
    exit 2
}

ONLY_REPO=""
DRY_RUN=0
JSON=0
TODAY="$(date -u +%Y-%m-%d)"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)
            if [[ $# -lt 2 || -z "$2" ]]; then
                echo "Missing value for --repo" >&2; usage
            fi
            ONLY_REPO="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        --json)    JSON=1; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown flag: $1" >&2; usage ;;
    esac
done

# Findings accumulate as TSV lines: repo<TAB>check-id<TAB>class<TAB>severity<TAB>detail
FINDINGS_FILE="$(mktemp)"
# Issue-action log: repo<TAB>check-id<TAB>action<TAB>url-or-note
ISSUE_LOG="$(mktemp)"
cleanup() { rm -f "$FINDINGS_FILE" "$ISSUE_LOG"; }
trap cleanup EXIT

add_finding() {
    # repo check-id class severity detail
    printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" >> "$FINDINGS_FILE"
}

# Resolve a relative markdown link target the way Jekyll/just-the-docs
# would, not as a literal on-disk path. A bare `[..](page/)` or
# `[..](page.html)` link is valid if a `page/index.md` or `page.md`
# source exists — flagging those as broken auto-files false-positive
# issues on sibling repos. Returns 0 if ANY plausible source mapping
# exists on disk, 1 otherwise.
#   $1 = directory the link is relative to
#   $2 = cleaned target (no #anchor, no ?query, not external)
link_target_resolves() {
    local reldir="$1" clean="$2"
    # 1. Literal target — direct .md links and assets (images etc.).
    [[ -e "$reldir/$clean" ]] && return 0
    case "$clean" in
        */)
            # Pretty-URL directory link: <target>index.md or
            # <target without trailing slash>.md.
            local base="${clean%/}"
            [[ -e "$reldir/$clean"index.md ]] && return 0
            [[ -e "$reldir/$base.md" ]] && return 0
            ;;
        *.html)
            # .html target: the same path as .md, or <base>/index.md.
            local stem="${clean%.html}"
            [[ -e "$reldir/$stem.md" ]] && return 0
            [[ -e "$reldir/$stem/index.md" ]] && return 0
            ;;
        *.*)
            # Has some other extension (asset, .json, etc.) — only the
            # literal test above applies; nothing more to try.
            ;;
        *)
            # Extensionless target: <target>.md or <target>/index.md.
            [[ -e "$reldir/$clean.md" ]] && return 0
            [[ -e "$reldir/$clean/index.md" ]] && return 0
            ;;
    esac
    return 1
}

# Latest sibling commit sha touching docs/.
sibling_docs_sha() {
    local id="$1" local_path="$2" sha=""
    if [[ -n "$local_path" && -d "$local_path/.git" ]]; then
        sha="$(git -C "$local_path" log -1 --format=%H -- docs/ 2>/dev/null || true)"
    elif command -v gh >/dev/null 2>&1; then
        sha="$(gh api -X GET "repos/agentculture/$id/commits" \
                 -f "path=docs" -f "per_page=1" --jq '.[0].sha' 2>/dev/null || true)"
    fi
    printf '%s\n' "$sha"
}

# --- Per-repo checks --------------------------------------------------
check_repo() {
    local id="$1" local_path="$2"
    local dest="$SITE_DOCS/$id"
    local src_docs=""

    [[ -n "$local_path" && -d "$local_path/docs" ]] && src_docs="$local_path/docs"

    if [[ ! -d "$dest" ]]; then
        # Nothing pulled yet — doctor has nothing to diff. Skip silently;
        # overview.sh is the surface that reports "not-pulled".
        return 0
    fi

    # ---- sibling-actionable checks (need the source tree) ----
    if [[ -n "$src_docs" ]]; then
        # missing-frontmatter + no-h1: walk source .md files.
        while IFS= read -r -d '' f; do
            rel="${f#"$src_docs"/}"
            head_block="$(head -c 4096 "$f")"
            # missing-frontmatter: source lacks sites: AND title: in a
            # leading frontmatter block.
            has_fm=0
            if [[ "$head_block" == "---"* ]]; then has_fm=1; fi
            has_sites=0; has_title=0
            if [[ "$has_fm" -eq 1 ]]; then
                fmblock="$(awk 'NR==1&&$0=="---"{f=1;next} f&&$0=="---"{exit} f{print}' "$f")"
                printf '%s\n' "$fmblock" | grep -qE '^sites:' && has_sites=1
                printf '%s\n' "$fmblock" | grep -qE '^title:' && has_title=1
            fi
            if [[ "$has_sites" -eq 0 || "$has_title" -eq 0 ]]; then
                missing=""
                [[ "$has_sites" -eq 0 ]] && missing="sites:"
                [[ "$has_title" -eq 0 ]] && missing="${missing:+$missing,}title:"
                add_finding "$id" "missing-frontmatter" "sibling" "error" \
                    "docs/$rel lacks $missing"
            fi
            # no-h1: no `# H1` line anywhere in the body.
            if ! grep -qE '^#[[:space:]]+\S' "$f"; then
                add_finding "$id" "no-h1" "sibling" "warning" \
                    "docs/$rel has no H1 heading"
            fi
        done < <(find "$src_docs" -name '*.md' -type f -print0 2>/dev/null)
    fi

    # broken-internal-link: scan pulled files in site/docs/<repo>/ for
    # [..](relative.md) links whose target doesn't exist on disk.
    while IFS= read -r -d '' f; do
        reldir="$(dirname "$f")"
        # Extract markdown link targets; keep only relative, non-anchor,
        # non-URL ones. Links inside ```-fenced code blocks are skipped:
        # they're documentation examples, not real links, and a false
        # positive here gets auto-filed as an issue on a sibling repo.
        # awk tracks a simple in-fence toggle as it scans lines, only
        # emitting link targets from lines OUTSIDE a fence. (Residual
        # edge: an inline `code span` containing `](...)` on a non-fenced
        # line can still match — see SKILL.md known-limitation note.)
        while IFS= read -r target; do
            [[ -z "$target" ]] && continue
            case "$target" in
                http://*|https://*|mailto:*|tel:*|//*|/*) continue ;;
                \#*) continue ;;
            esac
            # Strip any #anchor and ?query before resolving.
            clean="${target%%#*}"; clean="${clean%%\?*}"
            [[ -z "$clean" ]] && continue
            # Resolve the way Jekyll would: a finding is only recorded
            # when NONE of the plausible source mappings exist (literal
            # target, pretty-URL dir -> index.md/.md, .html -> .md,
            # extensionless -> .md/index.md).
            if ! link_target_resolves "$reldir" "$clean"; then
                rel="${f#"$dest"/}"
                add_finding "$id" "broken-internal-link" "sibling" "error" \
                    "$rel -> $target (target missing)"
            fi
        done < <(awk '
            /^[[:space:]]*```/ { infence = !infence; next }
            !infence {
                line = $0
                while (match(line, /\]\([^)]+\)/)) {
                    tok = substr(line, RSTART, RLENGTH)
                    sub(/^\]\(/, "", tok); sub(/\)$/, "", tok)
                    print tok
                    line = substr(line, RSTART + RLENGTH)
                }
            }
        ' "$f" 2>/dev/null)
    done < <(find "$dest" -name '*.md' -type f -print0 2>/dev/null)

    # ---- katvan-actionable checks ----
    local manifest="$dest/.katvan-pull.json"

    # stale-vs-source: manifest sha behind the sibling's latest docs/ commit.
    if [[ -f "$manifest" ]]; then
        recorded="$(python3 -c 'import json,sys
try:
    print(json.load(open(sys.argv[1])).get("sha","") or "")
except Exception:
    print("")' "$manifest")"
        latest="$(sibling_docs_sha "$id" "$local_path")"
        if [[ -n "$recorded" && -n "$latest" && "$recorded" != "$latest" ]]; then
            add_finding "$id" "stale-vs-source" "katvan" "warning" \
                "manifest sha ${recorded:0:12} behind source ${latest:0:12}"
        fi
    else
        add_finding "$id" "stale-vs-source" "katvan" "warning" \
            "no .katvan-pull.json manifest — cannot verify freshness"
    fi

    # orphaned-file + drift: compare pulled files against the source tree.
    if [[ -n "$src_docs" ]]; then
        while IFS= read -r -d '' f; do
            rel="${f#"$dest"/}"
            [[ "$rel" == ".katvan-pull.json" ]] && continue
            srcf="$src_docs/$rel"
            if [[ ! -e "$srcf" ]]; then
                add_finding "$id" "orphaned-file" "katvan" "warning" \
                    "$rel no longer exists in $id's docs/"
                continue
            fi
            # drift: re-run the source through the same frontmatter
            # injection and compare. .md only — non-md are copied verbatim
            # so a plain byte compare suffices.
            if [[ "$rel" == *.md ]]; then
                expected="$(python3 "$FRONTMATTER" --repo "$id" --rel-path "$rel" < "$srcf" 2>/dev/null || true)"
                if [[ -n "$expected" ]] && ! printf '%s' "$expected" | cmp -s - "$f"; then
                    add_finding "$id" "drift" "katvan" "warning" \
                        "$rel diverges from source beyond frontmatter injection"
                fi
            else
                if ! cmp -s "$srcf" "$f"; then
                    add_finding "$id" "drift" "katvan" "warning" \
                        "$rel (binary/non-md) diverges from source"
                fi
            fi
        done < <(find "$dest" -type f -print0 2>/dev/null)
    fi
}

# --- Run checks across pull-mode repos --------------------------------
while IFS=$'\t' read -r id mode local_path; do
    [[ -z "$id" ]] && continue
    [[ "$mode" != "pull" ]] && continue
    if [[ -n "$ONLY_REPO" && "$id" != "$ONLY_REPO" ]]; then
        continue
    fi
    check_repo "$id" "$local_path"
done < <(librarian_repos)

# --- File / update issues for sibling-actionable findings -------------
# One issue per (repo, check-id); aggregate all findings of that check.
file_issues() {
    # Unique (repo, check-id) pairs among sibling-class findings.
    local pairs
    pairs="$(awk -F'\t' '$3=="sibling"{print $1"\t"$2}' "$FINDINGS_FILE" | sort -u)"
    [[ -z "$pairs" ]] && return 0

    # Preflight: a real (non-dry-run) issue-filing pass needs gh
    # authenticated. Without this, the dedup search below silently
    # no-ops (gh errors are swallowed), every issue looks "new", and
    # then post-issue.sh fails per-issue with a confusing error. Fail
    # fast and clearly instead.
    if [[ "$DRY_RUN" -eq 0 ]]; then
        if ! command -v gh >/dev/null 2>&1 || ! gh auth status >/dev/null 2>&1; then
            echo "error: gh not authenticated — run 'gh auth login'" >&2
            exit 2
        fi
    fi

    while IFS=$'\t' read -r repo check; do
        [[ -z "$repo" ]] && continue
        local marker="<!-- katvan-doctor: $repo/$check -->"
        # Aggregate the detail lines for this (repo, check-id).
        local details severity
        details="$(awk -F'\t' -v r="$repo" -v c="$check" \
            '$1==r && $2==c {print "- "$5}' "$FINDINGS_FILE")"
        severity="$(awk -F'\t' -v r="$repo" -v c="$check" \
            '$1==r && $2==c {print $4; exit}' "$FINDINGS_FILE")"

        # Build the issue body.
        local body_file
        body_file="$(mktemp)"
        {
            echo "$marker"
            echo
            echo "katvan's \`librarian doctor\` found \`$check\` ($severity) findings"
            echo "in \`$repo\`'s docs while syncing them into the culture.dev site"
            echo "(\`site/docs/$repo/\`):"
            echo
            echo "$details"
            echo
            echo "These are **sibling-actionable** — they need a fix in \`$repo\`'s"
            echo "own \`docs/\` tree, not in katvan. Once fixed, katvan re-pulls and"
            echo "this issue can be closed."
            echo
            echo "_Filed automatically by katvan's librarian skill. The marker above"
            echo "lets katvan dedup — re-runs comment here instead of filing anew._"
        } > "$body_file"

        # Search for an existing open issue carrying the marker.
        # NOTE: GitHub's issue search index is eventually consistent — a
        # freshly-filed issue can take seconds to become searchable. Two
        # `doctor` runs within that window can both miss the same issue
        # and double-file. This is a known, low-probability race; the
        # marker still makes later runs converge (they'll find one of the
        # duplicates once the index catches up).
        local existing_num=""
        if command -v gh >/dev/null 2>&1; then
            existing_num="$(gh issue list --repo "agentculture/$repo" \
                --state open --search "katvan-doctor: $repo/$check" \
                --json number,body 2>/dev/null \
                | python3 -c 'import json,sys
m = sys.argv[1]
try:
    data = json.load(sys.stdin)
except Exception:
    data = []
for it in data:
    if m in (it.get("body") or ""):
        print(it["number"]); break' "$marker" || true)"
        fi

        if [[ "$DRY_RUN" -eq 1 ]]; then
            if [[ -n "$existing_num" ]]; then
                printf '%s\t%s\t%s\t%s\n' "$repo" "$check" "would-update" \
                    "agentculture/$repo#$existing_num" >> "$ISSUE_LOG"
            else
                printf '%s\t%s\t%s\t%s\n' "$repo" "$check" "would-file" \
                    "agentculture/$repo (new)" >> "$ISSUE_LOG"
            fi
            rm -f "$body_file"
            continue
        fi

        if [[ -n "$existing_num" ]]; then
            # Comment "still present" on the existing issue.
            local cbody
            cbody="$(mktemp)"
            {
                echo "$marker"
                echo
                echo "Still present as of $TODAY — \`librarian doctor\` re-detected"
                echo "these \`$check\` findings in \`$repo\`'s docs:"
                echo
                echo "$details"
            } > "$cbody"
            if bash "$COMMUNICATE/post-comment.sh" --repo "agentculture/$repo" \
                    --number "$existing_num" --body-file "$cbody" >/dev/null 2>&1; then
                printf '%s\t%s\t%s\t%s\n' "$repo" "$check" "updated" \
                    "agentculture/$repo#$existing_num" >> "$ISSUE_LOG"
            else
                printf '%s\t%s\t%s\t%s\n' "$repo" "$check" "update-failed" \
                    "agentculture/$repo#$existing_num" >> "$ISSUE_LOG"
            fi
            rm -f "$cbody"
        else
            # File a new issue.
            local title="librarian doctor: $check in $repo docs (sync blocker for culture.dev)"
            local url
            if url="$(bash "$COMMUNICATE/post-issue.sh" --repo "agentculture/$repo" \
                          --title "$title" --body-file "$body_file" 2>/dev/null)"; then
                printf '%s\t%s\t%s\t%s\n' "$repo" "$check" "filed" \
                    "${url:-agentculture/$repo (new)}" >> "$ISSUE_LOG"
            else
                printf '%s\t%s\t%s\t%s\n' "$repo" "$check" "file-failed" \
                    "agentculture/$repo" >> "$ISSUE_LOG"
            fi
        fi
        rm -f "$body_file"
    done <<< "$pairs"
}

file_issues

# --- Report -----------------------------------------------------------
# Count non-empty lines. `grep -c` exits 1 on no match, so capture
# unconditionally and default to 0 — never chain `|| echo 0` (that would
# append a second value and corrupt the integer).
FINDING_COUNT="$(grep -c . "$FINDINGS_FILE" 2>/dev/null)" || FINDING_COUNT=0
[[ -z "$FINDING_COUNT" ]] && FINDING_COUNT=0

if [[ "$JSON" -eq 1 ]]; then
    python3 - "$FINDINGS_FILE" "$ISSUE_LOG" "$DRY_RUN" <<'PY'
import json, sys
findings_file, issue_log, dry = sys.argv[1:4]
findings = []
with open(findings_file, encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        repo, check, cls, sev, detail = line.split("\t", 4)
        findings.append({
            "repo": repo, "check": check, "class": cls,
            "severity": sev, "detail": detail,
        })
issues = []
with open(issue_log, encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        repo, check, action, ref = line.split("\t", 3)
        issues.append({"repo": repo, "check": check, "action": action, "ref": ref})
print(json.dumps({
    "dry_run": (dry == "1"),
    "finding_count": len(findings),
    "findings": findings,
    "issues": issues,
}, indent=2))
PY
else
    if [[ "$FINDING_COUNT" -eq 0 ]]; then
        echo "librarian doctor: no findings."
    else
        echo "librarian doctor — $FINDING_COUNT finding(s)"
        [[ "$DRY_RUN" -eq 1 ]] && echo "  (dry-run — no issues filed)"
        echo
        printf '%-12s  %-22s  %-8s  %-8s  %s\n' \
            "REPO" "CHECK" "CLASS" "SEVERITY" "DETAIL"
        printf '%-12s  %-22s  %-8s  %-8s  %s\n' \
            "----" "-----" "-----" "--------" "------"
        while IFS=$'\t' read -r repo check cls sev detail; do
            [[ -z "$repo" ]] && continue
            printf '%-12s  %-22s  %-8s  %-8s  %s\n' \
                "$repo" "$check" "$cls" "$sev" "$detail"
        done < "$FINDINGS_FILE"
        echo
        if [[ -s "$ISSUE_LOG" ]]; then
            echo "Issues:"
            while IFS=$'\t' read -r repo check action ref; do
                [[ -z "$repo" ]] && continue
                printf '  %-12s  %-22s  %-13s  %s\n' "$repo" "$check" "$action" "$ref"
            done < "$ISSUE_LOG"
        else
            echo "Issues: none (no sibling-actionable findings)."
        fi
    fi
fi

[[ "$FINDING_COUNT" -gt 0 ]] && exit 1
exit 0
