---
name: ucr_hpcc_cluster
description: Help users work with the UCR HPCC (High Performance Computing Center) cluster. Provides commands for connecting, submitting jobs, managing software, and handling data storage.
---

# ucr_hpcc_cluster

Help users work with the UCR HPCC (High Performance Computing Center) cluster. This skill provides commands for connecting, submitting jobs, managing software, and handling data storage.

## Connection

SSH to the cluster:
```bash
ssh -X username@cluster.hpcc.ucr.edu
```

Change password after first login:
```bash
passwd
```

## Slurm Job Submission

### Interactive Jobs

```bash
# Basic interactive session
srun --pty bash -l

# With resources specified
srun --mem=1gb --cpus-per-task=1 --ntasks=1 --time=10:00:00 --pty bash -l

# Short partition (2 hour max)
srun -p short -t 2:00:00 -c 8 --mem=8GB --pty bash -l

# GPU interactive
srun -p gpu --gres=gpu:1 --mem=100g --time=1:00:00 --pty bash -l
```

### Batch Jobs

Submit a script:
```bash
sbatch script.sh
sbatch -p batch script.sh
sbatch -p highmem --mem=100g --time=24:00:00 script.sh
sbatch -p gpu --gres=gpu:1 --mem=100g --time=1:00:00 script.sh
```

### SBATCH Script Template

```bash
#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=10G
#SBATCH --time=1-00:15:00     # D-HH:MM:SS
#SBATCH --mail-user=user@email.com
#SBATCH --mail-type=ALL
#SBATCH --job-name="my_job"
#SBATCH -p epyc

module load <software>
# Your commands here
```

### Array Jobs

```bash
#SBATCH --array=1-100
# Access index with ${SLURM_ARRAY_TASK_ID}
```

### GPU Jobs

```bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1              # 1 GPU
#SBATCH --gres=gpu:k80:1          # Specific GPU type
#SBATCH --gres=gpu:4              # 4 GPUs
```

## Job Monitoring

```bash
squeue -u $USER --start          # Your jobs with start times
scontrol show job JOBID          # Job details
sacct -u $USER -l                # Past job history
seff JOBID                       # Resource usage after completion
scancel JOBID                    # Cancel a job
scancel JOBID1 JOBID2 JOBID3     # Cancel multiple jobs
group_cpus                       # Cores used by your group
slurm_limits                     # Show resource limits
```

## Partitions (Queues)

| Partition | Use Case | Per-User Limit | Max Time |
|-----------|----------|----------------|----------|
| epyc, intel, batch | CPU jobs | 384 cores, 1TB mem | 30 days |
| short | Quick jobs | 384 cores, 1TB mem | 2 hours |
| highmem | Memory-intensive | 32 cores, 2TB mem | 30 days |
| gpu | GPU workloads | 4 GPUs, 48 cores | 7 days |
| preempt | Preemptible | Same as CPU | 24 hours |
| preempt_gpu | Preemptible GPU | 1 GPU | 24 hours |

Group limits: 768 cores, 8 GPUs across all users in a group.

## Module System

```bash
module avail                     # List available software
module avail R                   # Search for R versions
module load miniconda3           # Load Python/conda
module load R/4.2.0              # Load specific version
module list                      # Show loaded modules
module unload <name>             # Unload a module
module purge                     # Unload all modules
```

## Conda Environments

Configure conda for bigdata storage (`~/.condarc`):
```yaml
channels:
  - defaults
pkgs_dirs:
  - ~/bigdata/.conda/pkgs
envs_dirs:
  - ~/bigdata/.conda/envs
auto_activate_base: false
```

Manage environments:
```bash
conda create -n myenv python=3.10
conda activate myenv
conda install package_name
conda env list
conda deactivate
conda env remove --name myenv
```

Install packages on a compute node to avoid memory issues:
```bash
srun -p short -c 4 --mem=10g --pty bash -l
conda install -n myenv package_name
```

## Storage

| Location | Path | Quota |
|----------|------|-------|
| Home | `/rhome/username` | 20 GB |
| Bigdata (shared) | `/bigdata/labname/shared` | Lab purchase |
| Bigdata (personal) | `/bigdata/labname/username` | Lab purchase |
| Scratch | `/scratch` | Node-local, auto-deleted |

Check usage:
```bash
check_quota home
check_quota bigdata
du -sh .                         # Current directory size
du -sch *                        # Subdirectory sizes
```

Snapshots (backups):
- Home: daily, kept 1 week (`/rhome/.snapshots/`)
- Bigdata: weekly, kept 1 month (`/bigdata/.snapshots/`)

## SSH Tunneling (for Jupyter, etc.)

```bash
ssh -NL 8888:NodeName:8888 username@cluster.hpcc.ucr.edu
```

## Node Constraints

Request specific hardware:
```bash
srun -p short --constraint intel --pty bash -l
srun -p short --constraint "amd&(rome|milan)" --pty bash -l
srun -p short_gpu --constraint "gpu_latest" --gpus=1 --pty bash -l
```

## Common Slurm Flags

| Flag | Description |
|------|-------------|
| `-p PARTITION` | Specify partition |
| `--cpus-per-task=N` | Cores for threading (OpenMP) |
| `--ntasks=N` | Tasks for MPI |
| `--mem=XG` | Memory per job |
| `--time=D-HH:MM:SS` | Wall time limit |
| `--gres=gpu:N` | Request N GPUs |
| `--constraint=X` | Hardware filter |
| `--array=1-N` | Array job |
| `--mail-type=ALL` | Email notifications |
