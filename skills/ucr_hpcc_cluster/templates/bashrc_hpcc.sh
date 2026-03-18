# ============================================================================
# UCR HPCC Cluster Aliases and Functions
# Add this to your ~/.bashrc: source /path/to/bashrc_hpcc.sh
# Or append the contents directly to ~/.bashrc
# ============================================================================

# ── Interactive Sessions ──────────────────────────────────────────────────

# Launch Claude Code in an interactive SLURM session
# Usage: ccn [hours]
# Examples: ccn (2h), ccn 4 (4h), ccn 24 (24h)
ccn() {
    local hours="${1:-2}"
    local dir="$(pwd)"
    local partition="short"

    if (( hours > 2 )); then
        partition="epyc"
    fi

    echo "Launching Claude Code on $partition partition (${hours}h, 16GB RAM)..."
    echo "Working directory: $dir"
    echo "To exit: type 'exit' or press Ctrl+D"
    echo ""

    srun -p "$partition" -c 4 --mem=16GB -t "${hours}:00:00" --pty bash -c "cd '$dir' && claude --dangerously-skip-permissions"
}

# Launch VS Code tunnel in an interactive SLURM session
# Usage: vsc [hours]
# Examples: vsc (2h), vsc 5 (5h), vsc 24 (24h)
vsc() {
    local hours="${1:-2}"
    local partition="short"

    if (( hours > 2 )); then
        partition="epyc"
    fi

    echo "Launching VS Code tunnel on $partition partition (${hours}h)..."
    echo "After authorization, connect via:"
    echo "  - Browser: https://vscode.dev/tunnel/<tunnel-name>"
    echo "  - Desktop: Click green '><' icon -> Connect to Tunnel"
    echo "To exit: Ctrl+C to stop tunnel, then 'exit'"
    echo ""

    srun -p "$partition" -c 32 --mem=64GB -t "${hours}:00:00" --pty bash -c "module load vscode && code tunnel"
}

# Quick interactive session
# Usage: node [hours] [partition]
# Examples: node (2h short), node 4 (4h epyc), node 4 gpu (4h gpu)
node() {
    local hours="${1:-2}"
    local partition="${2:-}"

    if [[ -z "$partition" ]]; then
        if (( hours > 2 )); then
            partition="epyc"
        else
            partition="short"
        fi
    fi

    echo "Starting interactive session on $partition (${hours}h)..."
    srun -p "$partition" -c 4 --mem=16GB -t "${hours}:00:00" --pty bash -l
}

# GPU interactive session
# Usage: gpunode [hours]
# Examples: gpunode (1h), gpunode 4 (4h)
gpunode() {
    local hours="${1:-1}"
    echo "Starting GPU interactive session (${hours}h)..."
    srun -p gpu --gres=gpu:1 -c 8 --mem=32GB -t "${hours}:00:00" --pty bash -l
}

# ── Job Monitoring ─────────────────────────────────────────────────────────

# Show my running/pending jobs
alias sq='squeue -u $USER -o "%.10i %.12j %.10P %.8T %.10M %.10l %.6C %.10m %R" --sort=-S'

# Show my jobs with start time estimates
alias sqstart='squeue -u $USER --start -o "%.10i %.12j %.10P %.8T %.19S %.10l %R"'

# Watch jobs (refresh every 5s)
alias sqwatch='watch -n 5 "squeue -u $USER -o \"%.10i %.12j %.10P %.8T %.10M %.10l %.6C %.10m %R\" --sort=-S"'

# Show all GPU jobs in the cluster
alias sqgpu='squeue -p gpu,short_gpu,preempt_gpu -o "%.10i %.12j %.10P %.8u %.8T %.10M %.10l %b %R"'

# Show my recent job history (last 24h)
alias sacct24='sacct -u $USER --starttime=$(date -d "24 hours ago" +%Y-%m-%d) -o JobID,JobName%20,Partition,State,Elapsed,MaxRSS,NodeList'

# Cancel all my jobs
alias scancel_all='scancel -u $USER'

# Show job efficiency after completion
# Usage: eff JOBID
eff() {
    seff "$1"
}

# Show full job details
# Usage: jobinfo JOBID
jobinfo() {
    scontrol show job "$1"
}

# Tail job output log
# Usage: joblog JOBID [log_dir]
joblog() {
    local jobid="$1"
    local logdir="${2:-logs}"
    local logfile=$(ls -t ${logdir}/*_${jobid}.out 2>/dev/null | head -1)
    if [[ -n "$logfile" ]]; then
        tail -f "$logfile"
    else
        echo "No log file found for job $jobid in $logdir"
    fi
}

# Tail job error log
# Usage: joberr JOBID [log_dir]
joberr() {
    local jobid="$1"
    local logdir="${2:-logs}"
    local logfile=$(ls -t ${logdir}/*_${jobid}.err 2>/dev/null | head -1)
    if [[ -n "$logfile" ]]; then
        tail -f "$logfile"
    else
        echo "No error file found for job $jobid in $logdir"
    fi
}

# ── GPU Monitoring ─────────────────────────────────────────────────────────

# Show GPU availability across all GPU partitions
alias gpus='sinfo -p gpu,short_gpu,preempt_gpu -O "NodeList:12,Gres:20,GresUsed:20,StateLong:12,Partition:14" --noheader'

# Show GPU nodes with details
alias gpunodes='sinfo -N -p gpu,short_gpu,preempt_gpu -o "%N %G %c %m %P %T" --noheader | sort | uniq'

# ── Resource Monitoring ────────────────────────────────────────────────────

# Check my process memory usage on login node
alias mymem='ps -U $USER -o pid,rss:12,vsz:12,etime,comm --sort=-rss | head -20'

# Kill zombie node processes (from old VS Code sessions)
alias killnodes='pkill -u $USER node; pkill -u $USER -f "npm exec notebo"'

# Check quota
alias quota_home='check_quota home'
alias quota_bigdata='check_quota bigdata'

# ── Shortcuts ──────────────────────────────────────────────────────────────

# Quick directory jumps (customize these paths)
# alias ws='cd ~/workspace'
# alias data='cd /bigdata/labname/username'

# Module shortcuts
alias ml='module load'
alias mls='module list'
alias mav='module avail'
