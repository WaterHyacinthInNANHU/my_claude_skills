#!/bin/bash
# Compact experiment monitor
# Polls training status and outputs only meaningful changes
# Usage: ./monitor.sh [--pid PID | --slurm JOB_ID | --log LOG_FILE] [--interval SECONDS] [--metric PATTERN]

set -e

PID=""
SLURM_JOB=""
LOG_FILE="logs/train.log"
INTERVAL=60
METRIC_PATTERN="(loss|acc|epoch|step|val_|eval_|reward)"
PREV_METRICS=""
START_TIME=$(date +%s)

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --pid) PID="$2"; shift 2 ;;
        --slurm) SLURM_JOB="$2"; shift 2 ;;
        --log) LOG_FILE="$2"; shift 2 ;;
        --interval) INTERVAL="$2"; shift 2 ;;
        --metric) METRIC_PATTERN="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "  --pid PID          Process ID to monitor"
            echo "  --slurm JOB_ID     SLURM job ID to monitor"
            echo "  --log FILE         Log file to monitor (default: logs/train.log)"
            echo "  --interval SEC     Polling interval in seconds (default: 60)"
            echo "  --metric PATTERN   Regex for metrics to extract (default: loss|acc|epoch|...)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Check if process is still running
is_running() {
    if [[ -n "$PID" ]]; then
        kill -0 "$PID" 2>/dev/null
    elif [[ -n "$SLURM_JOB" ]]; then
        local state=$(squeue -j "$SLURM_JOB" -h -o "%T" 2>/dev/null)
        [[ "$state" == "RUNNING" || "$state" == "PENDING" ]]
    elif [[ -f "$LOG_FILE" ]]; then
        # Check if log file is still being written to (modified in last 2 intervals)
        local last_mod=$(stat -c %Y "$LOG_FILE" 2>/dev/null || echo 0)
        local now=$(date +%s)
        local stale_threshold=$((INTERVAL * 3))
        [[ $((now - last_mod)) -lt $stale_threshold ]]
    else
        return 1
    fi
}

# Extract latest metrics from log
extract_metrics() {
    if [[ ! -f "$LOG_FILE" ]]; then
        echo "NO_LOG_FILE"
        return
    fi

    # Get last 50 lines, extract metric-like patterns
    tail -50 "$LOG_FILE" 2>/dev/null | \
        grep -oiE "[a-z_]*($METRIC_PATTERN)[a-z_]*[=: ]+[0-9]+\.?[0-9]*" | \
        tail -10
}

# Get exit status
get_exit_status() {
    if [[ -n "$SLURM_JOB" ]]; then
        sacct -j "$SLURM_JOB" --format=State -n 2>/dev/null | head -1 | tr -d ' '
    elif [[ -n "$PID" ]]; then
        wait "$PID" 2>/dev/null
        echo $?
    else
        # Check last line of log for common completion patterns
        tail -5 "$LOG_FILE" 2>/dev/null | grep -iqE "(complete|finish|done|error|exception|traceback)"
        if [[ $? -eq 0 ]]; then
            tail -5 "$LOG_FILE" | grep -iqE "(error|exception|traceback|failed)" && echo "FAILED" || echo "COMPLETED"
        else
            echo "UNKNOWN"
        fi
    fi
}

# Main monitoring loop
echo "=== MONITOR START ==="
echo "Log: $LOG_FILE"
[[ -n "$PID" ]] && echo "PID: $PID"
[[ -n "$SLURM_JOB" ]] && echo "SLURM: $SLURM_JOB"
echo "Interval: ${INTERVAL}s"
echo "Metric pattern: $METRIC_PATTERN"
echo ""

while is_running; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$(( (CURRENT_TIME - START_TIME) / 60 ))

    # Extract current metrics
    CURRENT_METRICS=$(extract_metrics)

    # Only print if metrics changed
    if [[ "$CURRENT_METRICS" != "$PREV_METRICS" ]]; then
        echo "--- ${ELAPSED}min elapsed ---"
        echo "$CURRENT_METRICS"
        echo ""
        PREV_METRICS="$CURRENT_METRICS"
    fi

    sleep "$INTERVAL"
done

# Training finished
TOTAL_TIME=$(( ($(date +%s) - START_TIME) / 60 ))
EXIT_STATUS=$(get_exit_status)

echo "=== TRAINING COMPLETE ==="
echo "Total time: ${TOTAL_TIME} minutes"
echo "Status: $EXIT_STATUS"
echo ""
echo "Final metrics:"
extract_metrics
echo ""

# Signal completion
echo "MONITOR_DONE:${EXIT_STATUS}:${TOTAL_TIME}min"
