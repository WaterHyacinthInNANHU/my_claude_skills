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

Web-based access (Open OnDemand) is also available for browser-based JupyterHub, RStudio, and VSCode sessions.

Change password after first login:
```bash
passwd
```

**Important:** Do NOT run computationally intensive tasks on head nodes. Always submit jobs via `sbatch` or `srun` to compute nodes.

## Slurm Job Submission

### Interactive Jobs

```bash
# Basic interactive session (uses default epyc partition)
srun --pty bash -l

# With resources specified
srun --mem=1gb --cpus-per-task=1 --ntasks=1 --time=10:00:00 --pty bash -l

# Short partition (2 hour max)
srun -p short -t 2:00:00 -c 8 --mem=8GB --pty bash -l

# GPU interactive
srun -p gpu --gres=gpu:1 --mem=100g --time=1:00:00 --pty bash -l

# GPU interactive with specific GPU type
srun -p gpu --gres=gpu:a100:1 --mem=100g --pty bash -l
```

### Batch Jobs

Submit a script:
```bash
sbatch script.sh
sbatch -p epyc script.sh
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
# Array job limit: 2500 jobs per array
```

### GPU Jobs

Available GPU types: K80, P100, A100, H100.

```bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1              # 1 GPU (any type)
#SBATCH --gres=gpu:a100:1         # Specific GPU type
#SBATCH --gres=gpu:4              # 4 GPUs
```

The assigned GPUs are exposed via the `CUDA_VISIBLE_DEVICES` environment variable.

### Preemptible Jobs

Preemptible partitions offer access without counting against lab quotas, but jobs can be killed at any time (1-minute grace period):

```bash
# CPU preempt (requires -A preempt)
sbatch -p preempt -A preempt --time=12:00:00 script.sh

# GPU preempt
sbatch -p preempt_gpu -A preempt --gres=gpu:1 script.sh
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
jobMonitor                       # Cluster activity summary
```

### Resource Efficiency

After a job completes, use `seff JOBID` to check efficiency. Aim to request ~20% more memory than actually used to account for spikes while avoiding waste.

## Partitions (Queues)

| Partition | Use Case | Per-User Limit | Max Time |
|-----------|----------|----------------|----------|
| epyc (default), intel, batch | CPU jobs | 384 cores, 1TB mem | 30 days |
| short | Quick CPU jobs | 384 cores, 1TB mem | 2 hours |
| highmem | Memory-intensive (min 100GB) | 32 cores, 2TB mem | 30 days |
| highclock | Low-parallelism, high clock speed | 32 cores, 256GB mem | 7 days |
| gpu | GPU workloads | 4 GPUs, 48 cores, 512GB mem | 7 days |
| short_gpu | Quick GPU jobs | 4 GPUs, 48 cores, 512GB mem | 2 hours |
| preempt | Preemptible CPU (-A preempt) | Same as CPU | 24 hours |
| preempt_gpu | Preemptible GPU (-A preempt) | 1 GPU | 24 hours |

Group limits: 768 cores and 8 GPUs across all users in a group. Max 5000 queued/running jobs per user.

## Module System

The cluster uses **Environment Modules** (Tcl-based). Note: `module spider` is not available; use `module avail` to search.

```bash
module avail                     # List available software
module avail R                   # Search for R versions
module load miniconda3           # Load Python/conda
module load R/4.2.0              # Load specific version
module list                      # Show loaded modules
module unload <name>             # Unload a module
module purge                     # Unload all modules
module help                      # Module help
```

## Conda Environments

The default Python module is `miniconda3` (minimal packages). `anaconda` provides a full distribution with pre-installed packages. `mamba` is available as a faster drop-in replacement for `conda`.

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

### Jupyter Kernel Registration

To use a conda environment in Jupyter, register it as a kernel:
```bash
conda activate myenv
conda install ipykernel
python -m ipykernel install --user --name myenv --display-name "My Env"
```

## Storage

| Location | Path | Quota | Backup |
|----------|------|-------|--------|
| Home | `/rhome/username` | 20 GB | Daily, 1 week |
| Bigdata (shared) | `/bigdata/labname/shared` | Lab purchase | Weekly, 1 month |
| Bigdata (personal) | `/bigdata/labname/username` | Lab purchase | Weekly, 1 month |
| Scratch | `/scratch` (`$SCRATCH`) | None | None, auto-deleted after job |
| Temp | `/tmp` | Node disk | None |
| RAM disk | `/dev/shm` | Consumes job memory | None |

- **Scratch** is SSD-backed, node-local, and faster than persistent storage. Data is auto-deleted after job completion.
- **`/dev/shm`** is RAM-based (fastest) but consumes from your job's memory allocation.

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
- List snapshots: `mmlssnapshot home` or `mmlssnapshot bigdata`

## SSH Tunneling (for Jupyter, etc.)

```bash
ssh -NL 8888:NodeName:8888 username@cluster.hpcc.ucr.edu
```

Then open `http://localhost:8888` in your browser.

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
| `-A ACCOUNT` | Specify account (e.g., `-A preempt`) |
| `--cpus-per-task=N` | Cores for threading (OpenMP) |
| `--ntasks=N` | Tasks for MPI |
| `--mem=XG` | Memory per job |
| `--time=D-HH:MM:SS` | Wall time limit |
| `--gres=gpu:N` | Request N GPUs |
| `--gres=gpu:TYPE:N` | Request specific GPU type |
| `--constraint=X` | Hardware filter |
| `--array=1-N` | Array job |
| `--mail-type=ALL` | Email notifications |

## Common Slurm Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `QOSMaxWallDurationPerJobLimit` | Exceeds partition time limit | Reduce `--time` |
| `AssocGrpCpuLimit` | Per-user CPU limit hit | Wait for running jobs to finish |
| `AssocGrpMemLimit` | Per-user memory limit hit | Wait for running jobs to finish |
| `AssocGrpGRES` | Per-user GPU limit hit | Wait for GPU jobs to finish |
| `MaxSubmitJobLimit` | Over 5000 queued/running jobs | Wait for jobs to complete |
| `PartitionConfig` | Wrong account/partition pairing | Use `-A preempt` for preempt partitions |
| `QOSMinGRES` | Missing resource request | Use `--mem=100g+` for highmem, `--gres` for gpu |
