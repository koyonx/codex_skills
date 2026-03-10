#!/bin/bash
set -euo pipefail

REPO="."
COMMAND=""

while [ $# -gt 0 ]; do
    case "$1" in
        --repo)
            REPO="$2"
            shift 2
            ;;
        --command)
            COMMAND="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

if ! git -C "$REPO" rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "Not a git repository: $REPO" >&2
    exit 1
fi

ROOT=$(git -C "$REPO" rev-parse --show-toplevel)
CURRENT_BRANCH=$(git -C "$ROOT" branch --show-current 2>/dev/null || true)
if [ -z "$CURRENT_BRANCH" ]; then
    echo "Could not determine current branch." >&2
    exit 1
fi

PROTECTED_BRANCHES="main master"
CONFIG_FILE="$ROOT/.branch-guard.json"
if [ -f "$CONFIG_FILE" ]; then
    CUSTOM_BRANCHES=$(jq -r '.protected_branches[]? // empty' "$CONFIG_FILE" 2>/dev/null || true)
    if [ -n "$CUSTOM_BRANCHES" ]; then
        PROTECTED_BRANCHES="$CUSTOM_BRANCHES"
    fi
fi

IS_PROTECTED="false"
for branch in $PROTECTED_BRANCHES; do
    if [ "$CURRENT_BRANCH" = "$branch" ]; then
        IS_PROTECTED="true"
        break
    fi
done

echo "Repository: $ROOT"
echo "Current branch: $CURRENT_BRANCH"
echo "Protected branches: $(printf "%s" "$PROTECTED_BRANCHES" | tr '\n' ' ')"

if [ -z "$COMMAND" ]; then
    if [ "$IS_PROTECTED" = "true" ]; then
        echo "Status: protected branch"
    else
        echo "Status: safe branch"
    fi
    exit 0
fi

IS_COMMIT="false"
IS_PUSH="false"
if echo "$COMMAND" | grep -qE '(^|[[:space:]])git([[:space:]]+[-[:alnum:]]+)*[[:space:]]+commit([[:space:]]|$)'; then
    IS_COMMIT="true"
fi
if echo "$COMMAND" | grep -qE '(^|[[:space:]])git([[:space:]]+[-[:alnum:]]+)*[[:space:]]+push([[:space:]]|$)'; then
    IS_PUSH="true"
fi

if [ "$IS_PROTECTED" = "true" ] && { [ "$IS_COMMIT" = "true" ] || [ "$IS_PUSH" = "true" ]; }; then
    echo "Blocked: '$COMMAND' targets protected branch '$CURRENT_BRANCH'." >&2
    exit 2
fi

echo "Allowed: '$COMMAND'"
