#!/bin/bash
# Auto-experiment workspace setup
# Usage: ./setup.sh --code <path> --data <path> --workspace <path> --tag <tag>

set -e

CODE_PATH=""
DATA_PATH=""
WORKSPACE=""
TAG=""
SKILL_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --code) CODE_PATH="$2"; shift 2 ;;
        --data) DATA_PATH="$2"; shift 2 ;;
        --workspace) WORKSPACE="$2"; shift 2 ;;
        --tag) TAG="$2"; shift 2 ;;
        --skill-dir) SKILL_DIR="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 --code <path> --data <path> --workspace <path> --tag <tag>"
            echo ""
            echo "Options:"
            echo "  --code PATH        Code repository path or URL"
            echo "  --data PATH        Dataset path (will be symlinked)"
            echo "  --workspace PATH   Workspace directory to create"
            echo "  --tag TAG          Experiment tag (e.g., mar22)"
            echo "  --skill-dir DIR    Skill directory (auto-detected)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Validate inputs
if [[ -z "$CODE_PATH" || -z "$DATA_PATH" || -z "$WORKSPACE" || -z "$TAG" ]]; then
    echo "ERROR: All arguments required. Run with --help for usage."
    exit 1
fi

if [[ ! -d "$DATA_PATH" ]] && [[ ! -f "$DATA_PATH" ]]; then
    echo "ERROR: Data path does not exist: $DATA_PATH"
    exit 1
fi

if [[ -d "$WORKSPACE" ]]; then
    echo "WARNING: Workspace already exists: $WORKSPACE"
    read -p "Continue? [y/N] " confirm
    [[ "$confirm" != "y" && "$confirm" != "Y" ]] && exit 1
fi

echo "=== Setting up experiment workspace ==="
echo "Code:      $CODE_PATH"
echo "Data:      $DATA_PATH"
echo "Workspace: $WORKSPACE"
echo "Tag:       $TAG"
echo "Branch:    autoresearch/$TAG"
echo ""

# 1. Create directory structure
echo "Creating directories..."
mkdir -p "$WORKSPACE"/{outputs,logs,doc/agent,.claude/hooks,scripts}

# 2. Clone or link code
echo "Setting up code..."
if [[ "$CODE_PATH" == http* ]] || [[ "$CODE_PATH" == git@* ]]; then
    git clone "$CODE_PATH" "$WORKSPACE/code"
else
    git clone "$CODE_PATH" "$WORKSPACE/code"
fi

cd "$WORKSPACE/code"

# Check branch doesn't exist
if git show-ref --verify --quiet "refs/heads/autoresearch/$TAG" 2>/dev/null; then
    echo "ERROR: Branch autoresearch/$TAG already exists"
    exit 1
fi

git checkout -b "autoresearch/$TAG"
cd "$WORKSPACE"

# 3. Symlink data
echo "Symlinking data..."
ln -s "$(realpath "$DATA_PATH")" "$WORKSPACE/data"

# 4. Initialize tracking
echo "Initializing results tracking..."
echo -e "commit\tmetric\tmemory_gb\tstatus\tdescription" > results.tsv

# 5. Initialize context files
echo "Initializing context files..."
cat > doc/agent/sketch.md << EOF
# Experiment Sketch

## Current State
- Phase: setup
- Last action: workspace created
- Blocking issues: none

## Goal
(To be filled in Step 1)

## Baselines
| Source | Metric | Value | Notes |
|--------|--------|-------|-------|

## Approach
(To be determined in Step 3)

## Next Steps
1. [ ] Confirm inputs and understand instructions
2. [ ] Explore codebase
3. [ ] Create experiment plan

## Session Log
| Date | Summary |
|------|---------|
| $(date +%Y-%m-%d) | Workspace created |
EOF

touch doc/agent/architecture.md
touch doc/agent/findings.md

# 6. Install scripts
echo "Installing scripts..."
if [[ -d "$SKILL_DIR/templates/scripts" ]]; then
    cp "$SKILL_DIR/templates/scripts"/*.sh scripts/
    chmod +x scripts/*.sh
fi

# 7. Install hooks
echo "Installing hooks..."
if [[ -f "$SKILL_DIR/templates/hooks/restore-context.sh" ]]; then
    cp "$SKILL_DIR/templates/hooks/restore-context.sh" .claude/hooks/
    chmod +x .claude/hooks/restore-context.sh
fi

cat > .claude/settings.json << 'SETTINGS'
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/restore-context.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
SETTINGS

# 8. Summary
echo ""
echo "=== Workspace Ready ==="
echo ""
echo "Structure:"
find "$WORKSPACE" -maxdepth 2 -not -path '*/code/.git/*' -not -path '*/code/.git' | head -30 | sed "s|$WORKSPACE|.|"
echo ""
echo "Next steps:"
echo "  1. cd $WORKSPACE"
echo "  2. Fill in CLAUDE.md from template"
echo "  3. Start Claude Code in workspace"
echo ""
echo "Branch: autoresearch/$TAG"
echo "Data symlink: $(readlink data)"
