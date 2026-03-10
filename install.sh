#!/usr/bin/env bash
# Install Claude Code skills from this repo
#
# Skill groups are subdirectories under skills/ (e.g. skills/papers/).
# Core skills live directly in skills/ and are always installed.
# Groups are installed on-demand with --<group> flags.
#
# Usage:
#   ./install.sh                                            # Core only
#   ./install.sh --papers --all                             # Core + all papers
#   ./install.sh --papers paper_3d__dp3 paper_3d__utonia    # Core + specific papers
#   ./install.sh --list                                     # List everything

set -euo pipefail

SKILL_DIR="${HOME}/.claude/skills"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="${SCRIPT_DIR}/skills"

mkdir -p "$SKILL_DIR"

# --- Helpers ---

# Auto-discover groups (subdirectories that contain skill subdirs with SKILL.md)
get_groups() {
    for d in "$SKILLS_ROOT"/*/; do
        [ -d "$d" ] || continue
        name=$(basename "$d")
        if ls "$d"/*/SKILL.md &>/dev/null; then
            echo "$name"
        fi
    done
}

is_group() {
    local name="$1"
    for group in $(get_groups); do
        [ "$group" = "$name" ] && return 0
    done
    return 1
}

install_core() {
    echo "Installing core skills..."
    local count=0
    for d in "$SKILLS_ROOT"/*/; do
        [ -d "$d" ] || continue
        name=$(basename "$d")
        # Skip group directories
        if ls "$d"/*/SKILL.md &>/dev/null; then
            continue
        fi
        [ -f "$d/SKILL.md" ] || continue
        cp -r "$d" "$SKILL_DIR/"
        echo "  ✓ $name"
        ((count++))
    done
    echo "  ($count core skills)"
}

install_group_skill() {
    local group="$1" name="$2"
    if [ -d "$SKILLS_ROOT/$group/$name" ]; then
        cp -r "$SKILLS_ROOT/$group/$name" "$SKILL_DIR/"
        echo "  ✓ $name"
    else
        echo "  ✗ $name (not found in skills/$group/)"
        return 1
    fi
}

install_all_in_group() {
    local group="$1"
    local group_dir="$SKILLS_ROOT/$group"
    echo "Installing all skills from '$group'..."
    local count=0
    for d in "$group_dir"/*/; do
        [ -d "$d" ] || continue
        name=$(basename "$d")
        cp -r "$d" "$SKILL_DIR/"
        echo "  ✓ $name"
        ((count++))
    done
    echo "  ($count $group skills)"
}

list_group() {
    local group="$1"
    local group_dir="$SKILLS_ROOT/$group"
    echo "[$group]"
    if [ -d "$group_dir" ] && [ "$(ls -A "$group_dir" 2>/dev/null)" ]; then
        for d in "$group_dir"/*/; do
            [ -d "$d" ] || continue
            name=$(basename "$d")
            desc=$(grep -m1 'description:' "$d/SKILL.md" 2>/dev/null | sed 's/description: //' || echo "")
            echo "  $name — $desc"
        done
    else
        echo "  (empty)"
    fi
}

list_core() {
    echo "[core]"
    for d in "$SKILLS_ROOT"/*/; do
        [ -d "$d" ] || continue
        name=$(basename "$d")
        if ls "$d"/*/SKILL.md &>/dev/null; then continue; fi
        [ -f "$d/SKILL.md" ] || continue
        desc=$(grep -m1 'description:' "$d/SKILL.md" 2>/dev/null | sed 's/description: //' || echo "")
        echo "  $name — $desc"
    done
}

list_all() {
    list_core
    for group in $(get_groups); do
        echo ""
        list_group "$group"
    done
}

update_groups() {
    for group in $(get_groups); do
        local group_dir="$SKILLS_ROOT/$group"
        local found=false
        for d in "$group_dir"/*/; do
            [ -d "$d" ] || continue
            name=$(basename "$d")
            if [ -d "$SKILL_DIR/$name" ]; then
                cp -r "$d" "$SKILL_DIR/"
                echo "  ✓ $name (updated)"
                found=true
            fi
        done
        if [ "$found" = false ]; then
            echo "  (no installed skills from '$group' to update)"
        fi
    done
}

# Get all core skill names from the repo
get_core_names() {
    for d in "$SKILLS_ROOT"/*/; do
        [ -d "$d" ] || continue
        name=$(basename "$d")
        if ls "$d"/*/SKILL.md &>/dev/null; then continue; fi
        [ -f "$d/SKILL.md" ] || continue
        echo "$name"
    done
}

# Get all skill names in a group from the repo
get_group_names() {
    local group="$1"
    for d in "$SKILLS_ROOT/$group"/*/; do
        [ -d "$d" ] || continue
        echo "$(basename "$d")"
    done
}

uninstall_skill() {
    local name="$1"
    if [ -d "$SKILL_DIR/$name" ]; then
        rm -rf "$SKILL_DIR/$name"
        echo "  ✓ $name (removed)"
    else
        echo "  - $name (not installed, skipped)"
    fi
}

uninstall_core() {
    echo "Uninstalling core skills..."
    for name in $(get_core_names); do
        uninstall_skill "$name"
    done
}

uninstall_group() {
    local group="$1"
    echo "Uninstalling all '$group' skills..."
    for name in $(get_group_names "$group"); do
        uninstall_skill "$name"
    done
}

uninstall_all() {
    uninstall_core
    for group in $(get_groups); do
        uninstall_group "$group"
    done
}

# --- Main ---

if [ $# -eq 0 ]; then
    install_core
    echo ""
    groups=$(get_groups)
    if [ -n "$groups" ]; then
        echo "Optional skill groups (not installed):"
        for group in $groups; do
            count=$(find "$SKILLS_ROOT/$group" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
            echo "  --$group --all                    Install all $count $group skills"
            echo "  --$group NAME [NAME ...]          Install specific $group skills"
        done
        echo ""
        echo "Run '$0 --list' to see all available skills."
    fi
    exit 0
fi

case "$1" in
    --list)
        shift
        if [ $# -eq 0 ]; then
            list_all
        else
            group="${1#--}"  # allow --list --papers or --list papers
            is_group "$group" && list_group "$group" || { echo "Unknown group: $group"; exit 1; }
        fi
        ;;
    --update)
        install_core
        echo "Updating installed group skills..."
        update_groups
        ;;
    --uninstall)
        shift
        if [ $# -eq 0 ]; then
            # Uninstall everything from this repo
            echo "Uninstalling all skills from this repo..."
            uninstall_all
        elif [ "$1" = "--all" ]; then
            echo "Uninstalling all skills from this repo..."
            uninstall_all
        else
            group="${1#--}"
            if is_group "$group"; then
                shift
                if [ $# -eq 0 ] || [ "$1" = "--all" ]; then
                    uninstall_group "$group"
                else
                    echo "Uninstalling selected skills..."
                    for name in "$@"; do
                        uninstall_skill "$name"
                    done
                fi
            else
                # Treat args as individual skill names
                echo "Uninstalling selected skills..."
                for name in "$@"; do
                    name="${name#--}"
                    uninstall_skill "$name"
                done
            fi
        fi
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Install:"
        echo "  (none)                          Install core skills only"
        echo "  --<group> --all                 Install core + all skills in group"
        echo "  --<group> NAME [NAME ...]       Install core + specific skills from group"
        echo "  --update                        Update core + installed group skills"
        echo ""
        echo "Uninstall:"
        echo "  --uninstall                     Uninstall all skills from this repo"
        echo "  --uninstall --<group>           Uninstall all skills in a group"
        echo "  --uninstall NAME [NAME ...]     Uninstall specific skills"
        echo ""
        echo "Info:"
        echo "  --list                          List all available skills"
        echo "  --list <group>                  List skills in a group"
        echo "  --help                          Show this help"
        echo ""
        echo "Available groups: $(get_groups | tr '\n' ' ')"
        echo ""
        echo "Examples:"
        echo "  $0                                              # Core skills only"
        echo "  $0 --papers --all                               # Core + all paper skills"
        echo "  $0 --papers paper_3d__dp3                       # Core + specific paper"
        echo "  $0 --papers paper_3d__dp3 paper_3d__utonia      # Core + multiple papers"
        echo "  $0 --list                                       # Show everything"
        echo "  $0 --update                                     # Update installed skills"
        echo "  $0 --uninstall                                  # Remove all skills"
        echo "  $0 --uninstall --papers                         # Remove all paper skills"
        echo "  $0 --uninstall paper_3d__dp3                    # Remove a specific skill"
        ;;
    --*)
        # Extract group name from --<group>
        group="${1#--}"
        shift

        if ! is_group "$group"; then
            echo "Unknown option or group: --$group"
            echo "Available groups: $(get_groups | tr '\n' ' ')"
            echo "Run '$0 --help' for usage."
            exit 1
        fi

        install_core

        if [ $# -eq 0 ] || [ "$1" = "--all" ]; then
            install_all_in_group "$group"
        else
            echo "Installing selected skills from '$group'..."
            for name in "$@"; do
                install_group_skill "$group" "$name"
            done
        fi
        ;;
    *)
        echo "Unknown option: $1 (use --help for usage)"
        exit 1
        ;;
esac

echo ""
echo "Done. Skills installed to $SKILL_DIR"
