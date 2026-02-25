#!/bin/bash -l

#SBATCH --nodes=4
#SBATCH --ntasks=128
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4G
#SBATCH --time=2-00:00:00
#SBATCH --job-name="mpi_job"
#SBATCH --output=mpi_%j.out
#SBATCH --error=mpi_%j.err
#SBATCH -p batch

# Load MPI module
module load openmpi

# Run MPI application
echo "Job started on $(hostname) at $(date)"
echo "Running on nodes: ${SLURM_JOB_NODELIST}"
echo "Total tasks: ${SLURM_NTASKS}"

mpirun ./my_mpi_program input.dat

echo "Job finished at $(date)"
