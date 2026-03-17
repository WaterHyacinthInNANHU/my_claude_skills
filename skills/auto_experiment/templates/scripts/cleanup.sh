#!/bin/bash
# Auto-experiment workspace cleanup script
# Usage: ./cleanup.sh [--dry-run] [--force] [--keep-checkpoints N] [--archive-dir DIR]

set -e

# Default settings
DRY_RUN=false
FORCE=false
KEEP_CHECKPOINTS=3
KEEP_LOGS_DAYS=30
ARCHIVE_DIR="archives"
WORKSPACE_DIR="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --keep-checkpoints)
            KEEP_CHECKPOINTS="$2"
            shift 2
            ;;
        --keep-logs-days)
            KEEP_LOGS_DAYS="$2"
            shift 2
            ;;
        --archive-dir)
            ARCHIVE_DIR="$2"
            shift 2
            ;;
        --workspace)
            WORKSPACE_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run              Show what would be deleted without deleting"
            echo "  --force                Skip confirmation prompts"
            echo "  --keep-checkpoints N   Keep last N checkpoints (default: 3)"
            echo "  --keep-logs-days N     Keep logs newer than N days (default: 30)"
            echo "  --archive-dir DIR      Archive directory (default: archives)"
            echo "  --workspace DIR        Workspace directory (default: current)"
            echo "  -h, --help             Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

cd "$WORKSPACE_DIR"

echo -e "${BLUE}=== Experiment Workspace Cleanup ===${NC}"
echo "Workspace: $(pwd)"
echo "Dry run: $DRY_RUN"
echo ""

# Safety checks
safety_check() {
    # Never run in home directory
    if [[ "$(pwd)" == "$HOME" ]]; then
        echo -e "${RED}ERROR: Cannot run cleanup in home directory${NC}"
        exit 1
    fi

    # Check for experiment workspace markers
    if [[ ! -f "results.tsv" ]] && [[ ! -d "doc/agent" ]]; then
        echo -e "${RED}ERROR: This doesn't look like an experiment workspace${NC}"
        echo "Missing results.tsv or doc/agent/"
        exit 1
    fi

    # Never touch data symlink
    if [[ -L "data" ]]; then
        echo -e "${GREEN}✓ Data symlink detected - will not be touched${NC}"
    fi

    # Never touch context files
    echo -e "${GREEN}✓ Context files (doc/agent/) will be preserved${NC}"
}

# Calculate directory size
dir_size() {
    if [[ -d "$1" ]]; then
        du -sh "$1" 2>/dev/null | cut -f1
    else
        echo "0"
    fi
}

# Archive successful experiment
archive_experiment() {
    local exp_id="$1"
    local checkpoint="$2"
    local log="$3"
    local report="$4"

    mkdir -p "$ARCHIVE_DIR"
    local archive_name="$ARCHIVE_DIR/${exp_id}_$(date +%Y%m%d).tar.gz"

    echo -e "${BLUE}Archiving experiment: $exp_id${NC}"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  [DRY RUN] Would create: $archive_name"
        echo "  Contents: $checkpoint $log $report"
    else
        tar -czf "$archive_name" \
            ${checkpoint:+$checkpoint} \
            ${log:+$log} \
            ${report:+$report} \
            2>/dev/null || true
        echo -e "${GREEN}  Created: $archive_name${NC}"
    fi
}

# Prune old checkpoints
prune_checkpoints() {
    local checkpoint_dir="outputs/checkpoints"

    if [[ ! -d "$checkpoint_dir" ]]; then
        echo "No checkpoints directory found"
        return
    fi

    echo -e "\n${YELLOW}=== Checkpoint Pruning ===${NC}"
    echo "Policy: Keep last $KEEP_CHECKPOINTS checkpoints"
    echo "Current size: $(dir_size $checkpoint_dir)"

    # Find all checkpoints, sorted by modification time (newest first)
    local checkpoints=($(ls -t "$checkpoint_dir"/*.pt "$checkpoint_dir"/*.pth "$checkpoint_dir"/*.ckpt 2>/dev/null || true))
    local total=${#checkpoints[@]}

    if [[ $total -le $KEEP_CHECKPOINTS ]]; then
        echo "Only $total checkpoints found, nothing to prune"
        return
    fi

    local to_delete=$((total - KEEP_CHECKPOINTS))
    echo "Found $total checkpoints, will delete $to_delete"

    # Files to delete (oldest ones)
    local delete_list=("${checkpoints[@]:$KEEP_CHECKPOINTS}")

    local total_size=0
    for f in "${delete_list[@]}"; do
        local size=$(du -b "$f" 2>/dev/null | cut -f1)
        total_size=$((total_size + size))
        echo "  - $f ($(du -h "$f" | cut -f1))"
    done

    echo "Total to free: $(numfmt --to=iec $total_size 2>/dev/null || echo "${total_size} bytes")"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN] Would delete ${#delete_list[@]} checkpoints${NC}"
    else
        if [[ "$FORCE" != "true" ]]; then
            read -p "Delete these checkpoints? [y/N] " confirm
            [[ "$confirm" != "y" && "$confirm" != "Y" ]] && return
        fi

        for f in "${delete_list[@]}"; do
            rm -f "$f"
            echo -e "${GREEN}  Deleted: $f${NC}"
        done
    fi
}

# Prune old logs
prune_logs() {
    local logs_dir="logs"

    if [[ ! -d "$logs_dir" ]]; then
        echo "No logs directory found"
        return
    fi

    echo -e "\n${YELLOW}=== Log Pruning ===${NC}"
    echo "Policy: Keep logs newer than $KEEP_LOGS_DAYS days"
    echo "Current size: $(dir_size $logs_dir)"

    # Find old log files
    local old_logs=($(find "$logs_dir" -name "*.log" -type f -mtime +$KEEP_LOGS_DAYS 2>/dev/null || true))

    if [[ ${#old_logs[@]} -eq 0 ]]; then
        echo "No old logs found"
        return
    fi

    echo "Found ${#old_logs[@]} logs older than $KEEP_LOGS_DAYS days:"

    local total_size=0
    for f in "${old_logs[@]}"; do
        local size=$(du -b "$f" 2>/dev/null | cut -f1)
        total_size=$((total_size + size))
        echo "  - $f ($(du -h "$f" | cut -f1))"
    done

    echo "Total to free: $(numfmt --to=iec $total_size 2>/dev/null || echo "${total_size} bytes")"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN] Would delete ${#old_logs[@]} log files${NC}"
    else
        if [[ "$FORCE" != "true" ]]; then
            read -p "Delete these logs? [y/N] " confirm
            [[ "$confirm" != "y" && "$confirm" != "Y" ]] && return
        fi

        for f in "${old_logs[@]}"; do
            rm -f "$f"
            echo -e "${GREEN}  Deleted: $f${NC}"
        done
    fi
}

# Prune failed git branches
prune_branches() {
    local code_dir="code"

    if [[ ! -d "$code_dir/.git" ]]; then
        code_dir="."
        if [[ ! -d ".git" ]]; then
            echo "No git repository found"
            return
        fi
    fi

    echo -e "\n${YELLOW}=== Git Branch Pruning ===${NC}"

    cd "$code_dir"

    # Get current branch
    local current_branch=$(git branch --show-current)
    echo "Current branch: $current_branch"

    # Find merged branches (excluding current and main/master)
    local merged_branches=($(git branch --merged | grep -v "^\*" | grep -v "main" | grep -v "master" | grep -v "$current_branch" | tr -d ' ' || true))

    if [[ ${#merged_branches[@]} -eq 0 ]]; then
        echo "No merged branches to prune"
        cd - > /dev/null
        return
    fi

    echo "Found ${#merged_branches[@]} merged branches:"
    for b in "${merged_branches[@]}"; do
        echo "  - $b"
    done

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN] Would delete ${#merged_branches[@]} branches${NC}"
    else
        if [[ "$FORCE" != "true" ]]; then
            read -p "Delete these branches? [y/N] " confirm
            [[ "$confirm" != "y" && "$confirm" != "Y" ]] && cd - > /dev/null && return
        fi

        for b in "${merged_branches[@]}"; do
            git branch -d "$b" 2>/dev/null || true
            echo -e "${GREEN}  Deleted: $b${NC}"
        done
    fi

    cd - > /dev/null
}

# Clean Python cache
clean_cache() {
    echo -e "\n${YELLOW}=== Cache Cleanup ===${NC}"

    # Find cache directories
    local cache_dirs=($(find . -type d -name "__pycache__" -o -name ".pytest_cache" -o -name "*.egg-info" 2>/dev/null || true))
    local pyc_files=($(find . -name "*.pyc" -o -name "*.pyo" 2>/dev/null || true))

    local total_items=$((${#cache_dirs[@]} + ${#pyc_files[@]}))

    if [[ $total_items -eq 0 ]]; then
        echo "No cache files found"
        return
    fi

    echo "Found ${#cache_dirs[@]} cache directories, ${#pyc_files[@]} .pyc files"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN] Would delete $total_items cache items${NC}"
    else
        if [[ "$FORCE" != "true" ]]; then
            read -p "Delete cache files? [y/N] " confirm
            [[ "$confirm" != "y" && "$confirm" != "Y" ]] && return
        fi

        for d in "${cache_dirs[@]}"; do
            rm -rf "$d"
        done
        for f in "${pyc_files[@]}"; do
            rm -f "$f"
        done
        echo -e "${GREEN}  Deleted $total_items cache items${NC}"
    fi
}

# Clean processed data (with extra caution)
clean_processed_data() {
    local processed_dir="outputs/processed_data"

    if [[ ! -d "$processed_dir" ]]; then
        return
    fi

    echo -e "\n${YELLOW}=== Processed Data Cleanup ===${NC}"
    echo -e "${RED}WARNING: This may affect reproducibility!${NC}"
    echo "Current size: $(dir_size $processed_dir)"

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${YELLOW}[DRY RUN] Would prompt to delete processed data${NC}"
        return
    fi

    if [[ "$FORCE" != "true" ]]; then
        echo "Processed data can be regenerated from source data."
        read -p "Delete processed data? [y/N] " confirm
        [[ "$confirm" != "y" && "$confirm" != "Y" ]] && return
    fi

    rm -rf "$processed_dir"/*
    echo -e "${GREEN}  Cleaned processed data${NC}"
}

# Summary
show_summary() {
    echo -e "\n${BLUE}=== Workspace Summary ===${NC}"
    echo "outputs/:     $(dir_size outputs)"
    echo "logs/:        $(dir_size logs)"
    echo "doc/agent/:   $(dir_size doc/agent)"
    echo "archives/:    $(dir_size $ARCHIVE_DIR)"
    echo ""
    echo "Total workspace: $(du -sh . 2>/dev/null | cut -f1)"
}

# Main execution
main() {
    safety_check

    echo -e "\n${BLUE}Starting cleanup...${NC}"

    prune_checkpoints
    prune_logs
    prune_branches
    clean_cache
    clean_processed_data

    show_summary

    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "\n${YELLOW}This was a dry run. No files were deleted.${NC}"
        echo "Run without --dry-run to perform actual cleanup."
    else
        echo -e "\n${GREEN}Cleanup complete!${NC}"
    fi
}

main
