---
name: paper_rob__ibrl
description: IBRL uses Q-based selection between RL and BC actions for exploration and bootstrapping to achieve sample-efficient robotic manipulation.
---

# paper_rob__ibrl

Imitation Bootstrapped Reinforcement Learning (IBRL) trains a BC policy on demonstrations, then uses it alongside an RL actor during online training: at each step, a learned Q-function selects whichever action (RL or BC) has higher value for both exploration and computing TD bootstrap targets. This creates an automatic curriculum where BC dominates early and RL gradually takes over, yielding strong sample efficiency on pixel-based and state-based manipulation tasks.

## Paper Info

| Field | Value |
|-------|-------|
| Title | Imitation Bootstrapped Reinforcement Learning |
| Authors | Hengyuan Hu, Suvir Mirchandani, Dorsa Sadigh |
| Year | 2023 |
| Venue | arXiv (cs.LG) |
| Paper | https://arxiv.org/abs/2311.02198 |
| Code | https://github.com/hengyuan-hu/ibrl |
| Website | https://ibrl.hengyuanhu.com/ |
| Data/Weights | [Google Drive](https://drive.google.com/file/d/1F2yH84Iqv0qRPmfH8o-kSzgtfaoqMzWE/view?usp=sharing) |

## Method Overview

1. Pretrain a BC policy on demonstration data (HDF5 format from Robomimic)
2. Initialize RL actor, dual-Q critic, and target networks
3. Warm up: collect episodes into the replay buffer using BC policy actions
4. Online RL loop: at each step, obtain both RL and BC actions, use the critic to select the better one (IBRL selection) for environment interaction
5. For TD target computation, apply the same Q-based selection on next-state actions (IBRL bootstrapping)
6. Update critic with MSE loss on Bellman targets, update actor to maximize Q, soft-update targets

Key insight: By using the BC policy to propose alternative actions for Q-based selection in both exploration and bootstrapping, IBRL leverages high-quality demonstration knowledge from the start of training without requiring explicit scheduling or regularization.

## Paper-Code Mapping

| Paper Concept | Code Location | Notes |
|---------------|---------------|-------|
| IBRL action selection (hard) | `rl/q_agent.py:QAgent._act_ibrl` | argmax Q over {a_rl, a_bc}, eps-greedy support |
| IBRL action selection (soft) | `rl/q_agent.py:QAgent._act_ibrl_soft` | softmax(Q * beta) sampling over {a_rl, a_bc} |
| TD target with IBRL bootstrap | `rl/q_agent.py:QAgent.update_critic` | Calls `_act_ibrl`/`_act_ibrl_soft` with `use_target=True` |
| Critic update (dual-Q) | `rl/q_agent.py:QAgent.update_critic` | MSE loss, min(Q1, Q2) for target |
| Actor update | `rl/q_agent.py:QAgent.update_actor` | Maximize Q via policy gradient |
| RFT actor update with BC reg | `rl/q_agent.py:QAgent.update_actor_rft` | `bc_loss_coef * ratio * bc_loss`, dynamic ratio via Q-comparison |
| BC policy (pixel) | `bc/bc_policy.py:BcPolicy` | MultiViewEncoder -> MLP -> tanh |
| BC policy (state) | `bc/bc_policy.py:StateBcPolicy` | MLP with dropout -> tanh |
| RL actor (pixel) | `rl/actor.py:Actor` | Feature compress + MLP -> TruncatedNormal |
| RL actor (state) | `rl/actor.py:FcActor` | MLP with dropout -> TruncatedNormal |
| Dual-Q critic (pixel) | `rl/critic.py:Critic` | Two `_QNet` or `SpatialEmbQNet` heads |
| Multi-Q critic (state, RED-Q) | `rl/critic.py:MultiFcQ` | 10 parallel Q-nets via `_MultiLinear`, sample k=2 for target |
| ViT encoder | `networks/encoder.py:VitEncoder` | MinVit, default patch=8, depth=3, embed=128 |
| ResNet encoder | `networks/encoder.py:ResNetEncoder` | Custom ResNet with configurable stem/downsample |
| ResNet96 encoder | `networks/encoder.py:ResNet96Encoder` | ResNet variant for 96x96 inputs |
| DrQ encoder | `networks/encoder.py:DrQEncoder` | 4-layer conv, rescale to 84x84 |
| Multi-view fusion (BC) | `bc/multiview_encoder.py:MultiViewEncoder` | Per-camera ResNet + compress + cat/add/mult fusion |
| Spatial embedding (critic) | `rl/critic.py:SpatialEmbQNet` | Learned weighted sum over patch features fused with action |
| Spatial embedding (actor) | `rl/actor.py:SpatialEmb` | Learned weighted sum over patch features |
| Data augmentation | `rl/q_agent.py:QAgent.aug` | `RandomShiftsAug(pad=4)` — random shift crop |
| Replay buffer | `rl/replay.py:ReplayBuffer` | C++ `rela.SingleStepTransitionReplay` (pybind11), n-step returns |
| Exploration noise schedule | `common_utils/py/ibrl_utils.py:schedule` | `linear(max, min, duration)` decay |
| TruncatedNormal distribution | `common_utils/py/ibrl_utils.py:TruncatedNormal` | Clamped Gaussian with optional action norm clipping |
| Robomimic env wrapper | `env/robosuite_wrapper.py:PixelRobosuite` | Image extraction, resize, prop/state stacking |
| Meta-World env wrapper | `env/metaworld_wrapper.py:PixelMetaWorld` | Frame stacking, obs_stack support |
| Config system | `train_rl.py:MainConfig` | pyrallis dataclass, YAML + CLI overrides |

## Setup

### Dependencies

- Python 3.9
- PyTorch 2.1.0 (CUDA 12.1)
- MuJoCo 2.1 (mujoco210 binary in `~/.mujoco/mujoco210`)
- mujoco-py 2.1.2.14
- Key packages: `robosuite` (git), `metaworld` (git), `pyrallis`, `h5py`, `wandb`, `einops`, `rich`

### Installation

```bash
# MuJoCo 2.1
wget https://mujoco.org/download/mujoco210-linux-x86_64.tar.gz
mkdir -p ~/.mujoco && tar -xzf mujoco210-linux-x86_64.tar.gz -C ~/.mujoco/

# Clone and setup
git clone --recursive https://github.com/hengyuan-hu/ibrl.git
cd ibrl
conda create -n ibrl python=3.9 && conda activate ibrl
source set_env.sh  # sets PYTHONPATH, MUJOCO paths, OMP_NUM_THREADS=1

# Install packages
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# Compile C++ replay buffer (pybind11)
cd common_utils && make && cd ..
```

### Pre-trained Weights & Data

Download from [Google Drive](https://drive.google.com/file/d/1F2yH84Iqv0qRPmfH8o-kSzgtfaoqMzWE/view?usp=sharing), extract to `release/`:
```
release/
├── cfgs/          # YAML configs (shipped with repo)
├── data/          # HDF5 demo datasets
│   ├── robomimic/{can,square}/processed_data96.hdf5
│   └── metaworld/{Assembly,...}/dataset.hdf5
└── model/         # Pretrained BC checkpoints
    ├── robomimic/{can,square}/model0.pt
    └── metaworld/path{Assembly,...}_*/model1.pt
```

## Usage Scenarios

### Train IBRL (pixel, Robomimic)

```bash
python train_rl.py --config_path release/cfgs/robomimic_rl/can_ibrl.yaml \
  --save_dir exp/can_ibrl --use_wb 0
```

### Train RLPD baseline

```bash
python train_rl.py --config_path release/cfgs/robomimic_rl/can_rlpd.yaml \
  --save_dir exp/can_rlpd --use_wb 0
```

### Train RFT baseline (two-step)

```bash
# Step 1: Pretrain RL actor with BC loss
python train_rl.py --config_path release/cfgs/robomimic_rl/can_rft.yaml \
  --pretrain_only 1 --pretrain_num_epoch 5 --load_pretrained_agent None \
  --save_dir exp/can_pretrain --use_wb 0

# Step 2: RL fine-tune with BC regularization
python train_rl.py --config_path release/cfgs/robomimic_rl/can_rft.yaml \
  --load_pretrained_agent exp/can_pretrain/model0.pt \
  --save_dir exp/can_rft --use_wb 0
```

### Train on Meta-World

```bash
python mw_main/train_rl_mw.py \
  --config_path release/cfgs/metaworld/ibrl_basic.yaml \
  --bc_policy assembly --save_dir exp/mw_ibrl --use_wb 0
```

### Key Config Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--config_path` | (required) | YAML config file path |
| `--task_name` | `"Lift"` | Robomimic task: Lift, PickPlaceCan, NutAssemblySquare, TwoArmTransport, ToolHang |
| `--bc_policy` | `""` | Path to pretrained BC model (or task name for Meta-World) |
| `--q_agent.act_method` | `"rl"` | Action selection: `"rl"`, `"ibrl"`, `"ibrl_soft"` |
| `--q_agent.bootstrap_method` | same as act_method | Bootstrap action selection (can differ from act_method) |
| `--q_agent.enc_type` | `"vit"` | Encoder: `"vit"`, `"resnet"`, `"resnet96"`, `"drq"` |
| `--use_state` | `0` | 1 = state-based (no images), 0 = pixel-based |
| `--mix_rl_rate` | `1.0` | Fraction of RL data in batch; 0.5 = RLPD-style demo mixing |
| `--add_bc_loss` | `0` | 1 = add BC regularization to actor loss (RFT) |
| `--num_train_step` | `200000` | Total environment steps |
| `--replay_buffer_size` | `500` | Max episodes in replay buffer |
| `--preload_num_data` | `0` | Number of demo episodes to preload |
| `--stddev_max/min/step` | `1.0/0.1/500000` | Exploration noise linear schedule |
| `--num_warm_up_episode` | `50` | BC-guided warm-up episodes |
| `--save_dir` | `"exps/rl/run1"` | Output directory for logs, configs, model checkpoints |
| `--use_wb` | `0` | 1 = log to Weights & Biases |
| `--mp_eval` | `0` | 1 = parallel evaluation (10 processes) |

## Code Integration Guide

### Minimal Imports

```python
import sys
sys.path.append("/path/to/ibrl")

from rl.q_agent import QAgent, QAgentConfig
from bc.bc_policy import BcPolicy, BcPolicyConfig
from networks.encoder import VitEncoder, VitEncoderConfig
```

### Model Instantiation & Inference

```python
import torch
from rl.q_agent import QAgent, QAgentConfig

# Create QAgent for pixel-based task
cfg = QAgentConfig()
cfg.act_method = "ibrl"           # or "rl", "ibrl_soft"
cfg.enc_type = "vit"
cfg.use_prop = 1
cfg.vit.embed_style = "embed2"
cfg.vit.depth = 1
cfg.actor.dropout = 0.5
cfg.critic.spatial_emb = 1024

agent = QAgent(
    use_state=False,
    obs_shape=(3, 96, 96),         # (C*obs_stack, H, W)
    prop_shape=(27,),              # prop_dim * prop_stack (9 * 3)
    action_dim=7,                  # OSC_POSE: 6 EE + 1 gripper
    rl_camera="robot0_eye_in_hand",
    cfg=cfg,
)

# Load trained weights
agent.load_state_dict(torch.load("model0.pt"))
agent.eval()

# Inference: obs is dict with camera images and proprioception
# Images: uint8 [C, H, W], will be normalized internally (/255 - 0.5)
# Prop: float32 [prop_dim]
obs = {
    "robot0_eye_in_hand": torch.randint(0, 255, (3, 96, 96)).cuda(),
    "prop": torch.randn(27).cuda(),
}
with torch.no_grad():
    action = agent.act(obs, eval_mode=True)  # returns [7] tensor on CPU
```

### Loading a Full Trained Model

```python
import train_rl

agent, eval_env, eval_env_params = train_rl.load_model("path/to/model0.pt", "cuda")
# agent: QAgent with BC policy attached (if bc_policy was set in config)
# eval_env: PixelRobosuite ready for evaluation
```

### Data Format

| Field | Shape / Type | Description |
|-------|-------------|-------------|
| Camera obs | `(C, H, W)` uint8 | Per-camera image, C=3*obs_stack, H=W=96 (rl_image_size) |
| `prop` | `(prop_dim,)` float32 | EE pos(3) + quat(4) + gripper(2) = 9, stacked prop_stack times |
| `state` | `(state_dim,)` float32 | Full state (e.g. 19 for Lift), stacked state_stack times |
| `action` | `(action_dim,)` float32 | OSC_POSE: 6D EE delta + 1 gripper, range [-1, 1] |
| HDF5 dataset | `data/demo_N/obs/{camera}_image`, `actions`, `rewards` | Robomimic format |

### Integration Notes

- The repo must be on `PYTHONPATH` due to absolute imports (`import common_utils`, `from rl.q_agent import ...`)
- `common_utils` has a C++ pybind11 module (`rela`) that must be compiled with `make` before use
- The `QAgent` owns separate optimizers internally; for custom training loops, access `agent.encoder_opt`, `agent.critic_opt`, `agent.actor_opt`
- BC policies are stored in `agent.bc_policies` list and must be added via `agent.add_bc_policy()`
- Image observations must have pixel values > 5 (raw uint8 range); normalization is done inside the encoder
- `source set_env.sh` is critical: it sets `PYTHONPATH`, MuJoCo paths, and `OMP_NUM_THREADS=1` (needed for parallel eval)

## Core Architecture

```
IBRL Training Loop
==================

Demonstrations (HDF5)
  |
  v
BC Policy Training (train_bc.py)
  |
  +-- BcPolicy: MultiViewEncoder(per-cam ResNet + compress + cat) -> MLP -> tanh
  |   or
  +-- StateBcPolicy: MLP(dropout=0.5) -> tanh
  |
  v
RL Training (train_rl.py)
  |
  +-- QAgent (rl/q_agent.py)
  |     |
  |     +-- Encoder: VitEncoder / ResNetEncoder / DrQEncoder
  |     |     - Input: [B, C, 96, 96] uint8 -> /255 - 0.5
  |     |     - Output: [B, num_patch, patch_dim]
  |     |
  |     +-- Actor: feat -> compress(Linear+LN+ReLU or SpatialEmb) -> MLP -> TruncatedNormal
  |     |     - dropout=0.5 on RL actor helps prevent overfitting
  |     |
  |     +-- Critic: dual-Q, feat+action -> _QNet or SpatialEmbQNet -> scalar
  |     |     - Target: min(Q1_target, Q2_target)
  |     |
  |     +-- IBRL Selection (act + bootstrap):
  |           a_rl = Actor(s), a_bc = BCPolicy(s)
  |           a* = argmax_{a in {a_rl, a_bc}} Q_target(s, a)  [hard]
  |           or: sample from softmax(Q * beta)                [soft]
  |
  +-- Replay Buffer (C++ pybind11)
  |     - N-step returns (default n=3)
  |     - Separate BC replay for demo mixing (RLPD: mix_rl_rate=0.5)
  |
  +-- Data Augmentation: RandomShiftsAug(pad=4)

State-based variant:
  Actor = FcActor(MLP, dropout=0.5)
  Critic = MultiFcQ(10 Q-nets via _MultiLinear, RED-Q: sample k=2 for min)
```

## Repo Structure

| Path | Purpose |
|------|---------|
| `train_rl.py` | Main RL training entry point: `MainConfig`, `Workspace`, training loop |
| `train_bc.py` | BC pretraining entry point: `MainConfig`, training loop, `load_model()` |
| `bc/bc_policy.py` | `BcPolicy` (pixel, MultiViewEncoder+MLP), `StateBcPolicy` (state, MLP) |
| `bc/multiview_encoder.py` | `MultiViewEncoder`: per-camera ResNet encoders with fusion (cat/add/mult) |
| `bc/dataset.py` | `RobomimicDataset`: HDF5 loading, `DatasetConfig`, `sample_bc()` |
| `rl/q_agent.py` | `QAgent`: core IBRL logic, `_act_ibrl`, `_act_ibrl_soft`, `update_critic`, `update_actor`, `update_actor_rft` |
| `rl/actor.py` | `Actor` (pixel, with `SpatialEmb`), `FcActor` (state) |
| `rl/critic.py` | `Critic` (dual-Q with `_QNet`/`SpatialEmbQNet`), `MultiFcQ` (multi-Q via `_MultiLinear`) |
| `rl/replay.py` | `ReplayBuffer`: wraps C++ `rela.SingleStepTransitionReplay`, BC replay, `add_demos_to_replay()` |
| `networks/encoder.py` | `VitEncoder`, `ResNetEncoder`, `ResNet96Encoder`, `DrQEncoder` |
| `networks/min_vit.py` | `MinVit`: minimal ViT implementation |
| `networks/resnet.py` | Custom `ResNet` with configurable stem/downsample |
| `networks/resnet_rl.py` | `ResNet96` for 96x96 inputs |
| `env/robosuite_wrapper.py` | `PixelRobosuite`: robosuite env with image extraction, resize, obs stacking |
| `env/metaworld_wrapper.py` | `PixelMetaWorld`: Meta-World env wrapper |
| `mw_main/train_rl_mw.py` | Meta-World RL training (IBRL/RLPD/RFT), `BC_POLICIES` and `BC_DATASETS` dicts |
| `mw_main/train_bc_mw.py` | Meta-World BC training |
| `mw_main/mw_replay.py` | Meta-World replay buffer |
| `evaluate/eval.py` | Single-process evaluation: `run_eval()` |
| `evaluate/multi_process_eval.py` | Multi-process evaluation: `run_eval_mp()` |
| `common_utils/py/ibrl_utils.py` | `TruncatedNormal`, `eval_mode`, `soft_update_params`, `schedule()`, `orth_weight_init` |
| `common_utils/py/data_aug.py` | `RandomShiftsAug` |
| `common_utils/` | C++ pybind11 replay buffer (`rela` module), logging, saving utilities |
| `release/cfgs/` | YAML configs for all methods: `robomimic_rl/`, `robomimic_bc/`, `metaworld/` |
| `set_env.sh` | Environment setup: PYTHONPATH, MuJoCo paths, `OMP_NUM_THREADS=1` |

## Three Training Paradigms

| Method | Mechanism | Key Config |
|--------|-----------|------------|
| **IBRL** | Q-based selection between RL & BC actions for both exploration and bootstrapping | `act_method: "ibrl"`, `bc_policy: path/to/model.pt` |
| **RLPD** | Mix demonstration data into replay buffer (50/50 by default) | `act_method: "rl"`, `mix_rl_rate: 0.5`, `preload_num_data: N` |
| **RFT** | Pretrain RL actor with BC loss, then fine-tune with BC regularization | `act_method: "rl"`, `add_bc_loss: 1`, `bc_loss_coef: 0.1`, `load_pretrained_agent: path` |

## Tips & Gotchas

- **C++ compilation required**: `cd common_utils && make` is mandatory; requires cmake, gcc, and pybind11 (included as submodule). If you see `GLIBCXX_3.4.30 not found`, symlink system libstdc++ into conda env
- **`source set_env.sh`**: must run once per shell; sets `PYTHONPATH=$PWD`, MuJoCo paths, and `OMP_NUM_THREADS=1` (critical for parallel eval performance)
- **MuJoCo 2.1 specifically**: the repo uses `mujoco-py` which requires the old MuJoCo 2.1 binary (not the newer `mujoco` pip package alone)
- **GPU memory**: pixel-based ViT training uses ~16GB VRAM; ResNet/DrQ encoders use less
- **Warm-up phase**: the first 50 episodes use BC policy actions to fill the replay buffer; ensure `bc_policy` path is valid
- **Actor dropout**: 0.5 dropout on the RL actor is important for IBRL; it prevents overfitting to demonstration-heavy early data. During critic target computation, `actor_target.training` is asserted `True` (dropout active)
- **`assert False` at end**: both `train_rl.py` and `train_bc.py` deliberately crash at the end (`assert False`) to signal completion; this is intentional
- **Image normalization**: encoders expect raw pixel values (>5), normalization `/255 - 0.5` happens inside the encoder forward pass
- **Evaluation parallelism**: `--mp_eval 1` spawns 10 processes; requires `OMP_NUM_THREADS=1` to avoid thread contention
- **Config system**: pyrallis supports YAML file + CLI overrides; nested fields use dots: `--q_agent.actor.dropout 0.3`
- **Action space**: Robomimic uses OSC_POSE (6D end-effector delta + 1 gripper), actions clamped to [-1, 1] via `Tanh` output
- **HDF5 data format**: demos stored as `data/demo_N/obs/{camera}_image`, `data/demo_N/actions`, `data/demo_N/rewards`
- **Meta-World task names**: use short names (`assembly`, `boxclose`, `coffeepush`, `stickpull`) which map to `BC_POLICIES` and `BC_DATASETS` dicts in `mw_main/train_rl_mw.py`
- **`update_freq: 2`**: RL update happens every 2 env steps; critic updates `num_critic_update` times, actor updates only on the last critic iteration (RED-Q style)
