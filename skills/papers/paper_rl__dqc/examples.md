# DQC Examples & Reproduction

## Installation

```bash
git clone https://github.com/ColinQiyangLi/dqc.git
cd dqc
pip install -r requirements.txt
```

For large datasets (100m/1b), follow [horizon-reduction instructions](https://github.com/seohongpark/horizon-reduction?tab=readme-ov-file#using-large-datasets).

## Quick Start: Run DQC on cube-quadruple

```bash
MUJOCO_GL=egl python main.py \
    --run_group=dqc-test \
    --offline_steps=1000000 \
    --eval_interval=250000 \
    --seed=100001 \
    --agent=agents/dqc.py \
    --agent.num_qs=2 \
    --agent.policy_chunk_size=5 \
    --agent.backup_horizon=25 \
    --agent.use_chunk_critic=True \
    --agent.distill_method=expectile \
    --agent.implicit_backup_type=quantile \
    --env_name=cube-quadruple-play-oraclerep-v0 \
    --agent.q_agg=min \
    --dataset_dir=[DATA_ROOT]/cube-quadruple-play-100m-v0 \
    --agent.kappa_b=0.93 \
    --agent.kappa_d=0.8 \
    --tags="DQC,h=25,ha=5"
```

## All Baselines on Same Environment

```bash
# DQC (h=25, h_a=5) — full method
MUJOCO_GL=egl python main.py --agent=agents/dqc.py \
    --agent.backup_horizon=25 --agent.policy_chunk_size=5 \
    --agent.use_chunk_critic=True \
    --agent.kappa_b=0.93 --agent.kappa_d=0.8 \
    --env_name=cube-quadruple-play-oraclerep-v0 \
    --agent.q_agg=min --dataset_dir=[DATA_ROOT]/cube-quadruple-play-100m-v0 \
    --offline_steps=1000000 --seed=100001

# QC (h=5, h_a=5) — original Q-chunking
MUJOCO_GL=egl python main.py --agent=agents/dqc.py \
    --agent.backup_horizon=5 --agent.policy_chunk_size=5 \
    --agent.use_chunk_critic=False \
    --agent.kappa_b=0.93 \
    --env_name=cube-quadruple-play-oraclerep-v0 \
    --agent.q_agg=min --dataset_dir=[DATA_ROOT]/cube-quadruple-play-100m-v0 \
    --offline_steps=1000000 --seed=100001

# NS (n=25) — n-step returns, single-action policy
MUJOCO_GL=egl python main.py --agent=agents/dqc.py \
    --agent.backup_horizon=25 --agent.policy_chunk_size=1 \
    --agent.use_chunk_critic=False \
    --agent.kappa_b=0.5 \
    --env_name=cube-quadruple-play-oraclerep-v0 \
    --agent.q_agg=min --dataset_dir=[DATA_ROOT]/cube-quadruple-play-100m-v0 \
    --offline_steps=1000000 --seed=100001

# OS — standard 1-step TD
MUJOCO_GL=egl python main.py --agent=agents/dqc.py \
    --agent.backup_horizon=1 --agent.policy_chunk_size=1 \
    --agent.use_chunk_critic=False \
    --agent.kappa_b=0.7 \
    --env_name=cube-quadruple-play-oraclerep-v0 \
    --agent.q_agg=min --dataset_dir=[DATA_ROOT]/cube-quadruple-play-100m-v0 \
    --offline_steps=1000000 --seed=100001
```

## Environments Without Large Datasets

For `humanoidmaze-giant` and `puzzle-4x5`, data is auto-downloaded:

```bash
MUJOCO_GL=egl python main.py \
    --agent=agents/dqc.py \
    --agent.backup_horizon=25 --agent.policy_chunk_size=5 \
    --agent.use_chunk_critic=True \
    --agent.kappa_b=0.5 --agent.kappa_d=0.8 \
    --env_name=humanoidmaze-giant-navigate-oraclerep-v0 \
    --agent.q_agg=mean \
    --dataset_dir=None \
    --offline_steps=1000000 --seed=100001
```

## Generate All Reproduction Commands

```bash
cd experiments
python reproduce.py          # main results (edit dataset_root first)
python reproduce-sensitivity.py  # hyperparameter sensitivity
```

This produces shell scripts with all seed/environment/method combinations.

## Evaluate With Different Action Chunk Sizes at Test Time

```bash
# Evaluate with full policy chunk, then first 1 action, then first 5 actions
--action_chunk_eval_sizes="0,1,5"

# Evaluate with different best-of-N values
--best_of_n_eval_values="0,8,128"
```

## Restore From Checkpoint

```bash
python main.py \
    --restore_path="exp/dqc/run_group/exp_name" \
    --restore_epoch=1000000 \
    ...
```

## Debug Run (fast iteration)

```bash
MUJOCO_GL=egl python main.py \
    --run_group=debug \
    --offline_steps=100 \
    --eval_interval=20 \
    --log_interval=10 \
    --eval_episodes=0 \
    --video_episodes=0 \
    --agent=agents/dqc.py \
    --agent.batch_size=8 \
    --agent.backup_horizon=5 \
    --agent.policy_chunk_size=1 \
    --agent.use_chunk_critic=True \
    --env_name=cube-quadruple-play-oraclerep-v0 \
    --dataset_dir=None \
    --seed=42
```

## HPCC SLURM Example

```bash
#!/bin/bash
#SBATCH --job-name=dqc
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=24:00:00

module load mamba
mamba activate dqc

MUJOCO_GL=egl python main.py \
    --run_group=dqc-hpcc \
    --offline_steps=1000000 \
    --eval_interval=250000 \
    --seed=${SLURM_ARRAY_TASK_ID} \
    --agent=agents/dqc.py \
    --agent.backup_horizon=25 \
    --agent.policy_chunk_size=5 \
    --agent.use_chunk_critic=True \
    --agent.distill_method=expectile \
    --agent.implicit_backup_type=quantile \
    --env_name=cube-quadruple-play-oraclerep-v0 \
    --agent.q_agg=min \
    --dataset_dir=$DATA_ROOT/cube-quadruple-play-100m-v0 \
    --agent.kappa_b=0.93 \
    --agent.kappa_d=0.8
```
