#!/bin/bash
set -euo pipefail

SNAPSHOT_BASE="${DIFF_SNAPSHOT_HOME:-$HOME/.codex/diff-snapshots}"

usage() {
    echo "Usage: $0 <list|diff|restore> [args]"
}

find_snapshot() {
    local query="$1"
    if [ -f "$query" ]; then
        printf "%s\n" "$query"
        return 0
    fi
    find "$SNAPSHOT_BASE" -name "$query" -type f | head -1
}

cmd_list() {
    local repo="${1:-}"
    if [ -n "$repo" ]; then
        local workspace
        workspace=$(printf "%s" "$(realpath "$repo")" | tr '/' '_' | sed 's|^_||')
        find "$SNAPSHOT_BASE/$workspace" -name "*.snapshot" -type f 2>/dev/null | sort
        return 0
    fi
    find "$SNAPSHOT_BASE" -name "*.snapshot" -type f 2>/dev/null | sort
}

cmd_diff() {
    local snapshot_file
    snapshot_file=$(find_snapshot "$1")
    [ -n "$snapshot_file" ] || { echo "Snapshot not found: $1" >&2; exit 1; }
    local meta="${snapshot_file}.meta"
    local original_path
    original_path=$(jq -r '.original_path' "$meta")
    [ -f "$original_path" ] || { echo "Original file not found: $original_path" >&2; exit 1; }
    diff -u "$snapshot_file" "$original_path" || true
}

cmd_restore() {
    local snapshot_file
    snapshot_file=$(find_snapshot "$1")
    [ -n "$snapshot_file" ] || { echo "Snapshot not found: $1" >&2; exit 1; }
    local meta="${snapshot_file}.meta"
    local original_path
    original_path=$(jq -r '.original_path' "$meta")
    mkdir -p "$(dirname "$original_path")"
    cp "$snapshot_file" "$original_path"
    echo "Restored: $original_path"
}

[ $# -ge 1 ] || { usage; exit 1; }

case "$1" in
    list) shift; cmd_list "${1:-}" ;;
    diff) shift; cmd_diff "$1" ;;
    restore) shift; cmd_restore "$1" ;;
    *) usage; exit 1 ;;
esac
