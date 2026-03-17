#!/bin/bash
# Archive a successful experiment
# Usage: ./archive-experiment.sh <exp_id> [--include-all-checkpoints]

set -e

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <exp_id> [--include-all-checkpoints]"
    echo ""
    echo "Archives an experiment with:"
    echo "  - Best/final checkpoint"
    echo "  - Training log"
    echo "  - Experiment report"
    echo "  - Git commit info and notes"
    echo ""
    echo "Options:"
    echo "  --include-all-checkpoints  Include all checkpoints (large!)"
    exit 1
fi

EXP_ID="$1"
INCLUDE_ALL_CHECKPOINTS=false
ARCHIVE_DIR="archives"

if [[ "$2" == "--include-all-checkpoints" ]]; then
    INCLUDE_ALL_CHECKPOINTS=true
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Archiving Experiment: $EXP_ID ===${NC}"

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

# Create temp directory for archive contents
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

ARCHIVE_CONTENT="$TEMP_DIR/$EXP_ID"
mkdir -p "$ARCHIVE_CONTENT"

# 1. Copy experiment report
if [[ -f "doc/agent/exp_${EXP_ID}.md" ]]; then
    cp "doc/agent/exp_${EXP_ID}.md" "$ARCHIVE_CONTENT/report.md"
    echo "✓ Copied experiment report"
elif [[ -f "doc/agent/${EXP_ID}_report.md" ]]; then
    cp "doc/agent/${EXP_ID}_report.md" "$ARCHIVE_CONTENT/report.md"
    echo "✓ Copied experiment report"
else
    echo "⚠ No experiment report found"
fi

# 2. Copy training log
if [[ -f "logs/${EXP_ID}.log" ]]; then
    cp "logs/${EXP_ID}.log" "$ARCHIVE_CONTENT/train.log"
    echo "✓ Copied training log"
elif [[ -f "logs/train.log" ]]; then
    cp "logs/train.log" "$ARCHIVE_CONTENT/train.log"
    echo "✓ Copied training log (generic)"
else
    echo "⚠ No training log found"
fi

# 3. Copy checkpoints
if [[ "$INCLUDE_ALL_CHECKPOINTS" == "true" ]]; then
    if [[ -d "outputs/checkpoints" ]]; then
        mkdir -p "$ARCHIVE_CONTENT/checkpoints"
        cp outputs/checkpoints/*.pt "$ARCHIVE_CONTENT/checkpoints/" 2>/dev/null || true
        cp outputs/checkpoints/*.pth "$ARCHIVE_CONTENT/checkpoints/" 2>/dev/null || true
        cp outputs/checkpoints/*.ckpt "$ARCHIVE_CONTENT/checkpoints/" 2>/dev/null || true
        echo "✓ Copied all checkpoints"
    fi
else
    # Copy only best/final checkpoint
    for pattern in "best" "final" "last"; do
        for ext in "pt" "pth" "ckpt"; do
            if [[ -f "outputs/checkpoints/${pattern}.${ext}" ]]; then
                cp "outputs/checkpoints/${pattern}.${ext}" "$ARCHIVE_CONTENT/"
                echo "✓ Copied ${pattern}.${ext}"
            elif [[ -f "outputs/checkpoints/${pattern}_checkpoint.${ext}" ]]; then
                cp "outputs/checkpoints/${pattern}_checkpoint.${ext}" "$ARCHIVE_CONTENT/"
                echo "✓ Copied ${pattern}_checkpoint.${ext}"
            fi
        done
    done

    # If no best/final found, copy the newest checkpoint
    newest=$(ls -t outputs/checkpoints/*.pt outputs/checkpoints/*.pth outputs/checkpoints/*.ckpt 2>/dev/null | head -1)
    if [[ -n "$newest" ]] && [[ ! -f "$ARCHIVE_CONTENT/"*.pt ]] && [[ ! -f "$ARCHIVE_CONTENT/"*.pth ]]; then
        cp "$newest" "$ARCHIVE_CONTENT/"
        echo "✓ Copied newest checkpoint: $(basename $newest)"
    fi
fi

# 4. Extract relevant results from results.tsv
if [[ -f "results.tsv" ]]; then
    head -1 results.tsv > "$ARCHIVE_CONTENT/results.tsv"
    grep -i "$EXP_ID" results.tsv >> "$ARCHIVE_CONTENT/results.tsv" 2>/dev/null || true
    echo "✓ Copied relevant results"
fi

# 5. Save git info
GIT_DIR="."
[[ -d "code/.git" ]] && GIT_DIR="code"

(
    cd "$GIT_DIR"
    echo "# Git Info for $EXP_ID"
    echo ""
    echo "## Commit"
    git log --oneline -1 2>/dev/null || echo "N/A"
    echo ""
    echo "## Full Commit Info"
    git log -1 2>/dev/null || echo "N/A"
    echo ""
    echo "## Git Notes"
    git notes show HEAD 2>/dev/null || echo "No notes"
    echo ""
    echo "## Branch"
    git branch --show-current 2>/dev/null || echo "N/A"
) > "$ARCHIVE_CONTENT/git_info.txt"
echo "✓ Saved git info"

# 6. Copy config if exists
for config in "config.yaml" "config.json" "config.py" "configs/default.yaml"; do
    if [[ -f "$config" ]]; then
        cp "$config" "$ARCHIVE_CONTENT/"
        echo "✓ Copied config: $config"
        break
    fi
done

# 7. Create archive manifest
cat > "$ARCHIVE_CONTENT/MANIFEST.md" << EOF
# Archive: $EXP_ID

**Created:** $(date -Iseconds)
**Workspace:** $(pwd)
**Branch:** $(cd "$GIT_DIR" && git branch --show-current 2>/dev/null || echo "N/A")
**Commit:** $(cd "$GIT_DIR" && git rev-parse --short HEAD 2>/dev/null || echo "N/A")

## Contents

$(ls -la "$ARCHIVE_CONTENT" | tail -n +2)

## How to Restore

\`\`\`bash
# Extract archive
tar -xzf ${EXP_ID}_$(date +%Y%m%d).tar.gz

# Restore checkpoint
cp ${EXP_ID}/best.pt outputs/checkpoints/

# View report
cat ${EXP_ID}/report.md
\`\`\`
EOF
echo "✓ Created manifest"

# 8. Create the archive
ARCHIVE_NAME="$ARCHIVE_DIR/${EXP_ID}_$(date +%Y%m%d).tar.gz"
tar -czf "$ARCHIVE_NAME" -C "$TEMP_DIR" "$EXP_ID"

ARCHIVE_SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)
echo ""
echo -e "${GREEN}=== Archive Created ===${NC}"
echo "Location: $ARCHIVE_NAME"
echo "Size: $ARCHIVE_SIZE"
echo ""
echo "Contents:"
tar -tzf "$ARCHIVE_NAME" | head -20
