#!/bin/bash
# Auto-experiment context restoration hook
# Triggered on SessionStart events

INPUT=$(cat)
SOURCE=$(echo "$INPUT" | jq -r '.source // "unknown"')
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')

# Check if we're in an experiment workspace (has doc/agent/sketch.md)
SKETCH_FILE="$CWD/doc/agent/sketch.md"

if [ -f "$SKETCH_FILE" ]; then
    echo "=== EXPERIMENT CONTEXT RESTORED ==="
    echo ""
    echo "## Current State (from sketch.md)"
    cat "$SKETCH_FILE"
    echo ""

    # Show recent git history with notes
    if [ -d "$CWD/.git" ] || [ -d "$CWD/code/.git" ]; then
        GIT_DIR="$CWD"
        [ -d "$CWD/code/.git" ] && GIT_DIR="$CWD/code"

        echo "## Recent History"
        echo '```'
        cd "$GIT_DIR" && git log --oneline -5 --show-notes 2>/dev/null || echo "No git history"
        echo '```'
        echo ""
    fi

    # Show recent results
    RESULTS_FILE="$CWD/results.tsv"
    if [ -f "$RESULTS_FILE" ]; then
        echo "## Recent Results"
        echo '```'
        tail -5 "$RESULTS_FILE" | column -t -s $'\t'
        echo '```'
        echo ""
    fi

    # Add recovery note based on source
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
    echo "**Next action:** Check sketch.md 'Next Steps' and proceed."
fi

exit 0
