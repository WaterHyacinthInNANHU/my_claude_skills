---
name: ucr_hpcc_cluster
description: Help users work with the UCR HPCC (High Performance Computing Center) cluster. Provides commands for connecting, submitting jobs, managing software, and handling data storage.
---

# ucr_hpcc_cluster

Help users work with the UCR HPCC (High Performance Computing Center) cluster. This skill provides commands for connecting, submitting jobs, managing software, and handling data storage.

## Auto-Configuration

**When the user asks to "configure the cluster", "set up HPCC", or "install cluster aliases"**, automatically add the HPCC helper functions and aliases to their `~/.bashrc`.

### What to Install

Append the following block to `~/.bashrc` (check if already present first by searching for `# ── UCR HPCC`):

```bash
# ── UCR HPCC Cluster Helpers ───────────────────────────────────────────────

# Launch Claude Code on compute node: ccn [hours]
ccn() {
    local hours="${1:-2}" dir="$(pwd)" partition="short"
    (( hours > 2 )) && partition="epyc"
    echo "Claude Code on $partition (${hours}h) | Exit: Ctrl+C then 'exit'"
    srun -p "$partition" -c 4 --mem=16GB -t "${hours}:00:00" --pty bash -c "cd '$dir' && claude --dangerously-skip-permissions"
}

# Launch VS Code tunnel on compute node: vsc [hours]
vsc() {
    local hours="${1:-2}" partition="short"
    (( hours > 2 )) && partition="epyc"
    echo "VS Code tunnel on $partition (${hours}h) | Connect: https://vscode.dev/tunnel/<name>"
    srun -p "$partition" -c 32 --mem=64GB -t "${hours}:00:00" --pty bash -c "module load vscode && code tunnel"
}

# Quick interactive node: node [hours] [partition]
node() {
    local hours="${1:-2}" partition="${2:-short}"
    (( hours > 2 )) && [[ "$partition" == "short" ]] && partition="epyc"
    srun -p "$partition" -c 4 --mem=16GB -t "${hours}:00:00" --pty bash -l
}

# GPU interactive node: gpunode [hours]
gpunode() {
    local hours="${1:-1}"
    srun -p gpu --gres=gpu:1 -c 8 --mem=32GB -t "${hours}:00:00" --pty bash -l
}

# Job monitoring aliases
alias sq='squeue -u $USER -o "%.10i %.12j %.10P %.8T %.10M %.10l %.6C %.10m %R" --sort=-S'
alias sqstart='squeue -u $USER --start -o "%.10i %.12j %.10P %.8T %.19S %.10l %R"'
alias sqwatch='watch -n 5 "squeue -u $USER -o \"%.10i %.12j %.10P %.8T %.10M %.10l %.6C %R\""'
alias sqgpu='squeue -p gpu,short_gpu,preempt_gpu -o "%.10i %.12j %.10P %.8u %.8T %.10M %b %R"'

# GPU availability
alias gpus='sinfo -p gpu,short_gpu,preempt_gpu -O "NodeList:12,Gres:20,GresUsed:20,StateLong:12,Partition:14" --noheader'

# Job helpers: eff JOBID, joblog JOBID, joberr JOBID
eff() { seff "$1"; }
joblog() { tail -f "${2:-logs}"/*_"$1".out 2>/dev/null || echo "Log not found"; }
joberr() { tail -f "${2:-logs}"/*_"$1".err 2>/dev/null || echo "Log not found"; }

# Login node cleanup
alias mymem='ps -U $USER -o pid,rss:12,etime,comm --sort=-rss | head -15'
alias killnodes='pkill -u $USER node; pkill -u $USER -f "npm exec notebo"'

# ── End HPCC Helpers ───────────────────────────────────────────────────────
```

### Installation Steps

When configuring for a user:

1. **Check if already configured:**
   ```bash
   grep -q "# ── UCR HPCC Cluster Helpers" ~/.bashrc && echo "Already configured" || echo "Not configured"
   ```

2. **If not configured, append the block above to `~/.bashrc`**

3. **Remind user to reload:**
   ```bash
   source ~/.bashrc
   ```

### Quick Reference After Installation

| Command | Description |
|---------|-------------|
| `ccn` | Launch Claude Code (2h default) |
| `ccn 24` | Launch Claude Code for 24h |
| `vsc` | Launch VS Code tunnel (2h default) |
| `vsc 8` | Launch VS Code tunnel for 8h |
| `node` | Interactive shell (2h default) |
| `gpunode` | GPU interactive shell (1h default) |
| `sq` | Show my jobs |
| `sqwatch` | Watch my jobs (live refresh) |
| `sqgpu` | Show all GPU jobs |
| `gpus` | Show GPU availability |
| `eff JOBID` | Job efficiency report |
| `joblog JOBID` | Tail job stdout |
| `joberr JOBID` | Tail job stderr |
| `mymem` | Check my memory usage |
| `killnodes` | Kill zombie node processes |

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

### Login Node Memory Limits

**IMPORTANT:** Login nodes enforce per-user memory limits (typically 1 GB via cgroups). Running memory-intensive tools like Claude Code, VS Code remote sessions, or Jupyter kernels on login nodes can trigger the OOM killer.

**Symptoms of hitting the limit:**
- Processes getting killed randomly
- `dmesg` shows: `Memory cgroup out of memory: Killed process ... constraint=CONSTRAINT_MEMCG`

**Check for OOM kills:**
```bash
dmesg -T | grep -i "oom\|killed" | tail -10
```

**Check your current memory usage:**
```bash
ps -U $USER -o pid,rss:12,comm --sort=-rss | head -15
```

**Solution:** Run memory-intensive tools on compute nodes via `srun`:
```bash
srun -p short -c 4 --mem=16GB -t 2:00:00 --pty bash -l
```

**Clean up zombie processes:** Old VS Code sessions and Jupyter kernels often leave orphaned `node` processes consuming memory:
```bash
# Check for old node processes
ps -U $USER -o pid,rss:12,etime,comm --sort=-rss | grep node

# Kill them
pkill -u $USER node
pkill -u $USER -f "npm exec notebo"
```

### Claude Code & VS Code on HPCC

**Important:** Run these tools on compute nodes, not login nodes. Use the auto-configured shortcuts (see [Auto-Configuration](#auto-configuration)):

| Command | Description |
|---------|-------------|
| `ccn` | Launch Claude Code (2h, auto-selects partition) |
| `ccn 24` | Launch Claude Code for 24 hours |
| `vsc` | Launch VS Code tunnel (2h) |
| `vsc 8` | Launch VS Code tunnel for 8 hours |

**VS Code first-time setup:**
1. Run `vsc` — it prompts for GitHub authorization
2. Follow the link and enter the code
3. Connect via `https://vscode.dev/tunnel/<name>` or desktop VS Code "Remote - Tunnels" extension

**To exit:** `Ctrl+C` to stop the app, then `exit` to end the SLURM job.

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

Many tools cache to `~/.cache` by default, which quickly fills the home quota. Common offenders and typical sizes:

| Cache directory | What it stores | Typical size |
|----------------|---------------|-------------|
| `~/.cache/uv/` | uv package cache | 10–50 GB |
| `~/.cache/pip/` | pip download cache | 5–20 GB |
| `~/.cache/huggingface/` | HF model weights | 5–50+ GB |
| `~/.cache/torch/` | PyTorch hub models | 1–5 GB |
| `~/.cache/conda/` | conda package cache | 1–10 GB |
| `~/.cache/nvidia/` | CUDA/cuDNN caches | < 1 GB |
| `~/.cache/matplotlib/` | font cache | < 1 MB |
| `~/.cache/wandb/` | W&B run cache | varies |
| `~/.cache/singularity/` | container images | 1–20 GB |

**Diagnose:** Check what's using space:
```bash
check_quota home
du -sh ~/.cache/*/  2>/dev/null | sort -rh | head -15
```

**Clean:** Safe to delete — these are all regeneratable caches:
```bash
rm -rf ~/.cache/uv
rm -rf ~/.cache/pip
rm -rf ~/.cache/huggingface
rm -rf ~/.cache/torch
rm -rf ~/.cache/conda
rm -rf ~/.cache/nvidia
rm -rf ~/.cache/matplotlib
rm -rf ~/.cache/wandb
rm -rf ~/.cache/singularity
rm -rf ~/.cache/YAPF
```

**Redirect (permanent fix):** Add to `~/.bashrc` so caches go to bigdata instead of home:
```bash
# ── Redirect caches to bigdata (home is only 20-50GB) ──
export PIP_CACHE_DIR=/bigdata/labname/username/.cache/pip
export UV_CACHE_DIR=/bigdata/labname/username/.cache/uv
export HF_HOME=/bigdata/labname/username/.cache/huggingface
export TORCH_HOME=/bigdata/labname/username/.cache/torch
export CONDA_PKGS_DIRS=/bigdata/labname/username/.cache/conda/pkgs
export SINGULARITY_CACHEDIR=/bigdata/labname/username/.cache/singularity
export WANDB_DIR=/bigdata/labname/username/.cache/wandb
export MPLCONFIGDIR=/bigdata/labname/username/.cache/matplotlib
```

Create the target directories:
```bash
mkdir -p /bigdata/labname/username/.cache/{pip,uv,huggingface,torch,conda/pkgs,singularity,wandb,matplotlib}
```

**Important:** After adding redirects to `~/.bashrc`, clean the old `~/.cache` directories to reclaim space. The redirects only affect future caching — existing cached files stay in home until manually removed.

### Data Storage Strategy

| What | Where | Why |
|------|-------|-----|
| Code & scripts | `/bigdata/.../workspace/` | Version-controlled, plenty of space |
| Conda/uv envs | `/bigdata/.../` (via config) | Envs can be multi-GB |
| Raw input data | `/bigdata/.../data/` | Persistent, shared with lab |
| Job results | `/bigdata/.../results/` | Persistent, backed up weekly |
| Temp/intermediate | `$SCRATCH` (in jobs) | Fast local SSD, auto-cleaned |
| Configs/dotfiles | `/rhome/` | Small, backed up daily |

## Best Practices: Writing Production sbatch Scripts

When creating sbatch scripts for real workloads (not just quick tests), follow these patterns to make scripts robust, self-documenting, and easy to reuse.

### Script Structure

A well-structured sbatch script has these sections in order:

1. **SBATCH directives** — resource requests
2. **Safety flags** — `set -euo pipefail` (fail fast on errors)
3. **Self-submit with generic GPU request** (optional, for GPU jobs)
4. **Path definitions** — all paths in one place at the top
5. **Environment setup** — module loads, SSL fixes, venv setup
6. **Diagnostics banner** — print node, GPU, CUDA info for debugging
7. **Work steps** — with skip-if-done guards for idempotency

### Self-Submit with Generic GPU Request

This pattern lets you run a GPU script directly (`./script.sh`) instead of manually typing `sbatch -p ... --gres=gpu:1 script.sh`. When run outside SLURM, it submits itself with a generic GPU request:

```bash
#!/bin/bash -l
#SBATCH --job-name="my_gpu_job"
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

# ── Self-submit with generic GPU request ─────────────────────────────
# When run outside SLURM, submit itself and let SLURM pick the best GPU.
if [ -z "${SLURM_JOB_ID:-}" ]; then
    PARTITION="${PARTITION:-short_gpu}"
    mkdir -p logs
    echo "Submitting to $PARTITION with generic GPU request"
    exec sbatch -p "$PARTITION" --gres=gpu:1 "$0" "$@"
fi
```

**How it works:**
- `SLURM_JOB_ID` is only set when running inside a SLURM job — so the `if` block only runs when executed directly
- Uses `--gres=gpu:1` (no specific type) — SLURM picks the best available node and GPU
- `exec sbatch ... "$0" "$@"` replaces the current shell with the sbatch submission, passing through any CLI arguments
- Override the partition with `PARTITION=gpu ./script.sh`

**Why NOT auto-select a specific GPU type:** Scripting GPU type selection (e.g., `--gres=gpu:a100:1`) at submission time is unreliable:
1. **Stale availability** — A GPU free at submission may be taken by the time the job actually starts
2. **Column truncation** — `sinfo` output columns can truncate long GPU type names, breaking grep-based parsing
3. **All-or-nothing** — Requesting a specific type prevents SLURM from scheduling on other available types, causing jobs to queue indefinitely when that type fills up

Use generic `--gres=gpu:1` and let SLURM's scheduler handle GPU assignment. Only use `--gres=gpu:TYPE:1` when you truly need a specific GPU (e.g., for VRAM requirements), and accept that the job may wait longer.

### Diagnostics Banner

Always print environment info at the start of your job for debugging failed runs:

```bash
echo "============================================"
echo "  Job: $SLURM_JOB_NAME"
echo "  Node:  $(hostname)"
echo "  GPU:   $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "  CUDA:  $(nvcc --version 2>/dev/null | tail -1 || echo 'N/A')"
echo "============================================"
```

### SSL Certificate Fix

HPC nodes often have SSL issues when downloading from HuggingFace, PyPI, or GitHub. Add this after `module load`:

```bash
export SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-bundle.crt
```

### Idempotent Setup Functions

Wrap expensive setup (venv creation, package installs) in functions that skip if already done:

```bash
setup_venv() {
    if [ -f "$VENV/bin/python" ] && "$VENV/bin/python" -c "import torch" 2>/dev/null; then
        echo "[Setup] Venv OK"
        return
    fi
    echo "[Setup] Creating venv..."
    # --seed includes pip and setuptools in the venv (without it, only uv pip works)
    uv venv "$VENV" --python python3.11 --seed
    # Use the venv's pip for installs that compile C extensions (uv pip
    # strips pkg_resources, which breaks some build-time imports)
    "$VENV/bin/pip" install --upgrade pip "setuptools<71" wheel
    "$VENV/bin/pip" install torch torchvision
}

setup_venv
```

### Skip-If-Done Guards

For multi-step pipelines, skip steps whose output already exists:

```bash
if [ -d "$OUTPUT_DIR" ] && [ "$(ls -1 "$OUTPUT_DIR"/*.png 2>/dev/null | wc -l)" -gt 0 ]; then
    echo "[Skip] Output already exists at $OUTPUT_DIR"
else
    python process.py --output "$OUTPUT_DIR"
fi
```

## Job Monitoring Utility

For projects with multiple SLURM jobs, use a monitoring script to quickly check status, tail logs, and manage jobs. See the `templates/monitor.sh` template for a reusable utility that provides:

- `./monitor.sh` — show all your jobs
- `./monitor.sh watch` — live refresh every 5s
- `./monitor.sh log JOBID` — tail stdout log
- `./monitor.sh err JOBID` — tail stderr log
- `./monitor.sh info JOBID` — full job details
- `./monitor.sh eff JOBID` — resource efficiency (completed jobs)
- `./monitor.sh gpus` — show all GPU nodes and availability
- `./monitor.sh cancel JOBID` — cancel a specific job
- `./monitor.sh cancel all` — cancel all your jobs

Copy it into your project and adjust the log directory pattern if needed (default: `logs/*_JOBID.out`).

## SLURM Resource Limits

SLURM enforces **group-level caps** on simultaneous resource usage per partition. Even if the cluster has idle GPUs, your jobs will queue if your account hits these limits.

### Checking Your Limits

```bash
sacctmgr show assoc where user=$USER format=User,Account,GrpTRES,MaxTRES -p
```

### Typical Limits (jlilab account, `short_gpu`)

| Resource | Group Limit | Per-Job Max |
|----------|-------------|-------------|
| CPUs | 48 | 16 |
| Memory | 512G | 256G |
| GPUs | 4 | — |
| Time | — | 2 hours |

### Practical Impact

- **4 GPU jobs max**: Group limit of 4 GPUs = max 4 single-GPU jobs
- **CPU bottleneck**: 48 CPUs / 4 jobs = 12 CPUs each. Requesting 16 CPUs/job only allows 3 concurrent jobs
- **Memory bottleneck**: 512G / 4 jobs = 128G each. Requesting 200G/job only allows 2 concurrent jobs

### Recommended Settings for Concurrent GPU Jobs

To maximize concurrent GPU jobs (up to 4):

```bash
--cpus-per-task=12 --mem=80G --gres=gpu:1
```

This gives: 4 × 12 = 48 CPUs, 4 × 80G = 320G memory — fits within all limits.

### SLURM Pending Reasons

| Reason | Meaning |
|--------|---------|
| `AssocGrpCpuLimit` | Your account's CPU quota is full |
| `AssocGrpMemLimit` | Your account's memory quota is full |
| `AssocGrpGRES` | Your account's GPU quota is full |
| `Resources` | Not enough free resources on any node |
| `Priority` | Other jobs have higher priority |
| `Dependency` | Waiting for dependent job to finish |

### Auto-Resubmit for Time-Limited Partitions

For `short_gpu` (2-hour limit), use this pattern to auto-resubmit on timeout:

```bash
EXIT_CODE=0
python train.py ... || EXIT_CODE=$?

if [ $EXIT_CODE -eq 143 ]; then
    # 143 = SIGTERM (128+15), sent by SLURM at time limit
    sbatch ... "$0" "$@"
fi
```

## Common Slurm Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `QOSMaxWallDurationPerJobLimit` | Exceeds partition time limit | Reduce `--time` |
| `AssocGrpCpuLimit` | Per-user CPU limit hit | Reduce `--cpus-per-task` or wait |
| `AssocGrpMemLimit` | Per-user memory limit hit | Reduce `--mem` or wait |
| `AssocGrpGRES` | Per-user GPU limit hit | Wait for GPU jobs to finish |
| `MaxSubmitJobLimit` | Over 5000 queued/running jobs | Wait for jobs to complete |
| `PartitionConfig` | Wrong account/partition pairing | Use `-A preempt` for preempt partitions |
| `QOSMinGRES` | Missing resource request | Use `--mem=100g+` for highmem, `--gres` for gpu |

## Troubleshooting: CUDA & Python Build Issues

Common pitfalls when building CUDA extensions (tiny-cuda-nn, custom PyTorch ops, etc.) on HPCC.

### GCC Too Old for CUDA Extensions

**Symptom:** Compilation fails with `"You're trying to build PyTorch with a too old version of GCC. We need GCC 9 or later."`

**Cause:** HPCC default GCC is 8.x (RHEL 8). PyTorch 2.3+ CUDA extension headers require GCC 9+.

**Fix:** Load GCC 12 before any compilation:
```bash
module load gcc/12.2.0
module load cuda/12.1
```
This must happen before activating the venv and before any `pip install` that compiles C++ extensions.

### `pkg_resources` / `setuptools` Conflicts with CUDA Builds

**Symptom:** Building packages with CUDA extensions fails with:
```
ModuleNotFoundError: No module named 'pkg_resources'
```
or:
```
ImportError: cannot import name 'packaging' from 'pkg_resources'
```

**Cause (layered):**
1. **`uv pip` strips `pkg_resources`** — uv's bundled setuptools omits the `pkg_resources` module. Any package that imports it at build time fails.
2. **PyTorch < 2.3 imports `pkg_resources.packaging`** — `torch.utils.cpp_extension` (used during CUDA extension compilation) uses `pkg_resources.packaging`, which was removed in setuptools >= 71.

**Fix:** Use `uv` only for venv creation, then use the venv's own `pip` for installs:
```bash
UV="$HOME/.local/bin/uv"
$UV venv "$VENV_DIR" --python python3.11 --seed   # --seed includes pip
"$VENV_DIR/bin/pip" install --upgrade pip "setuptools<71" wheel ninja

# Use PyTorch 2.3+ (doesn't use pkg_resources.packaging)
"$VENV_DIR/bin/pip" install torch==2.3.1 torchvision==0.18.1 \
    --index-url https://download.pytorch.org/whl/cu121
```

For packages like tiny-cuda-nn that need direct `setup.py` invocation:
```bash
cd tiny-cuda-nn/bindings/torch
"$VENV_DIR/bin/python" setup.py install
```

### `python3.11` Not Found on Compute Nodes

**Symptom:** `python3.11 -m venv` fails on compute nodes with `command not found`.

**Cause:** python3.11 installed via `uv` at `~/.local/bin/` is in `$PATH` on the login node but not consistently on compute nodes.

**Fix:** Use `uv venv` instead of `python3.11 -m venv`. uv has its own Python discovery and doesn't rely on `$PATH`:
```bash
$UV venv "$VENV_DIR" --python python3.11 --seed
```

### `uv venv` Creates Venv Without pip

**Symptom:** After `uv venv`, running `pip install` fails with `No module named pip`.

**Cause:** `uv venv` by default creates a minimal venv without pip or setuptools (unlike `python -m venv`). uv expects you to use `uv pip` instead.

**Fix:** Add the `--seed` flag to include pip and setuptools:
```bash
$UV venv "$VENV_DIR" --python python3.11 --seed
```

### Vulkan on GPU Nodes

Vulkan **is available** on HPCC GPU nodes. The NVIDIA ICD file is at:
```
/usr/share/vulkan/icd.d/nvidia_icd.x86_64.json
```

To use Vulkan in job scripts (e.g., for rendering with Kaolin, Blender, or other GPU-accelerated graphics):
```bash
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.x86_64.json
```

**Note:** The ICD file is at `/usr/share/vulkan/icd.d/`, **not** `/etc/vulkan/icd.d/` as some documentation suggests.

### Auto GPU Selection Is Unreliable — Use Generic Requests

**Symptom:** Job script auto-selected a GPU type (e.g., `--gres=gpu:a100:1`) at submission, but by the time the job starts, those GPUs are taken. Job queues indefinitely with `ReqNodeNotAvail` or `Resources` pending reason, even though other GPU types are free.

**Cause:** Three compounding issues make scripted GPU auto-selection unreliable:
1. **Stale availability** — GPU free at submission may be taken minutes/hours later when SLURM schedules the job
2. **Column truncation** — `sinfo` output columns truncate long GPU type names (e.g., `ada6000` → `ada600`), breaking grep-based parsing
3. **All-or-nothing** — Requesting `gpu:a100:1` prevents SLURM from scheduling on other types (e.g., ada6000) that have free slots

**Fix:** Use generic `--gres=gpu:1` instead of specifying a GPU type. SLURM's scheduler will pick the best available node:
```bash
# Bad — locks you into one GPU type
sbatch --gres=gpu:a100:1 script.sh

# Good — SLURM picks the best available
sbatch --gres=gpu:1 script.sh
```

To check GPU availability for informational purposes:
```bash
sinfo -N -p "$PARTITION" \
    -O "NodeList:12,Gres:20,GresUsed:20,StateLong:12" \
    --noheader 2>/dev/null
```
Compare `Gres` (total) vs `GresUsed` (allocated). If `gpu:h100:4` and `gpu:h100:4(IDX:0-3)`, all H100s are taken even if node state is `mix`.
