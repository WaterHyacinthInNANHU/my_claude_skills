# Monitoring & Execution Guide

> Reference material for Step 4.2-4.3 of the experiment loop.
> Session protocol and early stopping heuristics are in CLAUDE.md.

## Smoke Test Checklist

Run before entering the experiment loop:

- [ ] All imports resolve
- [ ] Config loads without errors
- [ ] Data loads through symlink
- [ ] Forward pass completes (correct output shape)
- [ ] Backward pass completes (gradients exist)
- [ ] Metrics are computed
- [ ] Checkpoint saves correctly
- [ ] GPU memory within budget

### Common Smoke Test Failures

| Error | Check | Fix |
|-------|-------|-----|
| ImportError | Missing dependency | `pip install <package>` |
| FileNotFoundError | Path in config | Update config paths |
| CUDA OOM | Batch size | Reduce batch_size |
| Shape mismatch | Model vs data dims | Check input dimensions |
| NaN loss first step | LR or init | Reduce LR, check init |

### Reduced-data smoke test (alternative)
```bash
python train.py --data_fraction 0.01 --epochs 1 2>&1 | tee logs/smoke_test.log
```

## Launch Commands

### Local (background)
```bash
nohup python train.py <args> > logs/train_r<N>.log 2>&1 &
echo $! > logs/train.pid
```

### SLURM
```bash
sbatch --job-name=<tag>-r<N> job.sh
```

### tmux (interactive monitoring)
```bash
tmux new -s exp
python train.py <args> 2>&1 | tee logs/train_r<N>.log
# Ctrl+B, D to detach
```

## Monitor Script Usage

```bash
# Basic usage
./scripts/monitor.sh --log logs/train_r<N>.log --pid $(cat logs/train.pid)

# Custom interval and metrics
./scripts/monitor.sh --log logs/train_r<N>.log --interval 180 --metric "(loss|reward|val_)"

# SLURM job
./scripts/monitor.sh --slurm <job_id> --log slurm-<job_id>.out
```

The script:
- Only prints when metrics change (saves context)
- Prints `MONITOR_DONE:<status>:<time>` on completion
- Auto-detects training end via PID, SLURM state, or log staleness

## Manual Status Checks

```bash
# Process running?
kill -0 $(cat logs/train.pid) 2>/dev/null && echo "Running" || echo "Stopped"

# GPU usage
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 5

# SLURM status
squeue -j <job_id> -h -o "%T %M %l"
sacct -j <job_id> --format=JobID,State,Elapsed,MaxRSS
```

## Health Indicators

| Sign | Meaning |
|------|---------|
| GPU util >80% | Healthy — compute-bound |
| GPU util <30% | Data loading bottleneck |
| Memory growing | Possible memory leak |
| No log output for 5+ min | Check if process alive |
| Loss spikes then recovers | May be OK (LR warmup, hard batches) |
| Loss spikes and stays | Problem — consider stopping |
