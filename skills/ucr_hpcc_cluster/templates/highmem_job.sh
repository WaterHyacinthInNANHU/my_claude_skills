#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=500G
#SBATCH --time=7-00:00:00
#SBATCH --job-name="highmem_job"
#SBATCH --output=highmem_%j.out
#SBATCH --error=highmem_%j.err
#SBATCH -p highmem

# Load required modules
module load miniconda3
conda activate myenv

# Run your memory-intensive command
echo "Job started on $(hostname) at $(date)"
echo "Available memory: $(free -h | grep Mem | awk '{print $2}')"
# YOUR COMMAND HERE
echo "Job finished at $(date)"
