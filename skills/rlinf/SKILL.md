---
name: rlinf
description: Troubleshooting guide and operational knowledge for RLinf RL training framework on HPCC.
---

# rlinf

Operational guide for running RLinf (Ray-based RL infrastructure) on UCR HPCC, covering common issues, debugging patterns, and configuration pitfalls.

## Environment Setup

| Variable | Value | Notes |
|----------|-------|-------|
| `VK_ICD_FILENAMES` | `/usr/share/vulkan/icd.d/nvidia_icd.x86_64.json` | HPCC path, not `/etc/vulkan/` |
| `VK_DRIVER_FILES` | Same as above | Required for ManiSkill GPU sim |
| `EMBODIED_PATH` | `<repo>/examples/embodiment` | Hydra config search path |
| `MUJOCO_GL` | `egl` | Headless rendering |
| `PYOPENGL_PLATFORM` | `egl` | Headless rendering |
| `SSL_CERT_FILE` | `/etc/ssl/certs/ca-bundle.crt` | HPCC SSL fix |

## Critical Debugging Patterns

### 1. Demo Buffer Format (trajectory_index.json)

RLinf's `TrajectoryReplayBuffer.load_checkpoint()` expects a specific JSON structure. Getting this wrong causes **silent infinite busy-wait** (no error, no crash, just hangs).

**Correct format:**
```json
{
  "trajectory_index": {
    "0": {
      "num_samples": 16,
      "trajectory_id": 0,
      "max_episode_length": 50,
      "shape": [2, 8],
      "model_weights_id": "demo_uuid_0",
      "filename": "trajectory_0_demo_uuid_0.pt"
    }
  },
  "trajectory_id_list": [0, 1, 2, ...]
}
```

**Wrong format (causes hang):**
```json
{
  "0": {"model_weights_id": "...", "filename": "..."}
}
```

**Why it hangs:** `load_checkpoint()` looks for `index_data.get("trajectory_index", {})` and `index_data.get("trajectory_id_list", [])`. If these keys are missing, the buffer loads with `size=0`, and `ReplayBufferDataset.__iter__()` spins forever in a busy-wait loop checking `is_ready()` which always returns False.

**metadata.json must include:**
```json
{
  "trajectory_format": "pt",
  "size": <num_trajectories>,
  "total_samples": <total>,
  "trajectory_counter": <num_trajectories>,
  "seed": 1234
}
```
The `"size"` key is critical — without it, `metadata.get("size", 0)` returns 0.

### 2. Hydra Config Overrides

| Pattern | When to Use | Example |
|---------|-------------|---------|
| `key=value` | Override existing key | `runner.save_interval=100` |
| `++key=value` | Force add/override | `++cluster.component_placement={...}` |
| `+key=value` | Add new key to struct | `+runner.resume_dir=/path` |

**Pitfall:** Combined placement keys like `actor,env,rollout: 0` in YAML cannot be partially overridden via CLI. Split them into separate keys in the base YAML first.

### 3. Script Safety with `set -euo pipefail`

Glob failures in `ls -d` with no matches return exit code 1, which `set -e` treats as fatal. Always append `|| true`:

```bash
LATEST=$(ls -d ${DIR}/global_step_* 2>/dev/null | sort -n | tail -1 || true)
```

### 5. ManiSkill Sim Backend

- **Must use** `sim_backend: "gpu"` — CPU mode doesn't support vectorized envs
- Vulkan required — cannot run on login nodes (no GPU)
- Demo conversion must run on GPU nodes via sbatch

## RLPD-Specific Notes

RLPD (RL with Prior Data) adds a `demo_buffer` alongside the `replay_buffer`:

| Parameter | SAC | RLPD |
|-----------|-----|------|
| `num_q_heads` | 2 | 10 |
| `actor_agg_q` | min | mean |
| `critic_subsample_size` | 2 | 2 |
| `demo_buffer` | none | loaded from disk |

The `ReplayBufferDataset` mixes 50/50 from replay and demo buffer when demo_buffer is provided.

## Debugging Stuck Training

1. **Check stderr log line count over time** — if not growing, job is hung
2. **Look for "Replay buffer size X < Y, skipping training"** — buffer not filling
3. **Check demo_buffer format** — most common cause of silent hang
4. **Check tensorboard event file size** — growing = training active
5. **Don't assume GPU contention** — multiple jobs on same node work fine if each gets its own GPU via SLURM `--gres`

## Auto-Resubmit Pattern

```bash
EXIT_CODE=0
python train_embodied_agent.py ... || EXIT_CODE=$?

if [ $EXIT_CODE -eq 143 ]; then
    # SIGTERM from SLURM time limit
    sbatch ... "$SCRIPT_PATH" "$ARGS"
fi
```

Exit code 143 = SIGTERM (128 + 15), sent by SLURM when time limit reached.
