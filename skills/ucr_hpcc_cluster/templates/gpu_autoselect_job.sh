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

# ── Auto GPU selection & self-submit ──────────────────────────────────
# When run outside SLURM (./script.sh instead of sbatch script.sh),
# auto-detect the best available GPU type and sbatch itself.
# Override partition: PARTITION=gpu ./script.sh

if [ -z "${SLURM_JOB_ID:-}" ]; then
    PARTITION="${PARTITION:-short_gpu}"

    auto_select_gpu() {
        # Edit this list to match your cluster's GPUs, fastest first
        local -a preferred=("h100" "a100" "ada6000" "p100")
        local nodes
        nodes=$(sinfo -N -p "$PARTITION" -o "%N %G %T" --noheader 2>/dev/null)
        for gtype in "${preferred[@]}"; do
            if echo "$nodes" | grep "gpu:${gtype}:" | grep -iq "idle\|mix"; then
                echo "$gtype"
                return 0
            fi
        done
        return 1
    }

    mkdir -p logs
    GPU_TYPE=$(auto_select_gpu) || GPU_TYPE=""
    if [ -n "$GPU_TYPE" ]; then
        echo "Auto-selected GPU: $GPU_TYPE (partition: $PARTITION)"
        exec sbatch -p "$PARTITION" --gres="gpu:${GPU_TYPE}:1" "$0" "$@"
    else
        echo "No specific GPU type available, submitting with default"
        exec sbatch -p "$PARTITION" "$0" "$@"
    fi
fi

# ── Environment ───────────────────────────────────────────────────────
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
