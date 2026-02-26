# Reference: UCR HPCC Cluster Commands

## Cluster Information

| Property | Value |
|----------|-------|
| SSH Host | `cluster.hpcc.ucr.edu` |
| Job Scheduler | Slurm |
| Module System | Environment Modules (Tcl) |
| Default Shell | bash |
| Default Partition | epyc |
| Web Access | Open OnDemand (JupyterHub, RStudio, VSCode) |

---

## Slurm Commands Quick Reference

### Job Submission

| Command | Description |
|---------|-------------|
| `sbatch script.sh` | Submit batch job |
| `sbatch -p PARTITION script.sh` | Submit to specific partition |
| `srun --pty bash -l` | Start interactive session |
| `salloc -N 4 bash -l` | Allocate nodes for multiple srun commands |

### Job Monitoring

| Command | Description |
|---------|-------------|
| `squeue -u $USER` | Show your jobs |
| `squeue -u $USER --start` | Show jobs with estimated start times |
| `scontrol show job JOBID` | Detailed job information |
| `sacct -u $USER -l` | Job history |
| `sacct -j JOBID -o JobID,State,ExitCode,MaxRSS,Elapsed` | Specific job details |
| `sacct -u $USER -S 2024-01-01 -E 2024-12-31 -l` | Historical range query |
| `seff JOBID` | Resource efficiency report |

### Job Control

| Command | Description |
|---------|-------------|
| `scancel JOBID` | Cancel a job |
| `scancel -u $USER` | Cancel all your jobs |
| `scancel --state=PENDING -u $USER` | Cancel pending jobs only |
| `scontrol hold JOBID` | Hold a pending job |
| `scontrol release JOBID` | Release a held job |

### Cluster Status

| Command | Description |
|---------|-------------|
| `sinfo` | Show partition info |
| `sinfo -p PARTITION` | Show specific partition |
| `sinfo -N -o "%N %G %c %m %P %T" --noheader \| grep gpu` | All GPU nodes with type, CPUs, RAM, state |
| `sinfo -p gpu,short_gpu,preempt_gpu -O "NodeList:12,Gres:20,GresUsed:20,StateLong:12,Partition:14" --noheader` | GPU availability (idle vs used) |
| `scontrol show node NODENAME` | Full details for a specific node |
| `group_cpus` | Cores used by your group |
| `slurm_limits` | Your resource limits |
| `jobMonitor` | Cluster activity summary |

---

## SBATCH Directives

### Resource Allocation

| Directive | Description | Example |
|-----------|-------------|---------|
| `--nodes=N` | Number of nodes | `--nodes=2` |
| `--ntasks=N` | Number of tasks (MPI) | `--ntasks=32` |
| `--cpus-per-task=N` | CPUs per task (threading) | `--cpus-per-task=8` |
| `--mem=X` | Memory per job | `--mem=64G` |
| `--mem-per-cpu=X` | Memory per CPU | `--mem-per-cpu=4G` |
| `--time=D-HH:MM:SS` | Wall time limit | `--time=1-12:00:00` |

### GPU Resources

| Directive | Description | Example |
|-----------|-------------|---------|
| `--gres=gpu:N` | Request N GPUs | `--gres=gpu:2` |
| `--gres=gpu:TYPE:N` | Request specific GPU type | `--gres=gpu:a100:1` |

**Do not assume a fixed GPU list.** Always run `sinfo -N -o "%N %G %c %m %P %T" --noheader | grep gpu` to discover current GPU types and availability. Nodes change frequently.

### Job Configuration

| Directive | Description | Example |
|-----------|-------------|---------|
| `-p PARTITION` | Partition/queue | `-p gpu` |
| `-A ACCOUNT` | Account (for preempt) | `-A preempt` |
| `--job-name=NAME` | Job name | `--job-name="analysis"` |
| `--output=FILE` | Stdout file | `--output=job_%j.out` |
| `--error=FILE` | Stderr file | `--error=job_%j.err` |
| `--mail-user=EMAIL` | Email address | `--mail-user=user@ucr.edu` |
| `--mail-type=TYPE` | Email triggers | `--mail-type=ALL` |
| `--array=RANGE` | Array job (max 2500) | `--array=1-100` |
| `--constraint=X` | Hardware filter | `--constraint=intel` |

---

## Partitions

| Partition | Max Time | Default Time | Per-User Limit | Use Case |
|-----------|----------|--------------|----------------|----------|
| `epyc` (default) | 30 days | 7 days | 384 cores, 1TB mem | AMD EPYC nodes |
| `intel` | 30 days | 7 days | 384 cores, 1TB mem | Intel nodes |
| `batch` | 30 days | 7 days | 384 cores, 1TB mem | General CPU |
| `short` | 2 hours | 2 hours | 384 cores, 1TB mem | Quick CPU jobs |
| `highmem` | 30 days | 2 days | 32 cores, 2TB mem | Large memory (min 100GB) |
| `highclock` | 7 days | 12 hours | 32 cores, 256GB mem | High clock speed, low parallelism |
| `gpu` | 7 days | 12 hours | 4 GPUs, 48 cores, 512GB mem | GPU workloads |
| `short_gpu` | 2 hours | 2 hours | 4 GPUs, 48 cores, 512GB mem | Quick GPU jobs |
| `preempt` | 24 hours | 2 hours | Same as CPU | Preemptible (use `-A preempt`) |
| `preempt_gpu` | 24 hours | 2 hours | 1 GPU | Preemptible GPU (use `-A preempt`) |

**Group Limits:** 768 cores and 8 GPUs across all users in a group. Max 5000 queued/running jobs per user.

---

## Module Commands

| Command | Description |
|---------|-------------|
| `module avail` | List available modules |
| `module avail NAME` | Search for module |
| `module load NAME` | Load module |
| `module load NAME/VERSION` | Load specific version |
| `module unload NAME` | Unload module |
| `module list` | Show loaded modules |
| `module purge` | Unload all modules |
| `module help` | Show module help |

Note: This cluster uses Tcl Environment Modules. `module spider` is **not** available.

### Common Modules

| Module | Description |
|--------|-------------|
| `miniconda3` | Minimal Python 3 with conda |
| `anaconda` | Full Anaconda distribution |
| `R/X.X.X` | R language |
| `gcc/X.X.X` | GNU compiler |
| `openmpi` | MPI library |
| `cuda/X.X` | NVIDIA CUDA toolkit |

---

## Conda / Mamba Commands

`mamba` is available as a faster drop-in replacement for `conda` in most commands.

| Command | Description |
|---------|-------------|
| `conda create -n NAME python=3.10` | Create environment |
| `conda activate NAME` | Activate environment |
| `conda deactivate` | Deactivate environment |
| `conda env list` | List environments |
| `conda install PACKAGE` | Install package |
| `conda install -c CHANNEL PACKAGE` | Install from channel |
| `conda env remove --name NAME` | Delete environment |
| `conda env export > env.yml` | Export environment |
| `conda env create -f env.yml` | Create from file |
| `mamba install PACKAGE` | Install with mamba (faster) |
| `mamba create -n NAME python=3.10` | Create env with mamba |

### Jupyter Kernel Registration

```bash
conda activate myenv
conda install ipykernel
python -m ipykernel install --user --name myenv --display-name "My Env"
```

---

## Storage Paths

| Location | Path | Quota | Backup |
|----------|------|-------|--------|
| Home | `/rhome/USERNAME` | 20 GB | Daily, 1 week |
| Bigdata (shared) | `/bigdata/LABNAME/shared` | Lab purchase | Weekly, 1 month |
| Bigdata (personal) | `/bigdata/LABNAME/USERNAME` | Lab purchase | Weekly, 1 month |
| Scratch | `/scratch` (`$SCRATCH`) | None | None (auto-deleted after job) |
| Temp | `/tmp` | Node disk | None |
| RAM disk | `/dev/shm` | Uses job memory | None |

### Storage Commands

| Command | Description |
|---------|-------------|
| `check_quota home` | Check home quota |
| `check_quota bigdata` | Check bigdata quota |
| `du -sh DIRECTORY` | Directory size |
| `du -sch *` | Size of subdirectories |
| `mmlssnapshot home` | List home snapshots |
| `mmlssnapshot bigdata` | List bigdata snapshots |

### Snapshot Paths

- Home: `/rhome/.snapshots/daily_YYYYMMDD/USERNAME/`
- Bigdata: `/bigdata/.snapshots/weekly_YYYYMMDD/LABNAME/`

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `$SLURM_JOB_ID` | Current job ID |
| `$SLURM_ARRAY_TASK_ID` | Array task index |
| `$SLURM_NTASKS` | Number of tasks |
| `$SLURM_CPUS_PER_TASK` | CPUs per task |
| `$SLURM_MEM_PER_NODE` | Memory per node |
| `$SLURM_SUBMIT_DIR` | Submission directory |
| `$SLURM_JOB_NODELIST` | Assigned nodes |
| `$CUDA_VISIBLE_DEVICES` | Assigned GPUs (gpu partition) |
| `$SCRATCH` | Scratch directory path |

---

## SSH & Tunneling

### Basic Connection

```bash
ssh -X username@cluster.hpcc.ucr.edu
```

### Port Forwarding (for Jupyter, etc.)

```bash
ssh -NL LOCAL_PORT:NODE:REMOTE_PORT username@cluster.hpcc.ucr.edu
```

Example:
```bash
ssh -NL 8888:i001:8888 username@cluster.hpcc.ucr.edu
```

### VNC Desktop

Start VNC on a compute node, then tunnel:
```bash
# On cluster (inside srun session)
vncserver -fg

# On local machine
ssh -L 5901:NodeName:5901 cluster.hpcc.ucr.edu
vncviewer localhost:5901
```

---

## Hardware Constraints

Use `--constraint` to request specific hardware:

| Constraint | Description |
|------------|-------------|
| `intel` | Intel processors |
| `amd` | AMD processors |
| `rome` | AMD Rome CPUs |
| `milan` | AMD Milan CPUs |
| `gpu_latest` | Newest GPUs |
| `gpu_prev` | Previous gen GPUs |
| `gpu_legacy` | Oldest GPUs |

Example:
```bash
srun -p short --constraint="amd&rome" --pty bash -l
```

---

## Output File Patterns

| Pattern | Description |
|---------|-------------|
| `%j` | Job ID |
| `%a` | Array task ID |
| `%A` | Array master job ID |
| `%N` | Node name |
| `%u` | Username |

Example:
```bash
#SBATCH --output=logs/job_%j_%a.out
```

---

## Common Slurm Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Resources` | Awaiting availability | Job starts when resources free |
| `Priority` | Higher-priority jobs pending | Fair-share queue delay |
| `QOSMaxWallDurationPerJobLimit` | Exceeds partition time limit | Reduce `--time` |
| `AssocGrpCpuLimit` | Per-user CPU limit exceeded | Wait for running jobs to finish |
| `AssocGrpMemLimit` | Per-user memory limit exceeded | Wait for running jobs to finish |
| `AssocGrpGRES` | Per-user GPU limit exceeded | Wait for GPU jobs to finish |
| `MaxSubmitJobLimit` | Over 5000 queued/running jobs | Wait for jobs to complete |
| `ReqNodeNotAvail` | Overlaps maintenance window | Reduce runtime or wait |
| `PartitionConfig` | Wrong account/partition pairing | Use `-A preempt` for preempt partitions |
| `QOSMinGRES` | Minimum resources not requested | `--mem=100g+` for highmem, `--gres` for gpu |
