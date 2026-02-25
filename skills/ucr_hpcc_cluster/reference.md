# Reference: UCR HPCC Cluster Commands

## Cluster Information

| Property | Value |
|----------|-------|
| SSH Host | `cluster.hpcc.ucr.edu` |
| Job Scheduler | Slurm |
| Module System | Lmod |
| Default Shell | bash |

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

### Job Configuration

| Directive | Description | Example |
|-----------|-------------|---------|
| `-p PARTITION` | Partition/queue | `-p gpu` |
| `--job-name=NAME` | Job name | `--job-name="analysis"` |
| `--output=FILE` | Stdout file | `--output=job_%j.out` |
| `--error=FILE` | Stderr file | `--error=job_%j.err` |
| `--mail-user=EMAIL` | Email address | `--mail-user=user@ucr.edu` |
| `--mail-type=TYPE` | Email triggers | `--mail-type=ALL` |
| `--array=RANGE` | Array job | `--array=1-100` |
| `--constraint=X` | Hardware filter | `--constraint=intel` |

---

## Partitions

| Partition | Max Time | Per-User Limit | Use Case |
|-----------|----------|----------------|----------|
| `batch` | 30 days | 384 cores, 1TB mem | General CPU |
| `epyc` | 30 days | 384 cores, 1TB mem | AMD EPYC nodes |
| `intel` | 30 days | 384 cores, 1TB mem | Intel nodes |
| `short` | 2 hours | 384 cores, 1TB mem | Quick jobs |
| `highmem` | 30 days | 32 cores, 2TB mem | Large memory |
| `gpu` | 7 days | 4 GPUs, 48 cores | GPU workloads |
| `preempt` | 24 hours | Same as CPU | Preemptible |
| `preempt_gpu` | 24 hours | 1 GPU | Preemptible GPU |

**Group Limits:** 768 cores and 8 GPUs across all users in a group.

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
| `module spider NAME` | Deep search for module |

### Common Modules

| Module | Description |
|--------|-------------|
| `miniconda3` | Python 3 with conda |
| `anaconda` | Full Anaconda distribution |
| `R/X.X.X` | R language |
| `gcc/X.X.X` | GNU compiler |
| `openmpi` | MPI library |
| `cuda` | NVIDIA CUDA toolkit |

---

## Conda Commands

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

---

## Storage Paths

| Location | Path | Quota | Backup |
|----------|------|-------|--------|
| Home | `/rhome/USERNAME` | 20 GB | Daily, 1 week |
| Bigdata (shared) | `/bigdata/LABNAME/shared` | Lab purchase | Weekly, 1 month |
| Bigdata (personal) | `/bigdata/LABNAME/USERNAME` | Lab purchase | Weekly, 1 month |
| Scratch | `/scratch` | None | None (auto-deleted) |
| Temp | `/tmp` | Node disk | None |

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
| `%N` | Node name |
| `%u` | Username |

Example:
```bash
#SBATCH --output=logs/job_%j_%a.out
```
