#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=1:00:00
#SBATCH --job-name="my_job"
#SBATCH --output=job_%j.out
#SBATCH --error=job_%j.err
#SBATCH -p batch

# Load required modules
module load miniconda3
conda activate myenv

# Run your command
echo "Job started on $(hostname) at $(date)"
# YOUR COMMAND HERE
echo "Job finished at $(date)"
