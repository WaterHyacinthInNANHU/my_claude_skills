# ResFiT: Residual Off-Policy RL for Finetuning Behavior Cloning Policies

> Ankile, Jiang, Duan, Shi, Abbeel, Nagabandi (Stanford / Amazon FAR / CMU / UC Berkeley, 2025)

| Resource | Link |
|----------|------|
| Paper | https://arxiv.org/abs/2509.19301 |
| Project page | https://residual-offpolicy-rl.github.io/ |
| Code | https://github.com/amazon-far/residual-offpolicy-rl |
| License | CC-BY-NC-4.0 |

## What It Does

ResFiT finetunes pre-trained BC policies by learning **lightweight per-step residual corrections** via off-policy RL (TD3-based). The BC policy is treated as a frozen black box; a residual actor outputs small additive corrections (`action_scale * tanh(...)`) that are summed with BC actions before environment execution.

Key results:
- 200x more sample-efficient than on-policy (PPO) approaches (200k vs 40M steps)
- First real-world RL training on a humanoid robot with dexterous hands (29-DoF Vega)
- BoxClean: 98% success vs 77% BC baseline

## Method Overview

```
                    obs
                     |
            +--------+--------+
            |                 |
     [BC Policy (frozen)]  [RL Residual Actor]
            |                 |
        base_action     residual_action (scaled by action_scale, e.g. 0.1-0.2)
            |                 |
            +--------+--------+
                     |
            combined = clamp(base + residual, -1, 1)
                     |
                [Environment]
                     |
              sparse reward {0, 1}
```

**Two-phase training:**
1. **Critic warmup** (`critic_warmup_steps`): Only train critic, actor frozen. Random exploration noise around base policy.
2. **Joint training**: Train both critic and actor with off-policy TD3 + n-step returns.

**Key design choices:**
- UTD ratio = 4 (updates per env step)
- N-step returns (n=5) for sparse reward propagation
- 10-head critic ensemble (RED-Q style), min over 2 random heads for target
- Layer normalization throughout
- Offline demo mixing (50% offline / 50% online by default, RLPD-style)

## Architecture

| Component | Architecture | Details |
|-----------|-------------|---------|
| Vision encoder | MinViT | 1-layer, 128-dim, 4 heads, patch_size=8 on 84x84 images |
| Actor | SpatialEmb + MLP | 2-layer MLP (1024 hidden), Tanh output scaled by `action_scale` |
| Critic | SpatialEmbQEnsemble | Shared spatial trunk + 10 vmap'd MLP heads (1024 hidden) |
| Base policy | ACT (from LeRobot) | Frozen, loaded from W&B artifacts |

## Paper-Code Mapping

| Paper Concept | Code Location |
|---------------|---------------|
| Residual environment wrapper | `resfit/rl_finetuning/wrappers/residual_env_wrapper.py:BasePolicyVecEnvWrapper` |
| Residual actor (additive correction) | `resfit/rl_finetuning/off_policy/rl/actor.py:Actor` (`residual_actor=True`) |
| TD3 Q-agent (critic + actor update) | `resfit/rl_finetuning/off_policy/rl/q_agent.py:QAgent` |
| Critic ensemble (vmap'd heads) | `resfit/rl_finetuning/off_policy/rl/critic.py:SpatialEmbQEnsemble` |
| ViT image encoder | `resfit/rl_finetuning/off_policy/networks/encoder.py:VitEncoder` |
| Main training loop | `resfit/rl_finetuning/scripts/train_residual_td3.py:main()` |
| Config dataclasses (Hydra) | `resfit/rl_finetuning/config/residual_td3.py` |
| Base RLPD config | `resfit/rl_finetuning/config/rlpd.py` |
| N-step replay transform | `resfit/rl_finetuning/utils/rb_transforms.py:MultiStepTransform` |
| Action normalization | `resfit/rl_finetuning/utils/normalization.py:ActionScaler` |

## Key Classes & Signatures

### BasePolicyVecEnvWrapper
```python
# resfit/rl_finetuning/wrappers/residual_env_wrapper.py
class BasePolicyVecEnvWrapper:
    def __init__(self, vec_env, base_policy: ACTPolicy, action_scaler, state_standardizer):
        ...
    def reset(self) -> tuple[dict[str, Tensor], dict]:
        # Returns augmented obs with "observation.base_action" key
    def step(self, residual_naction: Tensor) -> tuple[dict, Tensor, Tensor, Tensor, dict]:
        # combined = base_naction + residual_naction, then unscale for env
```

### QAgent
```python
# resfit/rl_finetuning/off_policy/rl/q_agent.py
class QAgent(nn.Module):
    def __init__(self, obs_shape, prop_shape, action_dim, rl_cameras, cfg: QAgentConfig, residual_actor=True):
        ...
    def act(self, obs: dict[str, Tensor], eval_mode=False, stddev=0.0, cpu=True) -> Tensor:
        # Returns residual action
    def update(self, batch, stddev, update_actor, bc_batch=None, ref_agent=None) -> dict:
        # Full critic + actor update step
```

### Actor (Residual Mode)
```python
# resfit/rl_finetuning/off_policy/rl/actor.py
class Actor(nn.Module):
    def __init__(self, repr_dim, patch_repr_dim, prop_dim, action_dim, cfg: ActorConfig, residual_actor=True):
        # When residual_actor=True, takes base_action as additional input
    def forward(self, obs: dict, std: float) -> TruncatedNormal:
        # Returns distribution over scaled_mu = tanh(policy(x)) * action_scale
```

## Config Hierarchy

```
ResidualTD3DexmgConfig          # Top-level experiment config
├── algo: ResidualTD3AlgoConfig  # Training hyperparams
│   ├── total_timesteps: 300_000
│   ├── batch_size: 256
│   ├── n_step: 3 (override to 5)
│   ├── gamma: 0.99 (override to 0.995)
│   ├── num_updates_per_iteration: 4  (UTD ratio)
│   ├── critic_warmup_steps: 10_000
│   ├── learning_starts: 10_000
│   ├── offline_fraction: 0.5
│   ├── stddev_max/min: 0.05
│   └── random_action_noise_scale: 0.2
├── agent: QAgentConfig
│   ├── actor_lr: 1e-6
│   ├── critic_lr: 1e-4
│   ├── critic_target_tau: 0.005
│   └── actor: ActorConfig
│       ├── action_scale: 0.1 (override to 0.2)
│       └── actor_last_layer_init_scale: 0.0  # Critical: start residual at zero
├── base_policy: BasePolicyConfig
│   └── wandb_id: "<project>/<run_id>"
├── offline_data: OfflineDataConfig
│   └── name: "ankile/dexmg-two-arm-coffee" (HuggingFace dataset)
└── wandb: WandBConfig
```

## Key Hyperparameters

| Parameter | Default | Paper Best | Notes |
|-----------|---------|------------|-------|
| `action_scale` | 0.1 | 0.2 | Max magnitude of residual correction |
| `actor_last_layer_init_scale` | 0.0 | 0.0 | Initialize residual to zero (critical) |
| `n_step` | 3 | 5 | N-step returns for sparse rewards |
| `gamma` | 0.99 | 0.995 | Higher gamma for long horizons |
| `num_updates_per_iteration` | 4 | 4 | UTD ratio |
| `critic_warmup_steps` | 10,000 | 10,000 | Critic-only training before actor |
| `learning_starts` | 10,000 | 10,000 | Random exploration steps |
| `actor_lr` | 1e-6 | 1e-6 | Very low actor LR for stability |
| `critic_lr` | 1e-4 | 1e-4 | Standard critic LR |
| `stddev_max/min` | 0.05 | 0.025 | Exploration noise (constant) |
| `offline_fraction` | 0.5 | 0.5 | RLPD-style demo mixing |
| `buffer_size` | 200,000 | 300,000 | Replay buffer capacity |
| `critic.num_q` | 10 | 10 | Q-ensemble size (RED-Q) |

## Dependencies

```
python==3.10
torch (CUDA 12.8)
torchrl==0.9.2
draccus==0.10.0
hydra-core
omegaconf
lerobot  # HuggingFace LeRobot
wandb
mujoco (via robosuite/DexMG environments)
```

## Installation

```bash
conda create -n residual python=3.10 -y && conda activate residual
git clone https://github.com/amazon-far/residual-offpolicy-rl
cd residual-offpolicy-rl

# Core deps
./resfit/rl_finetuning/setup_rlpd_robosuite.sh
pip install wandb draccus==0.10.0 torchrl==0.9.2 hydra-core serial deepdiff matplotlib

# Auth
huggingface-cli login
wandb login
```

## Gotchas & Tips

- `actor_last_layer_init_scale=0.0` is critical -- ensures the residual starts at zero so the combined policy equals the BC policy at init
- The environment wrapper (`BasePolicyVecEnvWrapper`) handles the base+residual action combination -- the training loop only sees residual actions
- Images stored as uint8 in replay buffer to save GPU memory; converted to float on the fly
- Only `num_envs=1` is supported due to n-step return implementation
- Base policy weights loaded from W&B artifacts -- you need to train BC first and log to W&B
- The `action_scaler` normalizes actions to [-1, 1] range for both base and residual policies
