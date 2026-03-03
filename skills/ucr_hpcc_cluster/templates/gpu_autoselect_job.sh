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
        # Query per-node Gres vs GresUsed to find GPUs with free slots
        # (checking node state alone is unreliable — a "mix" node may have
        #  free CPUs but all GPUs allocated)
        local info
        info=$(sinfo -N -p "$PARTITION" \
               -O "NodeList:12,Gres:20,GresUsed:20,StateLong:12" \
               --noheader 2>/dev/null)
        for gtype in "${preferred[@]}"; do
            while IFS= read -r line; do
                [ -z "$line" ] && continue
                local state total used
                state=$(echo "$line" | awk '{print $4}')
                echo "$state" | grep -iq "down\|drain" && continue
                total=$(echo "$line" | awk '{print $2}' | grep -oP "gpu:${gtype}:\K[0-9]+" || echo 0)
                [ "$total" -eq 0 ] 2>/dev/null && continue
                used=$(echo "$line" | awk '{print $3}' | grep -oP "gpu:${gtype}:\K[0-9]+" || echo 0)
                if [ "$total" -gt "$used" ] 2>/dev/null; then
                    echo "$gtype"
                    return 0
                fi
            done <<< "$info"
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
