#!/bin/bash -l

#SBATCH --job-name="gpu_job"
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=100G
#SBATCH --time=2:00:00
#SBATCH -p short_gpu
#SBATCH --gres=gpu:1
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

# ── Self-submit with generic GPU request ─────────────────────────────
# When run outside SLURM (./script.sh instead of sbatch script.sh),
# submit itself with a generic GPU request and let SLURM schedule.
# Override partition: PARTITION=gpu ./script.sh
#
# NOTE: We deliberately use --gres=gpu:1 (no specific type) rather than
# auto-selecting a GPU type. Auto-selection is unreliable because:
#   1. Stale availability — GPU free at submission time may be taken by
#      the time the job starts (minutes to hours later)
#   2. Column truncation — sinfo output columns can truncate long GPU
#      type names, breaking grep-based parsing
#   3. All-or-nothing — requesting a specific GPU type (e.g., gpu:a100:1)
#      prevents SLURM from scheduling on other available types, causing
#      jobs to queue indefinitely when that type fills up
# Using generic --gres=gpu:1 lets SLURM pick the best available node.

if [ -z "${SLURM_JOB_ID:-}" ]; then
    PARTITION="${PARTITION:-short_gpu}"
    mkdir -p logs
    echo "Submitting to $PARTITION with generic GPU request (SLURM picks best available)"
    exec sbatch -p "$PARTITION" --gres=gpu:1 "$0" "$@"
fi

# ── Environment ───────────────────────────────────────────────────────
# GCC 12 is needed for CUDA extension compilation (default GCC 8.x is too old)
module load gcc/12.2.0
module load cuda/12.1

# Fix SSL cert issues on HPC nodes (HuggingFace, pip, torch.hub)
export SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-bundle.crt

# ── Diagnostics ───────────────────────────────────────────────────────
echo "============================================"
echo "  Job:   $SLURM_JOB_NAME (#$SLURM_JOB_ID)"
echo "  Node:  $(hostname)"
echo "  GPU:   $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "  CUDA:  $(nvcc --version 2>/dev/null | tail -1 || echo 'N/A')"
echo "============================================"
echo ""

# ── Your work here ────────────────────────────────────────────────────

echo "Job started at $(date)"

# Example: activate environment and run script
# source /path/to/.venv/bin/activate
# python train.py --epochs 100

echo "Job finished at $(date)"
