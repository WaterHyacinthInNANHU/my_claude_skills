#!/bin/bash
# Idea refinery context restoration hook
# Triggered on SessionStart events

INPUT=$(cat)
SOURCE=$(echo "$INPUT" | jq -r '.source // "unknown"')
CWD=$(echo "$INPUT" | jq -r '.cwd // "."')

# Check if we're in an idea refinery workspace (has doc/agent/sketch.md with "Idea Refinery")
SKETCH_FILE="$CWD/doc/agent/sketch.md"

if [ -f "$SKETCH_FILE" ] && grep -q "Idea Refinery" "$SKETCH_FILE" 2>/dev/null; then
    echo "=== IDEA REFINERY CONTEXT RESTORED ==="
    echo ""
    echo "## Current State (from sketch.md)"
    cat "$SKETCH_FILE"
    echo ""

    # Show current branch and recent git history
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

        # Show all idea branches
        echo "## Idea Branches"
        echo '```'
        cd "$CWD" && git branch -a 2>/dev/null | grep "ideate/" || echo "No idea branches yet"
        echo '```'
        echo ""
    fi

    # Show current best idea card
    BEST_VERSION=$(ls -t "$CWD/doc/agent/idea_versions/" 2>/dev/null | head -1)
    if [ -n "$BEST_VERSION" ]; then
        echo "## Latest Idea Version"
        cat "$CWD/doc/agent/idea_versions/$BEST_VERSION"
        echo ""
    fi

    # Show survey cache stats (count rows starting with "| <number>")
    CACHE_FILE="$CWD/doc/agent/survey_cache.md"
    if [ -f "$CACHE_FILE" ]; then
        PAPER_COUNT=$(grep -cE "^\| [0-9]" "$CACHE_FILE" 2>/dev/null || echo "0")
        echo "## Survey Cache: $PAPER_COUNT papers"
        echo ""
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
    echo "**Next action:** Check sketch.md 'Next Steps' and proceed."
fi

exit 0
