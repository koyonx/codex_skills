#!/bin/bash
set -euo pipefail

THRESHOLD="${AUTO_COMMIT_THRESHOLD:-5}"
REPO="."

while [ $# -gt 0 ]; do
    case "$1" in
        --threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        --repo)
            REPO="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

if ! echo "$THRESHOLD" | grep -Eq '^[0-9]+$'; then
    echo "Threshold must be a non-negative integer." >&2
    exit 1
fi

if ! git -C "$REPO" rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "Not a git repository: $REPO" >&2
    exit 1
fi

ROOT=$(git -C "$REPO" rev-parse --show-toplevel)
STATUS=$(git -C "$ROOT" status --porcelain=v1)
TOTAL=$(printf "%s\n" "$STATUS" | sed '/^$/d' | wc -l | tr -d ' ')
STAGED=$(printf "%s\n" "$STATUS" | awk 'substr($0,1,1)!=" " && substr($0,1,1)!="?"' | sed '/^$/d' | wc -l | tr -d ' ')
UNTRACKED=$(printf "%s\n" "$STATUS" | awk 'substr($0,1,2)=="??"' | sed '/^$/d' | wc -l | tr -d ' ')

echo "Repository: $ROOT"
echo "Threshold: $THRESHOLD"
echo "Changed entries: $TOTAL"
echo "Staged entries: $STAGED"
echo "Untracked entries: $UNTRACKED"
echo ""

if [ "$TOTAL" -eq 0 ]; then
    echo "Working tree is clean."
    exit 0
fi

echo "Top changed paths:"
printf "%s\n" "$STATUS" | sed '/^$/d' | head -10 | sed 's/^/  /'
echo ""

if [ "$TOTAL" -ge "$THRESHOLD" ]; then
    echo "Suggestion: create a checkpoint commit now."
    exit 0
fi

echo "Suggestion: keep working, or stage related files before committing."
