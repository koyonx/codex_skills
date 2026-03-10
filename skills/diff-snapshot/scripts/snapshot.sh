#!/bin/bash
set -euo pipefail

REPO="."
LABEL=""
USE_CHANGED="false"
declare -a TARGETS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)
            REPO="$2"
            shift 2
            ;;
        --label)
            LABEL="$2"
            shift 2
            ;;
        --changed)
            USE_CHANGED="true"
            shift
            ;;
        *)
            TARGETS+=("$1")
            shift
            ;;
    esac
done

if ! git -C "$REPO" rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "Not a git repository: $REPO" >&2
    exit 1
fi

ROOT=$(git -C "$REPO" rev-parse --show-toplevel)
WORKSPACE=$(printf "%s" "$ROOT" | tr '/' '_' | sed 's|^_||')
SNAPSHOT_BASE="${DIFF_SNAPSHOT_HOME:-$HOME/.codex/diff-snapshots}"
SNAPSHOT_DIR="$SNAPSHOT_BASE/$WORKSPACE"
mkdir -p "$SNAPSHOT_DIR"

if [ "$USE_CHANGED" = "true" ]; then
    while IFS= read -r path; do
        [ -n "$path" ] && TARGETS+=("$ROOT/$path")
    done < <(git -C "$ROOT" status --porcelain=v1 | awk '{print $2}')
fi

[ "${#TARGETS[@]}" -gt 0 ] || { echo "No files specified." >&2; exit 1; }

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
for target in "${TARGETS[@]}"; do
    [ -f "$target" ] || continue
    RESOLVED=$(realpath "$target")
    case "$RESOLVED" in
        "$ROOT"/*) ;;
        *) echo "Skipping outside repo: $target" >&2; continue ;;
    esac
    SAFE_NAME=$(printf "%s" "${RESOLVED#$ROOT/}" | tr '/' '_' | tr -cd 'a-zA-Z0-9_.-')
    SNAPSHOT_FILE="$SNAPSHOT_DIR/${TIMESTAMP}_${SAFE_NAME}.snapshot"
    cp "$RESOLVED" "$SNAPSHOT_FILE"
    jq -n \
        --arg original_path "$RESOLVED" \
        --arg label "$LABEL" \
        --arg timestamp "$TIMESTAMP" \
        '{"original_path": $original_path, "label": $label, "timestamp": $timestamp}' > "${SNAPSHOT_FILE}.meta"
    echo "$SNAPSHOT_FILE"
done
