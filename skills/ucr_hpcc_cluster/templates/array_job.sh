#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=1:00:00
#SBATCH --job-name="array_job"
#SBATCH --output=array_%A_%a.out
#SBATCH --error=array_%A_%a.err
#SBATCH -p epyc
#SBATCH --array=1-100

# Each task gets a unique ID from 1 to 100
TASK_ID=${SLURM_ARRAY_TASK_ID}

# Load required modules
module load miniconda3
conda activate myenv

# Run your command with the task ID
echo "Running task ${TASK_ID} on $(hostname)"
# python script.py --param-id ${TASK_ID}
echo "Task ${TASK_ID} finished"
