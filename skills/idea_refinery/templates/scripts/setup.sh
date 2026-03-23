#!/bin/bash
# Idea Refinery workspace setup script
set -euo pipefail

usage() {
    echo "Usage: $0 --workspace <path> --tag <name> [--idea <text>]"
    echo ""
    echo "Options:"
    echo "  --workspace   Path for the idea workspace"
    echo "  --tag         Short identifier (e.g., 3d-vla-robust)"
    echo "  --idea        Seed idea text (optional, can fill later)"
    exit 1
}

WORKSPACE=""
TAG=""
IDEA=""
DATE=$(date +%Y-%m-%d)
SKILL_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace) WORKSPACE="$2"; shift 2 ;;
        --tag) TAG="$2"; shift 2 ;;
        --idea) IDEA="$2"; shift 2 ;;
        *) usage ;;
    esac
done

[[ -z "$WORKSPACE" || -z "$TAG" ]] && usage

echo "=== Setting up Idea Refinery workspace ==="
echo "Workspace: $WORKSPACE"
echo "Tag: $TAG"

# Create directory structure
mkdir -p "$WORKSPACE"/{doc/agent/{idea_versions,directions,validations},doc/proposals,.claude/hooks}

# Initialize git
cd "$WORKSPACE"
if [ ! -d .git ]; then
    git init
    echo "Initialized git repo"
fi

# Create main branch
git checkout -b "ideate/$TAG" 2>/dev/null || git checkout "ideate/$TAG" 2>/dev/null || true

# Helper: safe template substitution using awk (handles special chars in IDEA)
fill_template() {
    local src="$1"
    local dest="$2"
    awk \
        -v tag="$TAG" \
        -v date="$DATE" \
        -v idea="$IDEA" \
        '{
            gsub(/\{\{TAG\}\}/, tag)
            gsub(/\{\{DATE\}\}/, date)
            gsub(/\{\{IDEA\}\}/, idea)
            gsub(/\{\{TOPIC\}\}/, "")
            gsub(/\{\{GOAL\}\}/, "")
            gsub(/\{\{COMPUTE\}\}/, "")
            gsub(/\{\{DEADLINE\}\}/, "")
            gsub(/\{\{DATA\}\}/, "")
            gsub(/\{\{TEAM\}\}/, "")
            print
        }' "$src" > "$dest"
}

# Install context files from templates
for tmpl in sketch survey_cache findings decisions; do
    SRC="$SKILL_DIR/templates/${tmpl}.md.template"
    case $tmpl in
        sketch)       DEST="doc/agent/sketch.md" ;;
        survey_cache) DEST="doc/agent/survey_cache.md" ;;
        findings)     DEST="doc/agent/findings.md" ;;
        decisions)    DEST="doc/agent/decisions.md" ;;
    esac
    if [ -f "$SRC" ]; then
        fill_template "$SRC" "$DEST"
        echo "Created $DEST"
    fi
done

# Install seed idea card
CARD_SRC="$SKILL_DIR/templates/idea_card.md.template"
if [ -f "$CARD_SRC" ]; then
    awk \
        -v tag="$TAG" \
        -v date="$DATE" \
        -v idea="$IDEA" \
        '{
            gsub(/\{\{VERSION\}\}/, "0")
            gsub(/\{\{PARENT_VERSION\}\}/, "none")
            gsub(/\{\{DIRECTION\}\}/, "seed")
            gsub(/\{\{DATE\}\}/, date)
            gsub(/\{\{TAG\}\}/, tag)
            gsub(/\{\{DESCRIPTION\}\}/, idea)
            gsub(/\{\{DELTA\}\}/, "Initial seed idea")
            print
        }' "$CARD_SRC" > "doc/agent/idea_versions/v0_seed.md"
    echo "Created doc/agent/idea_versions/v0_seed.md"
fi

# Install hooks
cp "$SKILL_DIR/templates/hooks/restore-context.sh" .claude/hooks/
chmod +x .claude/hooks/restore-context.sh
cp "$SKILL_DIR/templates/hooks/settings.json" .claude/settings.json
echo "Installed session hooks"

# Install CLAUDE.md
if [ -f "$SKILL_DIR/templates/CLAUDE.md.template" ]; then
    awk \
        -v tag="$TAG" \
        -v idea="$IDEA" \
        -v date="$DATE" \
        '{
            gsub(/\{\{TAG\}\}/, tag)
            gsub(/\{\{IDEA\}\}/, idea)
            gsub(/\{\{DATE\}\}/, date)
            print
        }' "$SKILL_DIR/templates/CLAUDE.md.template" > CLAUDE.md
    echo "Created CLAUDE.md"
fi

# Initial commit
git add -A
git commit -m "ideate/$TAG: workspace setup"

echo ""
echo "=== Workspace ready ==="
echo "  cd $WORKSPACE"
echo "  Branch: ideate/$TAG"
echo ""
echo "Context files:"
echo "  doc/agent/sketch.md          — Current state"
echo "  doc/agent/survey_cache.md    — Paper cache"
echo "  doc/agent/idea_versions/     — Idea card per version"
echo "  doc/agent/directions/        — Direction evaluation reports"
echo "  doc/agent/validations/       — Validation reports"
echo "  doc/agent/findings.md        — Accumulated insights"
echo "  doc/agent/decisions.md       — Decision log"
echo "  doc/proposals/               — Final output documents"
