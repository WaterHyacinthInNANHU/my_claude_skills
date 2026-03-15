---
name: paper_rl__qc
description: Q-Chunking -- action chunking for TD-based offline-to-online RL on long-horizon sparse-reward tasks
---

# paper_rl__qc

Q-Chunking (QC) applies action chunking to temporal-difference RL methods, enabling agents to operate in a temporally extended action space with unbiased n-step backups. This improves exploration and online sample efficiency in offline-to-online settings, particularly on long-horizon, sparse-reward manipulation tasks.

## Paper Info

| Field | Value |
|-------|-------|
| Title | Reinforcement Learning with Action Chunking |
| Authors | Qiyang Li, Zhiyuan Zhou, Sergey Levine |
| Year | 2025 |
| Venue | NeurIPS 2025 |
| Paper | https://arxiv.org/abs/2507.07969 |
| Code | https://github.com/ColinQiyangLi/qc |
| Website | https://colinqiyangli.github.io/qc/ |

## Method Overview

1. **Action chunking**: The actor outputs `horizon_length` actions concatenated into a single vector. The critic evaluates `Q(s, a_0:H)` where `a_0:H` is the full chunk. During execution, the entire chunk is committed open-loop.
2. **N-step returns**: With chunk length H, the Bellman target uses the cumulative discounted reward over H steps and bootstraps from the state H steps later, with discount raised to the power H: `r_0 + gamma*r_1 + ... + gamma^(H-1)*r_{H-1} + gamma^H * Q(s_H, a_H)`.
3. **Offline-to-online**: Offline pre-training uses `main.py` (ACFQL agent). Online fine-tuning continues with `main.py` (same script, runs offline then online phases) or uses `main_online.py` (ACRLPD agent, pure online with replay buffer mixing).
4. **Two agent variants**: ACFQL (flow Q-learning with flow-matching actor) and ACRLPD (SAC-based with TanhNormal actor).

Key insight: Action chunking applied to TD-based RL provides both structured exploration (by committing to multi-step action sequences from offline data) and correct value learning (via unbiased n-step returns), bridging the gap between behavior cloning's temporal coherence and RL's optimality.

## Paper-Code Mapping

| Paper Concept | Code Location | Notes |
|---------------|---------------|-------|
| QC (ACFQL agent) | `agents/acfql.py:ACFQLAgent` | Flow Q-learning with action chunking; `action_chunking=True` reshapes actions to `(H*action_dim,)` |
| QC-RLPD (ACRLPD agent) | `agents/acrlpd.py:ACRLPDAgent` | SAC-based agent with action chunking and BC regularization |
| Action chunk critic | `agents/acfql.py:ACFQLAgent.critic_loss` | `Q(s, concat(a_0..a_H))` with `discount^H` bootstrap |
| Flow-matching actor | `agents/acfql.py:ACFQLAgent.actor_loss` | BC flow loss via conditional flow matching (CFM) + optional distill-ddpg Q loss |
| Flow action sampling (Euler) | `agents/acfql.py:ACFQLAgent.compute_flow_actions` | Euler integration over `flow_steps` steps from Gaussian noise |
| Best-of-N actor | `agents/acfql.py:ACFQLAgent.sample_actions` | `actor_type="best-of-n"`: sample N flow actions, pick highest Q |
| Distill-DDPG actor | `agents/acfql.py:ACFQLAgent.sample_actions` | `actor_type="distill-ddpg"`: one-step flow distillation + DDPG Q-gradient |
| SAC actor loss | `agents/acrlpd.py:ACRLPDAgent.actor_loss` | Entropy-regularized + optional BC loss (`bc_alpha`) |
| Sequence sampling | `utils/datasets.py:Dataset.sample_sequence` | Samples contiguous H-step windows; computes cumulative rewards, masks, validity |
| Chunked evaluation | `evaluation.py:evaluate` | Action queue: commit full chunk, pop one at a time |
| Offline-to-online training | `main.py:main` | Offline phase -> replay buffer init -> online phase |
| Pure online training | `main_online.py:main` | Online-only with 50/50 dataset/replay buffer mixing |
| Critic ensemble (ACFQL) | `utils/networks.py:Value` | `ensemblize` wrapper with `num_ensembles` (default 2) |
| Critic ensemble (ACRLPD) | `agents/model.py:Ensemble` + `rlpd_networks/state_action_value.py:StateActionValue` | `nn.vmap`-based ensemble with `num_qs` (default 10) |
| Actor vector field | `utils/networks.py:ActorVectorField` | Flow-matching velocity network; inputs: (obs, action, time) |
| Visual encoder | `utils/encoders.py:ImpalaEncoder` | IMPALA ResNet stack; variants: `impala`, `impala_small`, `impala_large` |
| Sparse reward transform | `main.py:process_train_dataset` | `(reward != 0) * -1.0`; controlled by `--sparse=True` |

## Setup

### Dependencies

- Python 3.10+
- JAX 0.6.0+ (with CUDA 12 support)
- Flax 0.10.5+
- Key packages: `jax`, `flax`, `optax`, `ml_collections`, `distrax`, `tensorflow-probability`, `wandb`, `ogbench`, `mujoco`
- For RoboMimic tasks: `robomimic`, `h5py`
- For D4RL tasks: `d4rl`

### Installation

```bash
git clone https://github.com/ColinQiyangLi/qc.git
cd qc
pip install -r requirements.txt
```

### Datasets

**OGBench** (auto-downloaded):
- Standard datasets download automatically via `ogbench.make_env_and_datasets()`
- Large datasets (e.g., `cube-quadruple-play-100m-v0`): manually download and use `--ogbench_dataset_dir=<path>`

```bash
# Download cube-quadruple 100M dataset
wget -r -np -nH --cut-dirs=2 -A "*.npz" https://rail.eecs.berkeley.edu/datasets/ogbench/cube-quadruple-play-100m-v0/
```

**RoboMimic** (manual download):
- Place datasets at `~/.robomimic/<task>/<type>/low_dim_v15.hdf5`
- Download from https://robomimic.github.io/docs/datasets/robomimic_v0.1.html (Multi-Human MH links)
- Supported env name format: `<task>-<type>-low_dim` (e.g., `lift-mh-low_dim`, `can-mh-low_dim`, `square-mh-low_dim`)

## Usage Scenarios

### Offline-to-Online RL (QC with best-of-N actor)

```bash
MUJOCO_GL=egl python main.py \
    --agent=agents/acfql.py \
    --agent.actor_type=best-of-n \
    --agent.actor_num_samples=32 \
    --env_name=cube-triple-play-singletask-task2-v0 \
    --horizon_length=5 \
    --offline_steps=1000000 \
    --online_steps=1000000 \
    --seed=0
```

### Offline-to-Online RL (QC-FQL with distill-DDPG actor)

```bash
MUJOCO_GL=egl python main.py \
    --agent=agents/acfql.py \
    --agent.actor_type=distill-ddpg \
    --agent.alpha=100 \
    --env_name=cube-triple-play-singletask-task2-v0 \
    --horizon_length=5 \
    --seed=0
```

### Pure Online RL (QC-RLPD with BC regularization)

```bash
MUJOCO_GL=egl python main_online.py \
    --agent=agents/acrlpd.py \
    --env_name=cube-triple-play-singletask-task2-v0 \
    --horizon_length=5 \
    --agent.bc_alpha=0.01 \
    --seed=0
```

### Sparse Reward Tasks

```bash
MUJOCO_GL=egl python main.py \
    --agent.actor_type=best-of-n \
    --agent.actor_num_samples=32 \
    --env_name=scene-play-singletask-task0-v0 \
    --sparse=True \
    --horizon_length=5 \
    --seed=0
```

### Baselines (no action chunking)

```bash
# FQL (horizon_length=1, no chunking, no n-step)
MUJOCO_GL=egl python main.py --agent.alpha=100 --env_name=cube-triple-play-singletask-task2-v0 --horizon_length=1

# BFN-n (n-step returns without chunking, actor sees single action)
MUJOCO_GL=egl python main.py --agent.actor_type=best-of-n --agent.actor_num_samples=4 \
    --env_name=cube-triple-play-singletask-task2-v0 --horizon_length=5 --agent.action_chunking=False

# RLPD (no chunking, standard SAC online)
MUJOCO_GL=egl python main_online.py --env_name=cube-triple-play-singletask-task2-v0 --horizon_length=1
```

### Key Config Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--horizon_length` | `5` | Action chunk length H; controls both chunk size and n-step return horizon |
| `--agent` | `agents/acfql.py` (main.py) / `agents/acrlpd.py` (main_online.py) | Agent config file |
| `--env_name` | `cube-triple-play-singletask-task2-v0` | Environment name (OGBench, RoboMimic, or D4RL) |
| `--offline_steps` | `1000000` | Number of offline training steps (main.py only) |
| `--online_steps` | `1000000` | Number of online training steps |
| `--sparse` | `False` | Convert rewards to sparse: `(r != 0) * -1.0` |
| `--discount` | `0.99` | Discount factor gamma |
| `--utd_ratio` | `1` | Update-to-data ratio for online training |
| `--eval_episodes` | `50` | Number of evaluation episodes |
| `--eval_interval` | `100000` | Steps between evaluations |
| `--buffer_size` | `2000000` (main.py) / `1000000` (main_online.py) | Replay buffer size |
| `--start_training` | `5000` | Online step to begin gradient updates |
| `--dataset_proportion` | `1.0` | Fraction of offline dataset to use |
| `--ogbench_dataset_dir` | `None` | Path for large OGBench datasets (e.g., 100M) |
| `--dataset_replace_interval` | `1000` | Steps between cycling dataset shards (for large datasets) |
| `--agent.action_chunking` | `True` | Enable action chunking (False = n-step returns only) |
| `--agent.actor_type` | `distill-ddpg` | Actor type for ACFQL: `distill-ddpg` or `best-of-n` |
| `--agent.actor_num_samples` | `32` | Number of flow samples for best-of-N actor |
| `--agent.alpha` | `100.0` (ACFQL) | BC distillation coefficient for distill-ddpg actor |
| `--agent.bc_alpha` | `0.0` (ACRLPD) | BC regularization strength for SAC actor |
| `--agent.num_qs` | `2` (ACFQL) / `10` (ACRLPD) | Critic ensemble size |
| `--agent.flow_steps` | `10` | Euler integration steps for flow matching |
| `--agent.q_agg` | `mean` | Target Q aggregation: `min` or `mean` |
| `--agent.batch_size` | `256` | Batch size |
| `--agent.lr` | `3e-4` | Learning rate (Adam/AdamW) |
| `--agent.tau` | `0.005` | Target network soft update rate |
| `--agent.layer_norm` | `True` | Layer normalization in critic |
| `--agent.encoder` | `None` | Visual encoder: `impala`, `impala_small`, `impala_large`, or `None` (state) |
| `--agent.weight_decay` | `0.0` (ACFQL) | AdamW weight decay (0 = plain Adam) |
| `--agent.use_fourier_features` | `False` | Fourier time embedding in flow actor |
| `--agent.init_temp` | `1.0` (ACRLPD) | Initial entropy temperature |
| `--agent.target_entropy_multiplier` | `0.5` (ACRLPD) | Multiplied by -action_dim for auto target entropy |

## Code Integration Guide

### Minimal Imports

```python
import sys
sys.path.append("/path/to/qc")

from agents.acfql import ACFQLAgent, get_config as get_acfql_config
from agents.acrlpd import ACRLPDAgent, get_config as get_acrlpd_config
from utils.datasets import Dataset, ReplayBuffer
from evaluation import evaluate
```

### Agent Instantiation

```python
import jax.numpy as jnp

# Get default config and customize
config = get_acfql_config()
config["horizon_length"] = 5
config["actor_type"] = "best-of-n"
config["actor_num_samples"] = 32

# Create agent from example data
# ex_observations: shape (obs_dim,) e.g. (23,) for RoboMimic lift
# ex_actions: shape (action_dim,) e.g. (7,)
agent = ACFQLAgent.create(
    seed=0,
    ex_observations=ex_observations,
    ex_actions=ex_actions,
    config=config,
)
```

### Training Loop (single step)

```python
import jax

# Offline update (single batch)
batch = dataset.sample_sequence(
    batch_size=256,
    sequence_length=5,     # horizon_length
    discount=0.99,
)
agent, info = agent.update(batch)

# Online update (batched UTD)
utd_ratio = 4
batch = replay_buffer.sample_sequence(
    batch_size=256 * utd_ratio,
    sequence_length=5,
    discount=0.99,
)
batch = jax.tree.map(lambda x: x.reshape((utd_ratio, 256) + x.shape[1:]), batch)
agent, info = agent.batch_update(batch)
```

### Action Sampling and Execution

```python
import jax
import numpy as np

rng = jax.random.PRNGKey(0)
action = agent.sample_actions(observations=obs, rng=rng)
# action shape: (horizon_length * action_dim,) when action_chunking=True
# Reshape and execute sequentially:
action_chunk = np.array(action).reshape(-1, action_dim)
for a in action_chunk:
    next_obs, reward, terminated, truncated, info = env.step(a)
```

### Data Format

| Field | Shape / Type | Description |
|-------|-------------|-------------|
| `observations` | `(B, obs_dim)` float32 | Current state observation (first in sequence) |
| `actions` | `(B, H, action_dim)` float32 | H-step action sequence |
| `rewards` | `(B, H)` float32 | Cumulative discounted rewards: `rewards[:,i] = sum(gamma^j * r_j, j=0..i)` |
| `masks` | `(B, H)` float32 | Running minimum of continuation masks (0 if any terminal seen) |
| `valid` | `(B, H)` float32 | 1.0 for valid steps (before any terminal), 0.0 after |
| `next_observations` | `(B, H, obs_dim)` float32 | Observations at each step in the sequence |
| `full_observations` | `(B, H, obs_dim)` float32 | Full obs sequence (state) or `(B, h, w, H, c)` (visual) |
| `terminals` | `(B, H)` float32 | Running max of terminal flags |

### Integration Notes

- The codebase uses **JAX/Flax**, not PyTorch. Agents are Flax PyTree nodes (immutable).
- Agent updates return a **new** agent: `agent, info = agent.update(batch)`. You must reassign.
- `ModuleDict` in `utils/flax_utils.py` bundles all networks (actor, critic, target_critic) into a single `TrainState` with a shared optimizer.
- `TrainState.select(name)` returns a partial call that routes to a specific sub-module.
- The `batch_update` method uses `jax.lax.scan` over the UTD dimension for efficient multi-update.
- Config is passed as `ml_collections.ConfigDict` via absl flags. Agent config files double as the config source (`get_config()` at module bottom).
- `MUJOCO_GL=egl` is required for headless GPU rendering (cluster environments).
- ACFQL uses `utils/networks.py` (MLP with GELU, `ensemblize`). ACRLPD uses `rlpd_networks/` and `agents/model.py` (MLP with ReLU, `nn.vmap` Ensemble). They are **not interchangeable**.
- Save/restore via pickle: `save_agent(agent, dir, step)` writes `params_<step>.pkl`, `restore_agent_with_file(agent, path)` loads it.

## Core Architecture

```
                    ACFQL (Flow Q-Learning)                    ACRLPD (SAC-based)
                    ~~~~~~~~~~~~~~~~~~~~~~                     ~~~~~~~~~~~~~~~~~~

Observation ----+---> ActorVectorField (BC flow)              Observation ---> TanhNormal Actor
                |         |                                                        |
                |    [Euler integration, flow_steps=10]                       sample actions
                |         |                                                        |
                |    flow actions (H*action_dim)                             actions (H*action_dim)
                |         |                                                        |
                |    +----+---- (distill-ddpg)                               +-----+
                |    |         ActorVectorField (one-step)                    |
                |    |              |                                         |
                |    +---- OR ---- (best-of-n)                               |
                |    |         sample N, pick max Q                          |
                |    |                                                       |
                +---> Value (critic ensemble, num_qs=2)        Ensemble(StateActionValue, num_qs=10)
                |         |                                         |
                |    Q(s, a_0:H)                              Q(s, a_0:H)
                |         |                                         |
                +---> Value (target critic, EMA tau=0.005)    target critic (EMA tau=0.005)
                          |                                         |
                     target_q = sum(gamma^i * r_i)            target_q = sum(gamma^i * r_i)
                              + gamma^H * mask * Q_target           + gamma^H * mask * Q_target
                                                                         |
                                                                    + alpha * entropy
                                                                    + bc_alpha * BC_loss

Dataset.sample_sequence(batch_size, sequence_length=H, discount=gamma)
    -> {observations, actions[B,H,A], rewards[B,H], masks[B,H], valid[B,H], next_observations[B,H,...]}
```

## Repo Structure

| Path | Purpose |
|------|---------|
| `main.py` | Offline-to-online training (ACFQL default). Runs offline phase then online phase with replay buffer seeded from offline data. |
| `main_online.py` | Pure online training (ACRLPD default). Mixes 50/50 offline dataset + replay buffer batches. |
| `agents/__init__.py` | Agent registry: `{"acfql": ACFQLAgent, "acrlpd": ACRLPDAgent}` |
| `agents/acfql.py` | `ACFQLAgent`: flow Q-learning + action chunking. Also serves as config via `get_config()`. |
| `agents/acrlpd.py` | `ACRLPDAgent`: SAC + action chunking + optional BC. Also serves as config via `get_config()`. |
| `agents/model.py` | Shared network defs for ACRLPD: `MLP`, `Ensemble`, `Normal`/`TanhNormal`, `TD3Actor`, `MLPResNet`, `MLPResNetBlock`. |
| `utils/networks.py` | Core network defs for ACFQL: `MLP` (GELU), `Value`, `Actor`, `ActorVectorField`, `FourierFeatures`, `ensemblize`. |
| `utils/datasets.py` | `Dataset` (frozen, offline) and `ReplayBuffer` classes. Key method: `sample_sequence()`. |
| `utils/encoders.py` | `ImpalaEncoder` (visual encoder) with variants: `impala`, `impala_small`, `impala_large`, `impala_debug`. |
| `utils/flax_utils.py` | `ModuleDict`, `TrainState`, `save_agent()`, `restore_agent()`, `restore_agent_with_file()`. |
| `evaluation.py` | `evaluate()`: runs episodes with action queue (commit full chunk, pop FIFO). |
| `log_utils.py` | `CsvLogger`, WandB setup (`setup_wandb`), `get_exp_name`, video utilities. |
| `envs/env_utils.py` | `make_env_and_datasets()`: dispatcher for OGBench, D4RL, RoboMimic. `EpisodeMonitor`, `FrameStackWrapper`. |
| `envs/robomimic_utils.py` | `RobomimicLowdimWrapper`, `make_env()`, `get_dataset()`. Loads HDF5 from `~/.robomimic/`. |
| `envs/ogbench_utils.py` | `make_ogbench_env_and_datasets()`, `load_dataset()`. Loads NPZ files, supports custom dataset dirs. |
| `envs/d4rl_utils.py` | D4RL environment and dataset loading (AntMaze, Adroit). |
| `rlpd_networks/` | RLPD network modules (`MLP`, `Ensemble`, `StateActionValue`, `PixelMultiplexer`) used by ACRLPD. |
| `rlpd_networks/encoders/` | `D4PGEncoder` for pixel observations (used by ACRLPD). |
| `rlpd_distributions/` | `TanhNormal`, `TanhDeterministic`, `TanhTransformed` distributions for ACRLPD. |

## Tips & Gotchas

- **`action_chunking=True` vs `False`**: When True, the actor outputs `H*action_dim` actions and the critic takes the concatenated chunk as input. When False, the actor outputs a single action but still uses n-step returns (the "n-step return baseline" in the paper).
- **`horizon_length=1`**: Reduces to standard single-step RL (no chunking, no n-step return).
- **Two different network stacks**: ACFQL uses `utils/networks.py` (MLP with GELU activation, `ensemblize` via `nn.vmap`). ACRLPD uses `rlpd_networks/` and `agents/model.py` (MLP with ReLU, separate `Ensemble` class). They are not interchangeable.
- **Reward adjustment**: RoboMimic rewards are shifted by -1.0 (from [0,1] to [-1,0]). D4RL AntMaze rewards are also shifted by -1.0. Sparse mode further transforms to `(r != 0) * -1.0`.
- **Evaluation action queue**: During eval, a new action chunk is only sampled when the queue is empty. Actions are popped FIFO. The queue is cleared on episode reset.
- **WandB required by default**: Both scripts initialize WandB at startup. Set `WANDB_MODE=disabled` to run without logging.
- **Memory for large datasets**: Use `--ogbench_dataset_dir` with `--dataset_replace_interval=1000` to cycle through dataset shards (avoids loading entire 100M dataset into memory).
- **EGL rendering**: Set `MUJOCO_GL=egl` on headless machines. The code also auto-sets `EGL_DEVICE_ID` and `MUJOCO_EGL_DEVICE_ID` from `CUDA_VISIBLE_DEVICES`.
- **JAX JIT compilation**: First training step will be slow due to JIT compilation. Subsequent steps are fast.
- **Valid mask in sequence sampling**: The `valid` field marks whether each position in the H-step window is before any terminal. The critic loss is weighted by `valid[..., -1]` to ignore invalid target bootstraps.
- **`main.py` vs `main_online.py`**: `main.py` has both offline and online phases (replay buffer initialized from offline data). `main_online.py` is online-only with an empty replay buffer, mixing 50/50 dataset batches + replay batches at each step.
- **`batch_update` vs `update`**: `update` processes a single batch. `batch_update` takes a batch with an extra leading dimension (UTD ratio) and scans over it with `jax.lax.scan`, returning averaged info.
- **RoboMimic env naming**: Use `<task>-<dataset_type>-low_dim` format, e.g., `lift-mh-low_dim`. The `is_robomimic_env()` check requires `low_dim` in the name. Max episode lengths: lift/can=300, square=400, transport=800, tool_hang=1000.
- **Checkpoint format**: Saved as `params_<step>.pkl` via `pickle` with `flax.serialization.to_state_dict()`.
- **Online action queue reset**: When an episode terminates during online training, the action queue is cleared and a new chunk is sampled at the next step.
