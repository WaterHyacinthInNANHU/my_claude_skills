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
#SBATCH --gres=gpu:a100:1

module load miniconda3
module load cuda
conda activate pytorch_env

# Verify GPU assignment
nvidia-smi
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"

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
#SBATCH -p epyc
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

Note: Array jobs have a 2500 job limit per array submission.

---

## Example 5: Setting Up a New Conda Environment

**User Request:** "Install packages for my bioinformatics project"

### Best Practice: Install on Compute Node

```bash
# Start interactive session (avoid memory issues on login node)
srun -p short -c 4 --mem=10g --pty bash -l

# Load conda
module load miniconda3

# Create environment (mamba is faster)
mamba create -n bioinfo python=3.10

# Activate and install
conda activate bioinfo
mamba install -c bioconda samtools bwa bowtie2
mamba install -c conda-forge pandas numpy scipy

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

### Register as Jupyter Kernel (Optional)

```bash
conda activate bioinfo
conda install ipykernel
python -m ipykernel install --user --name bioinfo --display-name "Bioinfo (Python 3.10)"
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

Note: The `highmem` partition requires a minimum memory request of 100GB.

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

## Example 8: Preemptible Jobs for Extra Resources

**User Request:** "I need more cores than my lab limit allows"

### Preemptible Job Script

```bash
#!/bin/bash -l
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --job-name="preempt_job"
#SBATCH -p preempt
#SBATCH -A preempt

# Preemptible jobs can be killed anytime (1-min grace period)
# Use checkpointing to save progress periodically

module load miniconda3
conda activate myenv

python long_running_task.py --checkpoint-dir ./checkpoints
```

Note: Preempt partitions require `-A preempt`. Resources don't count against lab quotas, but jobs may be requeued at any time.

---

## Example 9: New Project Setup from Scratch

**User Request:** "I'm starting a new Python project on the cluster"

### Step 1: Set Up Directory Structure

```bash
# Create project on bigdata (not home)
mkdir -p /bigdata/labname/username/workspace/my_project
mkdir -p /bigdata/labname/username/workspace/my_project/{scripts,data,results}

# Symlink for easy access (one-time)
ln -sf /bigdata/labname/username/workspace ~/workspace

cd ~/workspace/my_project
```

### Step 2: Redirect Caches to Bigdata (One-Time)

Create `~/.condarc`:
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

Add to `~/.bashrc`:
```bash
export PIP_CACHE_DIR=/bigdata/labname/username/.cache/pip
export UV_CACHE_DIR=/bigdata/labname/username/.cache/uv
export HF_HOME=/bigdata/labname/username/.cache/huggingface
```

### Step 3a: Create Conda Environment

```bash
# Install on compute node
srun -p short -c 4 --mem=10g --pty bash -l
module load miniconda3
mamba create -n my_project python=3.11
conda activate my_project
mamba install numpy pandas matplotlib
```

Job script using conda:
```bash
#!/bin/bash -l
#SBATCH -p epyc --cpus-per-task=4 --mem=16G --time=4:00:00
module load miniconda3
conda activate my_project
cd ~/workspace/my_project
python scripts/analyze.py
```

### Step 3b: Or Use uv Instead

```bash
# Install uv (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

cd ~/workspace/my_project
uv init
uv add numpy pandas matplotlib
```

Job script using uv:
```bash
#!/bin/bash -l
#SBATCH -p epyc --cpus-per-task=4 --mem=16G --time=4:00:00
cd ~/workspace/my_project
uv run python scripts/analyze.py
```

### Step 4: R Project Setup (If Needed)

Create `~/.Renviron` to redirect R libraries to bigdata:
```
R_LIBS_USER=/bigdata/labname/username/R/%p-library/%v
```

Then install packages normally in R:
```r
install.packages("tidyverse")
BiocManager::install("DESeq2")
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
mmlssnapshot home

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

### Check Resource Efficiency

After a job completes, review efficiency to optimize future requests:
```bash
seff JOBID
# Look for:
#   CPU Efficiency - low means over-requested cores
#   Memory Efficiency - aim for ~80% (request ~20% more than needed)
```

### Use Scratch for Fast I/O

```bash
#!/bin/bash -l
#SBATCH -p epyc
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=4:00:00

# Copy data to fast node-local scratch
cp /rhome/$USER/large_input.dat $SCRATCH/
cd $SCRATCH

# Run with fast local I/O
python process.py --input large_input.dat --output results.dat

# Copy results back
cp results.dat /rhome/$USER/results/
```
