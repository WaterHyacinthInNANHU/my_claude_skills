# Q-Chunking Examples

## 1. Offline-to-Online: OGBench Cube Tasks (QC, recommended)

Best-of-N actor with flow matching, the primary method from the paper.

```bash
cd /path/to/qc

# QC on cube-triple (dense reward)
MUJOCO_GL=egl python main.py \
    --run_group=qc_cube_triple \
    --agent=agents/acfql.py \
    --agent.actor_type=best-of-n \
    --agent.actor_num_samples=32 \
    --env_name=cube-triple-play-singletask-task2-v0 \
    --horizon_length=5 \
    --offline_steps=1000000 \
    --online_steps=1000000 \
    --eval_interval=100000 \
    --seed=0
```

## 2. Offline-to-Online: QC-FQL (Distill-DDPG Actor)

Faster inference than best-of-N (single forward pass) but needs tuned `alpha`.

```bash
MUJOCO_GL=egl python main.py \
    --run_group=qcfql_cube_triple \
    --agent=agents/acfql.py \
    --agent.actor_type=distill-ddpg \
    --agent.alpha=100 \
    --env_name=cube-triple-play-singletask-task2-v0 \
    --horizon_length=5 \
    --offline_steps=1000000 \
    --online_steps=1000000 \
    --seed=0
```

## 3. Pure Online: QC-RLPD (SAC-based)

Online RL with 50/50 dataset/replay mixing and BC regularization.

```bash
MUJOCO_GL=egl python main_online.py \
    --run_group=qcrlpd_cube_triple \
    --agent=agents/acrlpd.py \
    --env_name=cube-triple-play-singletask-task2-v0 \
    --horizon_length=5 \
    --agent.bc_alpha=0.01 \
    --online_steps=1000000 \
    --seed=0
```

## 4. Sparse Reward Tasks (Scene, Puzzle)

Use `--sparse=True` to convert rewards to binary sparse form.

```bash
# Scene domain (sparse reward)
MUJOCO_GL=egl python main.py \
    --run_group=qc_scene_sparse \
    --agent.actor_type=best-of-n \
    --agent.actor_num_samples=32 \
    --env_name=scene-play-singletask-task0-v0 \
    --sparse=True \
    --horizon_length=5 \
    --seed=0

# Puzzle-3x3 domain (sparse reward)
MUJOCO_GL=egl python main.py \
    --run_group=qc_puzzle_sparse \
    --agent.actor_type=best-of-n \
    --agent.actor_num_samples=32 \
    --env_name=puzzle-3x3-play-singletask-task0-v0 \
    --sparse=True \
    --horizon_length=5 \
    --seed=0
```

## 5. RoboMimic Tasks

Requires datasets at `~/.robomimic/<task>/mh/low_dim_v15.hdf5`.

```bash
# Lift (easiest, max 300 steps)
MUJOCO_GL=egl python main.py \
    --run_group=qc_lift \
    --agent.actor_type=best-of-n \
    --agent.actor_num_samples=32 \
    --env_name=lift-mh-low_dim \
    --horizon_length=5 \
    --seed=0

# Can (max 300 steps)
MUJOCO_GL=egl python main.py \
    --run_group=qc_can \
    --agent.actor_type=best-of-n \
    --env_name=can-mh-low_dim \
    --horizon_length=5 \
    --seed=0

# Square (harder, max 400 steps)
MUJOCO_GL=egl python main.py \
    --run_group=qc_square \
    --agent.actor_type=best-of-n \
    --env_name=square-mh-low_dim \
    --horizon_length=5 \
    --seed=0
```

## 6. Large OGBench Datasets (100M)

For cube-quadruple with the 100M dataset, specify `--ogbench_dataset_dir` and `--dataset_replace_interval` to cycle through shards.

```bash
# Download first
wget -r -np -nH --cut-dirs=2 -A "*.npz" \
    https://rail.eecs.berkeley.edu/datasets/ogbench/cube-quadruple-play-100m-v0/

# Train with dataset shard cycling
MUJOCO_GL=egl python main.py \
    --run_group=qc_quadruple_100m \
    --agent.actor_type=best-of-n \
    --agent.actor_num_samples=32 \
    --env_name=cube-quadruple-play-singletask-task0-v0 \
    --ogbench_dataset_dir=/path/to/cube-quadruple-play-100m-v0/ \
    --dataset_replace_interval=1000 \
    --horizon_length=5 \
    --seed=0
```

## 7. Multi-Seed Experiments

```bash
for seed in 0 1 2 3 4; do
    MUJOCO_GL=egl python main.py \
        --run_group=qc_cube_triple_multiseed \
        --agent.actor_type=best-of-n \
        --agent.actor_num_samples=32 \
        --env_name=cube-triple-play-singletask-task2-v0 \
        --horizon_length=5 \
        --seed=$seed &
done
wait
```

## 8. SLURM Template

```bash
#!/bin/bash
#SBATCH --job-name=qc_train
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --array=0-4
#SBATCH --output=logs/qc_%A_%a.out

module load cuda/12.2

cd /path/to/qc
source activate qc_env

export MUJOCO_GL=egl
export WANDB_PROJECT=qc

SEED=$SLURM_ARRAY_TASK_ID

python main.py \
    --run_group=${SLURM_JOB_NAME} \
    --agent=agents/acfql.py \
    --agent.actor_type=best-of-n \
    --agent.actor_num_samples=32 \
    --env_name=cube-triple-play-singletask-task2-v0 \
    --horizon_length=5 \
    --offline_steps=1000000 \
    --online_steps=1000000 \
    --seed=$SEED
```

Submit: `sbatch train_qc.sh`

## 9. Ablations: Chunking vs N-step vs Standard

```bash
ENV=cube-triple-play-singletask-task2-v0

# QC (action chunking + n-step): the full method
MUJOCO_GL=egl python main.py --agent.actor_type=best-of-n --agent.actor_num_samples=32 \
    --env_name=$ENV --horizon_length=5 --run_group=ablation_qc --seed=0

# BFN-n (n-step only, no chunking): same horizon but critic sees single action
MUJOCO_GL=egl python main.py --agent.actor_type=best-of-n --agent.actor_num_samples=4 \
    --env_name=$ENV --horizon_length=5 --agent.action_chunking=False --run_group=ablation_nstep --seed=0

# BFN (standard, no chunking, no n-step): horizon_length=1
MUJOCO_GL=egl python main.py --agent.actor_type=best-of-n --agent.actor_num_samples=4 \
    --env_name=$ENV --horizon_length=1 --run_group=ablation_standard --seed=0
```

## 10. Agent Selection Guide

| Scenario | Script | Agent | Key Flags |
|----------|--------|-------|-----------|
| Best offline+online performance | `main.py` | ACFQL | `--agent.actor_type=best-of-n --agent.actor_num_samples=32` |
| Fast inference (single-pass actor) | `main.py` | ACFQL | `--agent.actor_type=distill-ddpg --agent.alpha=100` |
| Pure online with prior data | `main_online.py` | ACRLPD | `--agent.bc_alpha=0.01` |
| RLPD baseline (no chunking) | `main_online.py` | ACRLPD | `--horizon_length=1 --agent.bc_alpha=0.0` |
| RLPD + action chunking (no BC) | `main_online.py` | ACRLPD | `--horizon_length=5 --agent.bc_alpha=0.0` |
| Visual observations | `main.py` | ACFQL | `--agent.encoder=impala_small` |
| Sparse rewards | `main.py` | ACFQL | `--sparse=True` |
| Offline-only (no online phase) | `main.py` | ACFQL | `--online_steps=0` |

## 11. Offline-Only Training

```bash
MUJOCO_GL=egl python main.py \
    --run_group=offline_only \
    --agent.actor_type=best-of-n \
    --env_name=cube-triple-play-singletask-task2-v0 \
    --horizon_length=5 \
    --offline_steps=1000000 \
    --online_steps=0 \
    --eval_interval=100000 \
    --save_interval=500000 \
    --seed=0
```

## 12. Saving and Restoring Checkpoints

```bash
# Save checkpoints every 500k steps
MUJOCO_GL=egl python main.py \
    --agent.actor_type=best-of-n \
    --env_name=cube-triple-play-singletask-task2-v0 \
    --horizon_length=5 \
    --save_interval=500000 \
    --save_dir=exp/ \
    --seed=0
# Checkpoints saved as: exp/qc/<run_group>/<env_name>/<exp_name>/params_<step>.pkl
```

Restore in Python:

```python
from utils.flax_utils import restore_agent_with_file

# Must first create agent with same config, then restore weights
agent = ACFQLAgent.create(seed=0, ex_observations=ex_obs, ex_actions=ex_act, config=config)
agent = restore_agent_with_file(agent, "exp/qc/.../params_500000.pkl")
```

## 13. Hyperparameter Tuning Tips

- **`horizon_length`**: 5 works well across most tasks. Try 3-10 for different environments.
- **`agent.alpha`** (ACFQL distill-ddpg): Controls BC vs Q trade-off. 100 for OGBench cube; tune per environment.
- **`agent.bc_alpha`** (ACRLPD): Small values like 0.01 add mild behavior cloning regularization. 0.0 = pure SAC.
- **`agent.actor_num_samples`** (best-of-N): 32 gives best quality; 4-8 for faster runtime.
- **`agent.num_qs`**: ACFQL defaults to 2; ACRLPD defaults to 10 (standard RLPD ensemble).
- **`agent.q_agg`**: `mean` (default) is more stable; `min` is more conservative (SAC-style pessimism).
- **`utd_ratio`**: 1 by default. Higher values (e.g., 4, 8) can improve sample efficiency but increase compute.
- **`discount`**: 0.99 default. Lower values (0.95-0.97) for shorter-horizon tasks.
- **Hidden dims**: Both agents default to `(512, 512, 512, 512)` for actor and critic. Reduce for simpler tasks.
