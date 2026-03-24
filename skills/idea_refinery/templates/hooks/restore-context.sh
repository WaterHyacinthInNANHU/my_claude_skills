#!/bin/bash
# Idea refinery context restoration hook
# Triggered on SessionStart events

INPUT=$(cat)
if command -v jq &>/dev/null; then
    SOURCE=$(echo "$INPUT" | jq -r '.source // "unknown"')
    CWD=$(echo "$INPUT" | jq -r '.cwd // "."')
else
    # Fallback: parse JSON with grep/sed
    SOURCE=$(echo "$INPUT" | grep -o '"source"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"source"[[:space:]]*:[[:space:]]*"//;s/"$//')
    CWD=$(echo "$INPUT" | grep -o '"cwd"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"cwd"[[:space:]]*:[[:space:]]*"//;s/"$//')
    [ -z "$SOURCE" ] && SOURCE="unknown"
    [ -z "$CWD" ] && CWD="."
fi

# Check if we're in an idea refinery workspace (has doc/agent/sketch.md with "Idea Refinery")
SKETCH_FILE="$CWD/doc/agent/sketch.md"

if [ -f "$SKETCH_FILE" ] && grep -q "Idea Refinery" "$SKETCH_FILE" 2>/dev/null; then
    echo "=== IDEA REFINERY CONTEXT RESTORED ==="
    echo ""

    # Try status.py first (compact, structured output)
    STATUS_PY="$CWD/scripts/status.py"
    if [ -f "$STATUS_PY" ] && python3 "$STATUS_PY" --cwd "$CWD" 2>/dev/null; then
        echo ""
    else
        # Fallback: manual context dump
        echo "## Current State (from sketch.md)"
        cat "$SKETCH_FILE"
        echo ""

        if [ -d "$CWD/.git" ]; then
            echo "## Current Branch"
            echo '```'
            cd "$CWD" && git branch --show-current 2>/dev/null
            echo '```'
            echo ""

            echo "## Recent History"
            echo '```'
            cd "$CWD" && git log --oneline -10 --show-notes --all 2>/dev/null || echo "No git history"
            echo '```'
            echo ""
        fi

        REFS_DB="$CWD/refs.db"
        if [ -f "$REFS_DB" ]; then
            echo "## Reference Database"
            echo '```'
            python3 "$CWD/scripts/refs.py" --db "$REFS_DB" stats 2>/dev/null || echo "refs.db exists but stats failed"
            echo '```'
            echo ""
        fi
    fi

    # Recovery note
    case "$SOURCE" in
        compact)
            echo "> Context was compacted. Review above and continue from last step."
            ;;
        resume)
            echo "> Session resumed. Review above and continue from last step."
            ;;
        clear)
            echo "> Session cleared. Review above before proceeding."
            ;;
        *)
            echo "> Session started. Review context above."
            ;;
    esac

    echo ""
    echo "**Next action:** Run \`python3 scripts/status.py\` and proceed from next step."
fi

exit 0
