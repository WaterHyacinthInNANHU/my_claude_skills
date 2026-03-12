# IBRL — Imitation Bootstrapped Reinforcement Learning

> **Paper:** [Imitation Bootstrapped Reinforcement Learning](https://arxiv.org/abs/2311.02198) (2024)
> **Authors:** Hengyuan Hu, Suvir Mirchandani, Dorsa Sadigh
> **Repo:** [hengyuan-hu/ibrl](https://github.com/hengyuan-hu/ibrl)
> **Website:** [ibrl.hengyuanhu.com](https://ibrl.hengyuanhu.com)
> **Data/Weights:** [Google Drive](https://drive.google.com/file/d/1F2yH84Iqv0qRPmfH8o-kSzgtfaoqMzWE/view?usp=sharing)

## What It Does

IBRL combines imitation learning (BC) with reinforcement learning to achieve high sample efficiency on robotic manipulation. The key idea: train a BC policy on demos, then use it during RL in two ways:

1. **Exploration** — at each step, compare Q-values of the RL action vs the BC action; pick whichever is better
2. **Bootstrapping** — use the same Q-based selection when computing TD targets for critic updates

This creates an automatic curriculum: early on the BC policy dominates (its actions have higher Q); as RL improves, it gradually takes over — no explicit scheduling needed.

## Core Algorithm

```
1. Pretrain BC policy π_bc on demonstrations D
2. Initialize RL actor π_rl, critic Q, target networks
3. Warm-up: collect episodes using π_bc into replay buffer R
4. For each step t:
   a. a_rl = π_rl(s)           # RL action
   b. a_bc = π_bc(s)           # BC action
   c. a = argmax_{a ∈ {a_rl, a_bc}} Q(s, a)   # IBRL selection
   d. Execute a, store (s,a,r,s') in R
   e. Sample batch from R
   f. Compute TD target:
      - a'_rl = π_rl_target(s')
      - a'_bc = π_bc(s')
      - a' = argmax Q_target(s', a')     # IBRL bootstrap
      - y = r + γ · min(Q1_target, Q2_target)(s', a')
   g. Update critic: minimize (Q(s,a) - y)²
   h. Update actor: maximize Q(s, π_rl(s))
   i. Soft-update target networks (τ = 0.01)
```

### Action Selection Variants

| Mode | `act_method` | Behavior |
|------|-------------|----------|
| Pure RL | `"rl"` | Only uses π_rl |
| IBRL Hard | `"ibrl"` | argmax Q over {a_rl, a_bc} with ε-greedy |
| IBRL Soft | `"ibrl_soft"` | softmax(Q · β) sampling over {a_rl, a_bc} |

## Architecture

### Visual Pipeline (pixel observations)
```
Camera images (96×96)
  → Per-camera ResNet / ViT encoder
  → Multi-view fusion (concat)
  → Feature vector (shared between actor & critic)
```

### Networks

| Component | Architecture | Key Config |
|-----------|-------------|------------|
| BC Policy | MultiViewEncoder → MLP(1024) → tanh | `hidden_dim=1024`, `num_layer=1` |
| RL Actor | Feature compress → MLP(1024) → TruncatedNormal | `dropout=0.5`, `orth_init=1` |
| RL Critic | Dual-Q (Q1, Q2), feature+action → MLP → scalar | `spatial_emb=1024` |
| Encoder | ViT (depth=1, embed=128, patch=8) or ResNet96 | `enc_type="vit"` |

### State-based variant
- BC: simple MLP policy
- RL: `FcActor` + `MultiFcQ` (10 independent Q-networks, RED-Q style)

## Key Hyperparameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `lr` | 1e-4 | Adam for all networks |
| `batch_size` | 256 | |
| `discount` (γ) | 0.99 | |
| `critic_target_tau` | 0.01 | Soft update rate |
| `nstep` | 3 | N-step TD returns |
| `stddev_max/min` | 0.1/0.1 | Exploration noise |
| `num_warm_up_episode` | 50 | BC-guided warm-up |
| `num_train_step` | 200,000 | Total RL steps |
| `mix_rl_rate` | 1.0 | 1=pure RL buffer, <1 mixes BC data |
| `ibrl_eps_greedy` | 1.0 | ε for IBRL selection |
| `soft_ibrl_beta` | 10.0 | Softmax temperature for soft IBRL |
| `bc_loss_coef` | 0.1 | BC regularization weight (RFT only) |
| `update_freq` | 2 | Actor update every N critic updates |

## Repo Structure

```
ibrl/
├── train_rl.py              # Main RL training (517 lines)
├── train_bc.py              # BC pretraining (239 lines)
├── bc/
│   ├── bc_policy.py         # BcPolicy, StateBcPolicy
│   ├── multiview_encoder.py # Multi-camera fusion
│   └── dataset.py           # RobomimicDataset (HDF5)
├── rl/
│   ├── q_agent.py           # QAgent — core IBRL logic (640 lines)
│   ├── actor.py             # Actor network
│   ├── critic.py            # Dual-Q critic
│   └── replay.py            # Replay buffer with BC mixing
├── networks/
│   ├── encoder.py           # ViT, ResNet, ResNet96, DrQ encoders
│   └── min_vit.py           # Minimal Vision Transformer
├── env/
│   ├── robosuite_wrapper.py # PixelRobosuite wrapper
│   └── metaworld_wrapper.py # Meta-World wrapper
├── mw_main/                 # Meta-World training scripts
├── release/
│   ├── cfgs/                # YAML configs for all methods
│   ├── data/                # Datasets (Google Drive download)
│   └── model/               # Pretrained BC checkpoints
└── common_utils/            # C++ replay buffer (pybind11)
```

## Three Training Paradigms

| Method | Key Mechanism | Config Flag |
|--------|--------------|-------------|
| **IBRL** | Q-based selection between RL & BC actions | `act_method: "ibrl"` |
| **RLPD** | Mix demo data into replay buffer 50/50 | `mix_rl_rate: 0.5` |
| **RFT** | Fine-tune pretrained agent with BC loss | `add_bc_loss: 1`, `load_pretrained_agent: ...` |

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.9 | |
| PyTorch | 2.1.0 | CUDA 12.1 |
| MuJoCo | 2.1 (mujoco210) | Physics sim |
| mujoco-py | 2.1.2.14 | Python bindings |
| robosuite | git (custom) | Robomimic envs |
| metaworld | git (custom) | Meta-World envs |
| gym | 0.26.2 | |
| pyrallis | 0.3.1 | Config management |
| wandb | 0.16.4 | Logging |
| h5py | 3.10.0 | Dataset I/O |
| numpy | 1.24.1 | |

## Environments & Results

### Robomimic (pixel, 200 demos)

| Task | BC | RLPD | RFT | **IBRL** |
|------|-----|------|-----|----------|
| PickPlaceCan | ~75% | ~85% | ~88% | **~95%** |
| PickPlaceSquare | ~50% | ~60% | ~70% | **~85%** |

### Meta-World (state, 25 demos)

| Task | BC | RLPD | **IBRL** |
|------|-----|------|----------|
| Assembly | ~40% | ~70% | **~95%** |
| BoxClose | ~60% | ~80% | **~95%** |

IBRL consistently outperforms baselines, especially on harder tasks with longer horizons.

## Key Insights

- **No hard-coded curriculum**: the Q-function automatically decides when BC vs RL is better
- **Exploration + bootstrapping**: using BC for both gives compounding benefits
- **Warm-up matters**: 50 episodes of BC-guided exploration fills the buffer with good initial data
- **Dropout helps**: 0.5 dropout on the RL actor prevents overfitting to demo data
- **ViT encoder**: patch-based ViT with spatial embeddings outperforms CNN on pixel tasks
