# Decoupled Q-Chunking (DQC)

> **Decoupled Q-Chunking**
> Qiyang Li, Seohong Park, Sergey Levine (UC Berkeley)
> arXiv 2025 | [Paper](https://arxiv.org/abs/2512.10926) | [Code](https://github.com/ColinQiyangLi/dqc) | [Website](https://colinqiyangli.github.io/dqc)

## TL;DR

DQC improves upon [Q-Chunking (QC)](https://github.com/ColinQiyangLi/qc) by **decoupling the critic chunk size from the policy chunk size**. Long critic chunks (h) accelerate value learning; short policy chunks (h_a) improve policy learnability and reactivity. A distilled partial-chunk critic bridges the two via expectile/quantile regression.

## Problem

- TD methods suffer from slow value propagation in long-horizon sparse-reward tasks
- N-step returns speed up propagation but introduce off-policy bias
- QC groups actions into chunks for the critic, but forces the policy to output the same long chunk — hard to learn and reduces closed-loop reactivity
- QC assumes open-loop consistency (OLC) in the data, which real data rarely satisfies

## Key Contributions

1. **Theoretical analysis**: QC is near-optimal under OLC; DQC is near-optimal under the weaker BOV (Bounded Optimality Variability) condition
2. **Decoupled architecture**: critic uses chunk size h (e.g. 25), policy uses chunk size h_a (e.g. 5 or 1)
3. **Distilled partial critic**: bridges the gap between full-chunk critic and short-chunk policy via implicit maximization

## Method Overview

### Architecture (5 networks, jointly trained)

| Network | Class | Role | Input | Output |
|---------|-------|------|-------|--------|
| `chunk_critic` | `GCValue` (ensemble=2) | Q(s, a_{0:h}, g) over full action chunk | obs + goal + action_chunk[0:h] | scalar logit |
| `action_critic` | `GCValue` (ensemble=2) | Distilled Q^P(s, a_{0:h_a}, g) over policy chunk | obs + goal + action_chunk[0:h_a] | scalar logit |
| `target_action_critic` | `GCValue` (ensemble=2) | EMA target of action_critic | same as action_critic | scalar logit |
| `value` | `GCValue` (ensemble=1) | V(s, g) state-value | obs + goal | scalar logit |
| `actor_bc` | `ActorVectorField` | Flow-matching policy | obs + noisy_actions + time | velocity field |

All Q/V outputs are in **logit space** (sigmoid maps to [0,1] probabilities).

### Training Pipeline

**Step 1 — Chunk critic loss** (only when `use_chunk_critic=True`):
```
target = reward + gamma^h * mask * sigmoid(V(s_{t+h}, g))
L_chunk = BCE(Q_chunk_logit(s, a_{0:h}, g), clip(target, 0, 1))
```

**Step 2 — Action critic (distillation) loss**:
```
# Target comes from chunk_critic (if DQC) or n-step return (if QC/NS)
target_v = sigmoid(Q_chunk(s, a_{0:h}, g))   # DQC
# OR: target_v = reward + gamma^h * mask * sigmoid(V(s_{t+h}, g))  # QC/NS

# Expectile regression to distill into partial-chunk critic
weight = kappa_d if target_v >= q else (1 - kappa_d)
L_distill = weight * BCE(Q^P_logit, target_v)
```

**Step 3 — Value loss** (implicit value backup):
```
ex_q = agg(sigmoid(target_Q^P(s, a_{0:h_a}, g)))  # min or mean over ensemble
weight = kappa_b if ex_q >= v else (1 - kappa_b)
L_value = weight * BCE(V_logit, ex_q)  # or quantile loss on logits
```

**Step 4 — Actor loss** (conditional flow matching):
```
x_0 ~ N(0, I),  x_1 = a_{0:h_a}  (ground-truth partial chunk)
x_t = (1-t)*x_0 + t*x_1
L_actor = ||f_theta(s, x_t, t) - (x_1 - x_0)||^2
```

**Step 5 — Target update**: EMA on `action_critic` with tau=0.005.

### Inference (Best-of-N)

1. Sample N action chunks from flow policy (10 Euler steps)
2. Score each with `action_critic` (min or mean over ensemble)
3. Select highest-scoring chunk
4. Execute first `action_chunk_eval_size` actions, then re-plan

## Paper-Code Mapping

| Paper Concept | Code Location |
|---------------|---------------|
| DQC agent | `agents/dqc.py:DQCAgent` |
| Chunk critic Q(s,a_{0:h},g) | `agents/dqc.py:chunk_critic_loss()` using `GCValue` |
| Distilled critic Q^P | `agents/dqc.py:action_critic_loss()` — expectile/quantile distillation |
| Value function V(s,g) | `agents/dqc.py:action_critic_loss()` lines 115-131 |
| Flow-matching policy | `agents/dqc.py:actor_loss()`, `compute_flow_actions()` |
| Best-of-N extraction | `agents/dqc.py:sample_actions()` + `apply_bfn()` |
| Goal-conditioned dataset | `utils/datasets.py:CGCDataset` |
| OGBench environments | `envs/env_utils.py:make_ogbench_env_and_datasets()` |
| Network architectures | `utils/networks.py:GCValue`, `ActorVectorField`, `MLP` |
| Training loop | `main.py` |
| Reproduction configs | `experiments/reproduce.py` |

## Key Hyperparameters

| Parameter | Default | CLI Flag | Description |
|-----------|---------|----------|-------------|
| `backup_horizon` (h) | 25 | `--agent.backup_horizon` | Critic chunk size / n-step horizon |
| `policy_chunk_size` (h_a) | 1 | `--agent.policy_chunk_size` | Policy action chunk size |
| `use_chunk_critic` | True | `--agent.use_chunk_critic` | Enable separate chunk critic (DQC vs QC) |
| `kappa_b` | 0.9 | `--agent.kappa_b` | Implicit backup coefficient (value) |
| `kappa_d` | 0.5 | `--agent.kappa_d` | Distillation coefficient (action critic) |
| `distill_method` | expectile | `--agent.distill_method` | Loss type for distillation: expectile or quantile |
| `implicit_backup_type` | quantile | `--agent.implicit_backup_type` | Loss type for value backup: expectile or quantile |
| `best_of_n` | 32 | `--agent.best_of_n` | N for best-of-N policy extraction |
| `q_agg` | mean | `--agent.q_agg` | Q ensemble aggregation: mean or min |
| `flow_steps` | 10 | `--agent.flow_steps` | Euler integration steps for flow policy |
| `discount` | 0.999 | `--agent.discount` | Discount factor |
| `tau` | 0.005 | `--agent.tau` | Target network EMA rate |
| `lr` | 3e-4 | `--agent.lr` | Adam learning rate |
| `batch_size` | 4096 | `--agent.batch_size` | Batch size |
| `num_qs` | 2 | `--agent.num_qs` | Number of Q ensemble members |
| `actor_hidden_dims` | (1024,)*4 | — | Actor MLP layers |
| `value_hidden_dims` | (1024,)*4 | — | Critic/value MLP layers |

### Per-Environment Tuned Parameters

| Environment | q_agg | kappa_b | kappa_d | Dataset |
|-------------|-------|---------|---------|---------|
| cube-triple | min | 0.93 | 0.8 | 100m |
| cube-quadruple | min | 0.93 | 0.8 | 100m |
| cube-octuple | min | 0.93 | 0.5 | 1b |
| humanoidmaze-giant | mean | 0.5 | 0.8 | default |
| puzzle-4x5 | mean | 0.9 | 0.5 | default |
| puzzle-4x6 | mean | 0.7 | 0.5 | 1b |

## Baselines & Variants

| Method | Config | Description |
|--------|--------|-------------|
| **DQC** | `use_chunk_critic=True, h=25, h_a=5` | Full method |
| **QC** | `use_chunk_critic=False, h=h_a` | Original Q-chunking |
| **QC-NS** | `use_chunk_critic=False, h=25, h_a=5` | QC with n-step but no chunk critic |
| **NS** | `use_chunk_critic=False, h=25, h_a=1` | N-step returns, single-action policy |
| **OS** | `use_chunk_critic=False, h=1, h_a=1` | Standard 1-step TD |

## Dependencies

```
ogbench
jax >= 0.4.26
flax >= 0.8.4
distrax >= 0.1.5
ml_collections
matplotlib
moviepy
wandb
```

Built on top of [horizon-reduction](https://github.com/seohongpark/horizon-reduction) codebase. Uses [OGBench](https://github.com/seohongpark/ogbench) environments.

## Relationship to Q-Chunking (QC)

DQC is the direct follow-up to QC (same first author). Key differences:

| Aspect | QC | DQC |
|--------|-----|------|
| Critic chunk = Policy chunk | Yes (h = h_a) | No (h > h_a) |
| Separate chunk critic | No | Yes |
| Distillation step | No | Yes (expectile/quantile) |
| Theoretical guarantee | Under OLC | Under weaker BOV |
| Closed-loop reactivity | Limited by large h_a | High (small h_a) |

## Gotchas & Tips

- All Q/V values are in **logit space** — always apply `sigmoid()` before interpreting as probabilities
- The `valids` mask is critical for action chunks near trajectory boundaries
- `MUJOCO_GL=egl` is required for headless rendering on GPU servers
- Large datasets (100m, 1b) must be downloaded separately following [these instructions](https://github.com/seohongpark/horizon-reduction?tab=readme-ov-file#using-large-datasets)
- For `humanoidmaze-giant` and `puzzle-4x5`, set `--dataset_dir=None` (uses default OGBench download)
- Wandb logging is set to offline mode by default
- 10 seeds (100001–1000010) are used for paper results
