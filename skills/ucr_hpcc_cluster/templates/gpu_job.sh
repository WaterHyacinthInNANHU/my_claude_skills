#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=1-00:00:00
#SBATCH --job-name="gpu_job"
#SBATCH --output=gpu_%j.out
#SBATCH --error=gpu_%j.err
#SBATCH -p gpu
#SBATCH --gres=gpu:1

# Load required modules
module load miniconda3
module load cuda
conda activate pytorch_env

# Verify GPU is available
nvidia-smi

# Run your GPU command
echo "Job started on $(hostname) at $(date)"
# python train.py
echo "Job finished at $(date)"
