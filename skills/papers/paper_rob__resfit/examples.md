# ResFiT Examples & Reproduction

## Scenario 1: Train BC base policy (ACT on TwoArmCoffee)

```bash
python resfit/lerobot/scripts/train_bc_dexmg.py \
    --dataset ankile/dexmg-two-arm-coffee \
    --policy act \
    --steps 200000 \
    --batch_size 256 \
    --wandb_project dexmg-bc \
    --eval_env TwoArmCoffee \
    --rollout_freq 5000 \
    --eval_video_key observation.images.frontview \
    --eval_render_size 224 \
    --eval_num_envs 16 \
    --eval_num_episodes 100 \
    --wandb_enable
```

After training, note the `wandb_project/run_id` (e.g., `dexmg-bc/abc123`) and set it in the residual config.

## Scenario 2: Residual RL finetuning (TwoArmCoffee)

```bash
python resfit/rl_finetuning/scripts/train_residual_td3.py \
    --config-name=residual_td3_coffee_config \
    algo.prefetch_batches=4 \
    algo.n_step=5 \
    algo.gamma=0.995 \
    algo.learning_starts=10_000 \
    algo.critic_warmup_steps=10_000 \
    algo.num_updates_per_iteration=4 \
    algo.stddev_max=0.025 \
    algo.stddev_min=0.025 \
    algo.buffer_size=300_000 \
    agent.actor.action_scale=0.2 \
    agent.actor_lr=1e-6 \
    wandb.project=dexmg-coffee \
    wandb.name=resfit \
    wandb.group=resfit \
    debug=false
```

## Scenario 3: Available task configs

| Config Name | Task | Cameras |
|-------------|------|---------|
| `residual_td3_can_config` | Can (single-arm) | agentview + eye_in_hand |
| `residual_td3_square_config` | Square (single-arm) | agentview + eye_in_hand |
| `residual_td3_box_clean_config` | TwoArmBoxCleanup | agentview + 2x eye_in_hand |
| `residual_td3_coffee_config` | TwoArmCoffee | agentview + left/right hand |
| `residual_td3_two_arm_cansort_config` | TwoArmCanSortRandom | frontview + left/right hand |

## Scenario 4: Key ablation overrides

### Varying action scale (residual magnitude)
```bash
# Small corrections
agent.actor.action_scale=0.1
# Larger corrections
agent.actor.action_scale=0.3
```

### Varying n-step returns
```bash
algo.n_step=1   # 1-step TD (may struggle with sparse rewards)
algo.n_step=5   # 5-step (paper best for long-horizon tasks)
algo.n_step=10  # 10-step (more bias, faster credit assignment)
```

### UTD ratio
```bash
algo.num_updates_per_iteration=1   # Standard TD3
algo.num_updates_per_iteration=4   # Paper default (RLPD-style)
algo.num_updates_per_iteration=8   # More aggressive
```

### Exploration noise
```bash
algo.stddev_max=0.025  algo.stddev_min=0.025  # Low (paper best for coffee)
algo.stddev_max=0.05   algo.stddev_min=0.05   # Medium
algo.stddev_max=0.1    algo.stddev_min=0.1    # High
```

## Scenario 5: Integrating the residual approach in your own project

The key abstraction is `BasePolicyVecEnvWrapper` -- it wraps any vectorized env + frozen BC policy so that the RL agent only needs to output small residual actions.

```python
from resfit.rl_finetuning.wrappers.residual_env_wrapper import BasePolicyVecEnvWrapper
from resfit.rl_finetuning.utils.normalization import ActionScaler, StateStandardizer

# 1. Create your vectorized env and load BC policy
vec_env = create_vectorized_env(env_name="YourTask", num_envs=1, device="cuda")
base_policy = load_your_bc_policy()

# 2. Create normalizers from dataset stats
action_scaler = ActionScaler.from_dataset_stats(action_stats, action_scale=0.2)
state_standardizer = StateStandardizer.from_dataset_stats(state_stats)

# 3. Wrap -- now the env expects residual actions and returns augmented obs
env = BasePolicyVecEnvWrapper(vec_env, base_policy, action_scaler, state_standardizer)

# 4. Create residual agent
agent = QAgent(
    obs_shape=(3, 84, 84),
    prop_shape=(prop_dim,),
    action_dim=action_dim,
    rl_cameras=["observation.images.agentview"],
    cfg=QAgentConfig(
        actor_lr=1e-6,
        critic_lr=1e-4,
        actor=ActorConfig(action_scale=0.2, actor_last_layer_init_scale=0.0),
    ),
    residual_actor=True,
)

# 5. Training loop: agent outputs residual, env adds it to base
obs, info = env.reset()
residual_action = agent.act(obs, eval_mode=False, stddev=0.025)
next_obs, reward, terminated, truncated, info = env.step(residual_action)
# info["scaled_action"] contains the full combined normalized action
```

## Scenario 6: RLPD baseline (non-residual) comparison

The repo also includes a standard RLPD baseline (no residual, trains from scratch with offline demos):

```bash
python resfit/rl_finetuning/scripts/train_rlpd_dexmg.py \
    --config-name=rlpd_coffee_config \
    algo.n_step=5 \
    algo.gamma=0.995 \
    algo.num_updates_per_iteration=4 \
    wandb.project=dexmg-coffee-rlpd
```
