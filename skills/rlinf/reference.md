# RLinf Quick Reference

## Trajectory .pt File Format

```python
{
    "max_episode_length": 50,
    "model_weights_id": "uuid_step",
    "actions": torch.Size([T, B, action_dim]),      # [2, 8, 4]
    "intervene_flags": torch.Size([T, B, action_dim]),
    "rewards": torch.Size([T, B, 1]),
    "terminations": torch.Size([T, B, 1]),
    "truncations": torch.Size([T, B, 1]),
    "dones": torch.Size([T, B, 1]),
    "forward_inputs": {"action": [T, B, action_dim]},
    "curr_obs": {"states": [T, B, obs_dim]},         # 42 for PickCube state
    "next_obs": {"states": [T, B, obs_dim]},
}
```

## Key Source Files

| File | Purpose |
|------|---------|
| `rlinf/data/replay_buffer.py` | `TrajectoryReplayBuffer`, `load_checkpoint()`, `is_ready()` |
| `rlinf/data/embodied_buffer_dataset.py` | `ReplayBufferDataset` — the busy-wait iterator |
| `rlinf/workers/actor/fsdp_sac_policy_worker.py` | SAC training loop, demo_buffer init |
| `examples/embodiment/train_embodied_agent.py` | Entry point |
| `examples/embodiment/config/` | Hydra YAML configs |

## ManiSkill PickCube-v1

| Property | Value |
|----------|-------|
| Obs dim (state) | 42 |
| Action dim | 4 (pd_ee_delta_pos) |
| Max episode steps | 50 |
| Success criteria | Cube within 2.5cm of goal AND robot static (qvel < 0.2) |
| Reward components | reaching + grasping(+1) + placing + static, max ~5.0/step |

## SLURM Job Templates

### Single GPU training
```bash
sbatch --job-name="name" --nodes=1 --ntasks=1 \
    --cpus-per-task=12 --mem=80G --time=2:00:00 \
    -p short_gpu --gres=gpu:1 \
    --output="logs/name_%j.out" --error="logs/name_%j.err" \
    script.sh
```

## Common Errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| Job hangs after 2 rollout epochs | Demo buffer format wrong | Fix trajectory_index.json format |
| `AssocGrpMemLimit` | Group memory quota | Reduce `--mem` (80G works) |
| `AssocGrpCpuLimit` | Group CPU quota (48) | Use `--cpus-per-task=12` |
| `Key 'X' is not in struct` | Hydra missing key | Use `+key=value` prefix |
| Silent script death | `set -e` + glob failure | Add `|| true` to ls/glob commands |
| `Component X has multiple placements` | Combined YAML key + CLI override | Split combined keys in base YAML |
