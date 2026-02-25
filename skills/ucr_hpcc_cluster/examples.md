# Examples: UCR HPCC Cluster Usage

## Example 1: Running a Python Script

**User Request:** "Run my Python analysis script on the cluster"

### Step 1: Create Job Script

```bash
#!/bin/bash -l
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=2:00:00
#SBATCH --job-name="python_analysis"
#SBATCH -p short

module load miniconda3
conda activate myenv
python analysis.py
```

### Step 2: Submit and Monitor

```bash
sbatch job.sh                    # Submit job
squeue -u $USER --start          # Check status
seff JOBID                       # Check resource usage after completion
```

---

## Example 2: Interactive Data Exploration

**User Request:** "I need to interactively explore a large dataset"

### Start Interactive Session

```bash
# Request resources for interactive work
srun -p short -t 2:00:00 -c 8 --mem=32GB --pty bash -l

# Load software
module load miniconda3
conda activate myenv

# Start Jupyter (optional)
jupyter notebook --no-browser --port=8888
```

### Tunnel from Local Machine

```bash
ssh -NL 8888:NodeName:8888 username@cluster.hpcc.ucr.edu
```

Then open `http://localhost:8888` in your browser.

---

## Example 3: GPU Machine Learning Job

**User Request:** "Train my PyTorch model on GPU"

### GPU Job Script

```bash
#!/bin/bash -l
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=1-00:00:00
#SBATCH --job-name="pytorch_train"
#SBATCH -p gpu
#SBATCH --gres=gpu:1

module load miniconda3
conda activate pytorch_env

python train.py --epochs 100 --batch-size 32
```

### Submit

```bash
sbatch gpu_job.sh
squeue -u $USER                  # Monitor queue
```

---

## Example 4: Array Job for Parameter Sweep

**User Request:** "Run my simulation with 100 different parameters"

### Array Job Script

```bash
#!/bin/bash -l
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=1:00:00
#SBATCH --job-name="param_sweep"
#SBATCH -p batch
#SBATCH --array=1-100

# Each task gets a unique ID
PARAM_ID=${SLURM_ARRAY_TASK_ID}

module load miniconda3
conda activate myenv

python simulate.py --param-id $PARAM_ID --output results_${PARAM_ID}.csv
```

### Submit and Monitor

```bash
sbatch array_job.sh
squeue -u $USER                  # See all array tasks
scancel JOBID                    # Cancel entire array
scancel JOBID_50                 # Cancel specific task
```

---

## Example 5: Setting Up a New Conda Environment

**User Request:** "Install packages for my bioinformatics project"

### Best Practice: Install on Compute Node

```bash
# Start interactive session (avoid memory issues on login node)
srun -p short -c 4 --mem=10g --pty bash -l

# Load conda
module load miniconda3

# Create environment
conda create -n bioinfo python=3.10

# Activate and install
conda activate bioinfo
conda install -c bioconda samtools bwa bowtie2
conda install -c conda-forge pandas numpy scipy

# Verify
conda list
```

### Configure Storage Location

Create `~/.condarc` to store environments in bigdata:
```yaml
channels:
  - bioconda
  - conda-forge
  - defaults
pkgs_dirs:
  - ~/bigdata/.conda/pkgs
envs_dirs:
  - ~/bigdata/.conda/envs
auto_activate_base: false
```

---

## Example 6: Large Memory Job

**User Request:** "Process a 500GB file that needs lots of RAM"

### High Memory Job

```bash
#!/bin/bash -l
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=500G
#SBATCH --time=7-00:00:00
#SBATCH --job-name="highmem_job"
#SBATCH -p highmem

module load miniconda3
conda activate myenv

python process_large_file.py --input bigfile.dat --output results.csv
```

---

## Example 7: MPI Parallel Job

**User Request:** "Run my MPI simulation across multiple nodes"

### MPI Job Script

```bash
#!/bin/bash -l
#SBATCH --nodes=4
#SBATCH --ntasks=128
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=4G
#SBATCH --time=2-00:00:00
#SBATCH --job-name="mpi_sim"
#SBATCH -p batch

module load openmpi
module load my_mpi_app

mpirun my_simulation input.dat
```

---

## Common Workflows

### Check Quota Before Large Jobs

```bash
check_quota home
check_quota bigdata
```

### Recover Deleted File from Snapshot

```bash
# List available snapshots
ls /rhome/.snapshots/

# Copy file from snapshot
cp /rhome/.snapshots/daily_YYYYMMDD/username/deleted_file.txt ~/
```

### Debug a Failed Job

```bash
# Check job exit status
sacct -j JOBID -o JobID,State,ExitCode,MaxRSS,Elapsed

# View job output
cat slurm-JOBID.out

# Check if ran out of memory or time
seff JOBID
```
