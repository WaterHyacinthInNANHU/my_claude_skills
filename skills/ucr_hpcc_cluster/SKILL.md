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

```bash
#SBATCH -p gpu
#SBATCH --gres=gpu:1              # 1 GPU (any type)
#SBATCH --gres=gpu:a100:1         # Specific GPU type
#SBATCH --gres=gpu:4              # 4 GPUs
```

The assigned GPUs are exposed via the `CUDA_VISIBLE_DEVICES` environment variable.

**Important:** GPU types and availability change over time. Always auto-detect using the commands in the "Auto-Detecting Cluster Resources" section below rather than assuming a fixed list.

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

## Auto-Detecting Cluster Resources

**IMPORTANT:** When the user asks about available GPUs, nodes, hardware, or cluster resources — or when writing a job script that targets specific hardware — ALWAYS run the detection commands below to get **live** data. Do NOT rely on hardcoded lists, as nodes are frequently added, removed, or taken down for maintenance.

### GPU inventory (all GPU nodes across all partitions)

Run this to get a per-node breakdown of GPU type, count, CPUs, memory, state, and partitions:

```bash
sinfo -N -o "%N %G %c %m %P %T" --noheader 2>/dev/null | grep -i gpu | sort -t'u' -k2 -n | uniq
```

### Summary by partition

Run this for a partition-level view (which GPU types are in which partition):

```bash
sinfo -o "%P %N %G %a %T" --noheader 2>/dev/null | grep -i gpu | sort
```

### Current GPU availability (idle vs in-use)

Run this to see how many GPUs are free right now:

```bash
sinfo -p gpu,short_gpu,preempt_gpu -O "NodeList:12,Gres:20,GresUsed:20,StateLong:12,Partition:14" --noheader 2>/dev/null
```

### Node details (specific node)

To inspect a specific node's full hardware:

```bash
scontrol show node NODENAME
```

### When to auto-detect

Run detection commands automatically when:
- User asks "what GPUs are available?", "how many A100s?", "show me the nodes", etc.
- User asks which GPU type to use for their workload
- Writing or modifying a job script that requests GPU resources (to verify the requested GPU type actually exists and is available)
- User asks about cluster capacity or current utilization

### Interpreting results

When presenting results to the user:
- Show a clean summary table (node, GPU type, count, CPUs, RAM, partitions, state)
- Highlight which nodes are `down` or `drain` (unavailable)
- Note partition restrictions (e.g., some GPUs only in `short_gpu`/`preempt_gpu`, not in `gpu`)
- Calculate totals by GPU type
- Mention per-user limits: 4 GPUs and 48 cores in `gpu`/`short_gpu`; 1 GPU in `preempt_gpu`; group limit of 8 GPUs

## Estimating Wait Time & Choosing the Best Partition

**IMPORTANT:** When a user wants to submit a GPU job, proactively estimate queue wait times and recommend the best partition/GPU combination. Run these commands and analyze the results.

### Step 1: Check current GPU utilization

See which GPUs are in use vs available on each node:

```bash
sinfo -p gpu,short_gpu,preempt_gpu -O "NodeList:12,Gres:20,GresUsed:20,StateLong:12,Partition:14" --noheader 2>/dev/null
```

Compare `Gres` (total) vs `GresUsed` (in use). For example, `gpu:a100:8` with `gpu:a100:6(IDX:0-5)` means 2 A100s are free on that node.

### Step 2: Check pending queue depth per partition

```bash
squeue -p gpu --state=PENDING -o "%i %P %u %T %l %S %r" --noheader 2>/dev/null | head -20
squeue -p short_gpu --state=PENDING --noheader 2>/dev/null | wc -l
squeue -p preempt_gpu --state=PENDING --noheader 2>/dev/null | wc -l
```

The `%S` field shows the estimated start time (may be `N/A` for far-out jobs). The `%r` field shows the pending reason.

### Step 3: Check running jobs to estimate when GPUs free up

```bash
squeue -p gpu,short_gpu,preempt_gpu --state=RUNNING -o "%i %P %N %u %M %l %b" --noheader 2>/dev/null
```

Key columns: `%M` = elapsed time, `%l` = time limit, `%b` = GRES (GPU) allocation. Calculate remaining time as `time_limit - elapsed` to estimate when each GPU becomes available.

### Step 4: Analyze and recommend

After gathering the data above, analyze it to provide a recommendation:

1. **Free GPUs right now?** If any GPUs show `Gres` > `GresUsed`, those are immediately available. Recommend submitting there.
2. **Soonest availability:** Look at running jobs' remaining time (`time_limit - elapsed`). The job finishing soonest frees up a GPU first.
3. **Queue depth:** Fewer pending jobs = shorter wait. Compare pending counts across `gpu`, `short_gpu`, and `preempt_gpu`.
4. **Partition trade-offs:** Present options like:
   - `gpu` partition: up to 7-day jobs, but may have a long queue
   - `short_gpu`: 2-hour max, but often empty queue (good for quick tests)
   - `preempt_gpu`: up to 24 hours, can be preempted, but often has idle GPUs (requires `-A preempt`)
5. **GPU type matters:** If user needs a specific GPU (e.g., A100 for large models), check availability of that type specifically. If flexible, recommend whichever type has the shortest wait.
6. **Specific node targeting:** If a particular node has free GPUs, the user can request it with `--nodelist=gpu09` (not guaranteed but can help).

### Example recommendation format

Present findings as a concise summary:

```
Current GPU availability:
- gpu06: 0/8 A100 free (next available in ~1d 2h)
- gpu07: 2/8 A100 free  <-- submit here
- gpu09: 9/10 Ada 6000 free (short_gpu/preempt_gpu only)

Recommendation: Submit to gpu partition targeting A100 (2 free on gpu07).
If job is <2 hours, use short_gpu for faster scheduling.
If job is <24 hours and can tolerate preemption, preempt_gpu has 9 idle Ada 6000s on gpu09.

Pending queue: gpu=28 jobs, short_gpu=0, preempt_gpu=1
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

## Best Practices: Project & Environment Setup

### Directory Strategy

Home (`/rhome`) is only 20GB — use it for configs and dotfiles only. Put projects, environments, and data on bigdata:

```
/rhome/username/              # 20GB — configs, small scripts, symlinks
├── .condarc                  # points conda to bigdata
├── .bashrc                   # shell config
├── .Renviron                 # R library path → bigdata
└── workspace -> /bigdata/labname/username/workspace  # symlink

/bigdata/labname/username/    # Lab quota — bulk storage
├── workspace/                # project code
│   └── my_project/
│       ├── scripts/
│       ├── results/
│       └── .venv/            # uv venv (if using uv)
├── .conda/                   # conda envs + package cache
│   ├── envs/
│   └── pkgs/
├── .cache/                   # pip, uv, huggingface caches
│   ├── uv/
│   └── huggingface/
└── R/                        # R libraries
```

Create a symlink for convenience:
```bash
ln -s /bigdata/labname/username/workspace ~/workspace
```

### Python: Conda/Mamba Setup

**Step 1: Redirect conda storage** — create `~/.condarc`:
```yaml
channels:
  - conda-forge
  - defaults
pkgs_dirs:
  - ~/bigdata/.conda/pkgs
envs_dirs:
  - ~/bigdata/.conda/envs
auto_activate_base: false
```

**Step 2: Create environments on a compute node** (not the head node):
```bash
srun -p short -c 4 --mem=10g --pty bash -l
module load miniconda3
mamba create -n myproject python=3.11
conda activate myproject
mamba install numpy pandas scikit-learn
```

### Python: uv Setup

`uv` is not installed cluster-wide but can be installed per-user:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Redirect cache to bigdata — add to `~/.bashrc`:
```bash
export UV_CACHE_DIR=/bigdata/labname/username/.cache/uv
```

Use in projects:
```bash
cd /bigdata/labname/username/workspace/my_project
uv init                       # creates pyproject.toml
uv add numpy pandas           # adds dependencies + creates .venv
uv run python my_script.py    # runs with the project's env
```

In a job script, `uv run` handles activation automatically:
```bash
#!/bin/bash -l
#SBATCH -p epyc --cpus-per-task=4 --mem=16G --time=4:00:00
cd /bigdata/labname/username/workspace/my_project
uv run python my_script.py
```

### R Setup

Redirect R library path to bigdata — create `~/.Renviron`:
```
R_LIBS_USER=/bigdata/labname/username/R/%p-library/%v
```

Then in R:
```r
# Packages install to bigdata automatically
install.packages("ggplot2")
```

Note: Reinstall R packages when upgrading R versions — they aren't backward compatible across versions.

### Cache Management

Many tools cache to home by default. Redirect them to bigdata in `~/.bashrc`:
```bash
# Conda (handled by .condarc, but pip within conda also caches)
export PIP_CACHE_DIR=/bigdata/labname/username/.cache/pip

# uv
export UV_CACHE_DIR=/bigdata/labname/username/.cache/uv

# Hugging Face models
export HF_HOME=/bigdata/labname/username/.cache/huggingface

# Singularity/Apptainer containers
export SINGULARITY_CACHEDIR=/bigdata/labname/username/.cache/singularity
```

### Data Storage Strategy

| What | Where | Why |
|------|-------|-----|
| Code & scripts | `/bigdata/.../workspace/` | Version-controlled, plenty of space |
| Conda/uv envs | `/bigdata/.../` (via config) | Envs can be multi-GB |
| Raw input data | `/bigdata/.../data/` | Persistent, shared with lab |
| Job results | `/bigdata/.../results/` | Persistent, backed up weekly |
| Temp/intermediate | `$SCRATCH` (in jobs) | Fast local SSD, auto-cleaned |
| Configs/dotfiles | `/rhome/` | Small, backed up daily |

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
