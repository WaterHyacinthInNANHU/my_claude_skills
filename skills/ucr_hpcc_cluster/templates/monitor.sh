#!/bin/bash
#
# Job monitor & management utility
#
# Copy into your project and adjust LOG_DIR if needed.
#
# Usage:
#   ./monitor.sh              # show all your jobs
#   ./monitor.sh watch        # live refresh (every 5s)
#   ./monitor.sh log JOBID    # tail stdout log
#   ./monitor.sh err JOBID    # tail stderr log
#   ./monitor.sh info JOBID   # full job details
#   ./monitor.sh eff JOBID    # resource efficiency (after completion)
#   ./monitor.sh gpus         # show available GPUs
#   ./monitor.sh cancel JOBID # cancel a job
#   ./monitor.sh cancel all   # cancel all your jobs

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────
# Adjust this to match your project's log directory and naming pattern.
# Default expects: logs/<jobname>_<jobid>.out / .err
LOG_DIR="logs"

CMD="${1:-status}"
ARG="${2:-}"

FMT="%.10i %.20j %.8T %.10M %.10l %.4C %.8m %R"

case "$CMD" in
    status|s)
        echo "=== Your jobs ==="
        squeue -u "$USER" -o "$FMT" 2>/dev/null || echo "No jobs found."
        echo ""
        echo "Tip: use 'watch' for live refresh, 'log JOBID' to tail output"
        ;;

    watch|w)
        echo "Watching jobs (Ctrl+C to stop)..."
        watch -n 5 "squeue -u $USER -o \"$FMT\""
        ;;

    log|l)
        if [ -z "$ARG" ]; then
            echo "Usage: $0 log JOBID"
            exit 1
        fi
        LOG=$(ls -t ${LOG_DIR}/*_"${ARG}".out 2>/dev/null | head -1)
        if [ -z "$LOG" ]; then
            echo "No log found for job $ARG in ${LOG_DIR}/"
            exit 1
        fi
        echo "=== $LOG ==="
        tail -f "$LOG"
        ;;

    err|e)
        if [ -z "$ARG" ]; then
            echo "Usage: $0 err JOBID"
            exit 1
        fi
        LOG=$(ls -t ${LOG_DIR}/*_"${ARG}".err 2>/dev/null | head -1)
        if [ -z "$LOG" ]; then
            echo "No error log found for job $ARG in ${LOG_DIR}/"
            exit 1
        fi
        echo "=== $LOG ==="
        tail -f "$LOG"
        ;;

    info|i)
        if [ -z "$ARG" ]; then
            echo "Usage: $0 info JOBID"
            exit 1
        fi
        scontrol show job "$ARG"
        ;;

    eff)
        if [ -z "$ARG" ]; then
            echo "Usage: $0 eff JOBID"
            exit 1
        fi
        seff "$ARG"
        ;;

    gpus|g)
        echo "=== GPU nodes (all partitions) ==="
        sinfo -N -o "%12N %12P %10T %20G" --noheader 2>/dev/null \
            | grep "gpu:" \
            | sort -k4 -k3 \
            || echo "No GPU nodes found"
        echo ""
        echo "Summary by GPU type:"
        sinfo -o "%20G %12P %6D %10T" --noheader 2>/dev/null \
            | grep "gpu:" \
            | sort \
            || true
        ;;

    cancel|c)
        if [ -z "$ARG" ]; then
            echo "Usage: $0 cancel JOBID  or  $0 cancel all"
            exit 1
        fi
        if [ "$ARG" = "all" ]; then
            echo "Cancelling all your jobs..."
            scancel -u "$USER"
            echo "Done."
        else
            echo "Cancelling job $ARG..."
            scancel "$ARG"
            echo "Done."
        fi
        ;;

    *)
        echo "Usage: $0 {status|watch|log|err|info|eff|gpus|cancel} [JOBID|all]"
        exit 1
        ;;
esac
