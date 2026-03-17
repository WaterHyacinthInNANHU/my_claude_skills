# Experiment Monitoring Guide

## Smoke Test (Stage 1)

### Quick Validation Run

```bash
# Run minimal training to catch errors
python train.py --epochs 1 --debug 2>&1 | tee logs/smoke_test.log

# Or with reduced data
python train.py --data_fraction 0.01 --epochs 1 2>&1 | tee logs/smoke_test.log
```

### Common Smoke Test Failures

| Error Type | Check For | Fix |
|------------|-----------|-----|
| ImportError | Missing dependencies | `pip install <package>` |
| FileNotFoundError | Wrong paths in config | Update config paths |
| CUDA OOM | Batch size too large | Reduce batch_size |
| Shape mismatch | Model/data incompatibility | Check input dimensions |
| NaN loss | Learning rate too high | Reduce lr, add gradient clipping |

### Smoke Test Checklist

- [ ] Training starts without errors
- [ ] Data loads correctly
- [ ] Model initializes
- [ ] First forward pass completes
- [ ] First backward pass completes
- [ ] Metrics are computed
- [ ] Checkpoints save correctly
- [ ] Memory usage is acceptable

## Full Training (Stage 2)

### Launch Commands

**Local (background):**
```bash
nohup python train.py <args> > logs/train.log 2>&1 &
echo $! > logs/train.pid
```

**SLURM:**
```bash
sbatch --job-name={{TAG}} job.sh
```

**tmux/screen:**
```bash
tmux new -s exp
python train.py <args> 2>&1 | tee logs/train.log
# Ctrl+B, D to detach
```

### Monitoring Commands

**Log monitoring:**
```bash
# Follow log output
tail -f logs/train.log

# Search for specific patterns
grep -E "(loss|accuracy|epoch)" logs/train.log

# Last N lines
tail -100 logs/train.log
```

**GPU monitoring:**
```bash
# Continuous GPU stats
nvidia-smi -l 5

# GPU utilization only
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 5

# Watch GPU memory
watch -n 1 nvidia-smi
```

**Process monitoring:**
```bash
# Check if training is running
ps aux | grep train.py

# Check by PID
kill -0 $(cat logs/train.pid) && echo "Running" || echo "Stopped"

# Resource usage
htop -p $(cat logs/train.pid)
```

**SLURM monitoring:**
```bash
# Job status
squeue -u $USER

# Job details
scontrol show job <job_id>

# Resource usage
sacct -j <job_id> --format=JobID,State,Elapsed,MaxRSS,MaxVMSize

# Job output
tail -f slurm-<job_id>.out
```

### Progress Indicators

**Look for in logs:**
- Epoch number / Total epochs
- Step number / Total steps
- Loss values (should decrease)
- Learning rate (if scheduled)
- Validation metrics (periodic)
- ETA estimates

**Example progress parsing:**
```bash
# Extract loss progression
grep "loss" logs/train.log | tail -20

# Count completed epochs
grep -c "Epoch.*completed" logs/train.log

# Check latest metric
grep "val_" logs/train.log | tail -5
```

### Health Checks

**Signs training is healthy:**
- [ ] Loss is decreasing (or fluctuating down)
- [ ] GPU utilization is high (>80%)
- [ ] No error messages in log
- [ ] Memory usage is stable
- [ ] Disk space is sufficient

**Warning signs:**
- Loss increasing or stuck
- GPU utilization low (<50%)
- Memory constantly growing
- Repeated warnings in log
- No output for long periods

### Intervention Points

**When to intervene:**

| Situation | Action |
|-----------|--------|
| Loss exploding (NaN/Inf) | Stop, reduce LR, add gradient clipping |
| Loss stuck | Check for bugs, try different optimizer |
| OOM errors | Reduce batch size, enable gradient checkpointing |
| Slow training | Profile code, check data loading |
| Disk full | Clear old checkpoints, increase quota |

**How to stop:**
```bash
# Graceful (if supported)
kill -SIGTERM $(cat logs/train.pid)

# Force stop
kill -9 $(cat logs/train.pid)

# SLURM
scancel <job_id>
```

## Completion Detection

### Automated Completion Check

```bash
# Poll for completion
while kill -0 $(cat logs/train.pid) 2>/dev/null; do
    echo "Still running..."
    sleep 60
done
echo "Training completed!"
```

### Success Indicators

- [ ] "Training complete" message in log
- [ ] Final checkpoint saved
- [ ] Final metrics logged
- [ ] Process exited with code 0

### Post-Completion Checklist

- [ ] Verify final checkpoint exists
- [ ] Extract final metrics from log
- [ ] Check for any errors near end of log
- [ ] Update results.tsv
- [ ] Commit checkpoint and logs

```bash
# Extract final results
tail -50 logs/train.log

# Update tracking
echo -e "$(git rev-parse --short HEAD)\t<final_metric>\tsuccess\t<description>" >> results.tsv

# Commit
git add outputs/ logs/
git commit -m "exp: <description> - <metric>"
```
