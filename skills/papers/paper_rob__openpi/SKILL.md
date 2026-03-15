---
name: paper_rob__openpi
description: Physical Intelligence VLA foundation models (pi0, pi0-FAST, pi0.5) for generalist robot control
---

# paper_rob__openpi

OpenPI provides open-source **Vision-Language-Action (VLA)** foundation models from Physical Intelligence. Three model variants -- pi0, pi0-FAST, and pi0.5 -- share a PaliGemma backbone and differ in their action decoding strategy. Pre-trained on 10k+ hours of multi-platform robot data, they can be fine-tuned on custom tasks with as little as a single GPU.

## Paper Info

| Field | Value |
|-------|-------|
| Title (pi0) | pi0: A Vision-Language-Action Flow Model for General Robot Control |
| Title (pi0.5) | pi0.5: A Vision-Language-Action Model with Open-World Generalization |
| Authors | Kevin Black, Noah Brown, Danny Driess, Chelsea Finn, Sergey Levine, et al. (Physical Intelligence) |
| Year | 2024-2025 |
| Venue | RSS 2025 (pi0); arXiv (pi0.5) |
| Paper (pi0) | [arXiv:2410.24164](https://arxiv.org/abs/2410.24164) |
| Paper (pi0.5) | [arXiv:2504.16054](https://arxiv.org/abs/2504.16054) |
| Code | [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) |
| Checkpoints | `gs://openpi-assets/checkpoints/` |
| License | Apache 2.0 |

## Method Overview

All three models share a two-stage training recipe analogous to LLM pre-training and post-training:

1. **Pre-training** on 10k+ hours of robot data across 7 platforms and 68 tasks.
2. **Post-training (fine-tuning)** to adapt to a specific downstream task or robot.

The backbone is **PaliGemma** (SigLip So400m/14 vision encoder + Gemma 2B language model). An **action expert** (a smaller Gemma 300M model) decodes actions conditioned on the VLM's representation. The three variants differ in how the action expert produces actions:

| Model | Action Decoder | Token Length | Denoising Steps | Key Feature |
|-------|---------------|-------------|-----------------|-------------|
| **pi0** | Flow matching (continuous diffusion) | 48 | 10 (inference) | High-freq continuous actions at 50 Hz |
| **pi0-FAST** | Autoregressive (FAST tokenizer) | 250 | N/A (single pass AR) | Faster inference, discrete action tokens |
| **pi0.5** | Flow matching + adaRMSNorm | 200 | 10 (inference) | Knowledge insulation for better generalization |

Key insight: Using a separate action expert with flow matching decouples action generation from language understanding, enabling the VLM backbone to retain its semantic knowledge while learning fine-grained motor control.

## Paper-Code Mapping

| Paper Concept | Code Location | Notes |
|---------------|---------------|-------|
| Pi0 model (flow matching) | `src/openpi/models/pi0.py:Pi0` | `compute_loss()` implements flow matching; `sample_actions()` does Euler ODE integration |
| Pi0.5 model | `src/openpi/models/pi0.py:Pi0` | Same class, activated via `Pi0Config(pi05=True)` which enables adaRMSNorm |
| Pi0-FAST model (autoregressive) | `src/openpi/models/pi0_fast.py:Pi0FAST` | Cross-entropy loss on FAST-tokenized actions |
| Pi0 config | `src/openpi/models/pi0_config.py:Pi0Config` | `pi05=True` toggles pi0.5; `action_horizon`, `action_dim`, `paligemma_variant` |
| Pi0-FAST config | `src/openpi/models/pi0_fast.py:Pi0FASTConfig` | `fast_model_tokenizer`, `max_token_len` |
| PaliGemma backbone | `src/openpi/models/gemma.py:Module` | Dual-config Gemma (PaliGemma + action expert) |
| SigLip vision encoder | `src/openpi/models/siglip.py:Module` | So400m/14 variant, 224x224 input |
| LoRA | `src/openpi/models/lora.py:LoRAConfig` | `rank`, `alpha`, `rslora` support |
| Flow matching loss (Eq. 1) | `pi0.py:Pi0.compute_loss` L196-214 | Beta(1.5, 1) time sampling, `u_t = noise - actions` |
| Flow matching sampling | `pi0.py:Pi0.sample_actions` L216-279 | Euler integration with KV cache for prefix |
| Attention mask (prefix-LM) | `pi0.py:make_attn_mask` | Prefix bidirectional + suffix causal via cumulative AR mask |
| adaRMSNorm (pi0.5) | `pi0.py:Pi0.embed_suffix` L162-169 | Time MLP -> swish -> adarms_cond passed to action expert |
| Data transforms pipeline | `src/openpi/transforms.py` | `RepackTransform`, `Normalize`, `DeltaActions`, `TokenizePrompt`, `ResizeImages`, `PadStatesAndActions` |
| Training configs | `src/openpi/training/config.py:_CONFIGS` | All named configs in a list; accessed via `get_config(name)` |
| Policy serving | `src/openpi/policies/policy.py:Policy` | `infer()` applies transforms -> `sample_actions()` -> output transforms |
| PyTorch model | `src/openpi/models_pytorch/pi0_pytorch.py:PI0Pytorch` | PyTorch reimplementation for multi-GPU DDP training |

## Setup

### Dependencies

- Python 3.11+
- JAX (for default training) or PyTorch (>= transformers 4.53.2, for DDP training)
- CUDA 12.x+
- Key packages: `flax`, `optax`, `orbax-checkpoint`, `tyro`, `einops`, `augmax`, `wandb`, `safetensors`
- LeRobot (included as git submodule for data loading)

### Installation

```bash
# Clone with LeRobot submodule
git clone --recurse-submodules https://github.com/Physical-Intelligence/openpi.git
cd openpi
git submodule update --init --recursive

# Install with uv (recommended)
GIT_LFS_SKIP_SMUDGE=1 uv sync
GIT_LFS_SKIP_SMUDGE=1 uv pip install -e .
```

Docker: see `docs/docker.md`.

### Hardware Requirements

| Mode | VRAM | Example GPU |
|------|------|-------------|
| Inference | >= 8 GB | RTX 4090 |
| LoRA fine-tuning | >= 22.5 GB | RTX 4090 |
| Full fine-tuning | >= 70 GB | A100 / H100 |

### Available Checkpoints

**Base models** (starting points for fine-tuning):

| Config name | Checkpoint path |
|-------------|----------------|
| `pi0_base` | `gs://openpi-assets/checkpoints/pi0_base` |
| `pi0_fast_base` | `gs://openpi-assets/checkpoints/pi0_fast_base` |
| `pi05_base` | `gs://openpi-assets/checkpoints/pi05_base` |

**Fine-tuned experts** (ready for inference):

| Config name | Platform | Task |
|-------------|----------|------|
| `pi0_fast_droid` | DROID | General manipulation |
| `pi05_droid` | DROID | General manipulation |
| `pi0_aloha_towel` | ALOHA | Towel folding |
| `pi0_aloha_tupperware` | ALOHA | Tupperware unpacking |
| `pi05_libero` | LIBERO | Benchmark tasks |
| `pi0_aloha_sim` | ALOHA sim | Transfer cube |

Checkpoints auto-download from GCS on first use via `download.maybe_download()`.

## Usage Scenarios

### Serve a Trained Policy (Inference)

```bash
uv run scripts/serve_policy.py policy:checkpoint \
  --policy.config=pi05_droid \
  --policy.dir=gs://openpi-assets/checkpoints/pi05_droid
```

WebSocket server starts on port 8000. Health check: `GET /healthz`.

### Fine-Tune with JAX

```bash
# 1. Compute normalization stats (required before first train)
uv run scripts/compute_norm_stats.py --config-name pi05_libero

# 2. Train
XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run scripts/train.py pi05_libero \
  --exp-name=my_experiment
```

### Fine-Tune with PyTorch (Multi-GPU)

```bash
# Multi-GPU
torchrun --nproc_per_node=8 scripts/train_pytorch.py pi05_libero \
  --exp-name=my_experiment

# Single GPU
python scripts/train_pytorch.py pi05_libero --exp-name=my_experiment
```

### Convert JAX Checkpoint to PyTorch

```bash
python examples/convert_jax_model_to_pytorch.py \
  --checkpoint_dir gs://openpi-assets/checkpoints/pi0_base \
  --output_path ./pi0_base_pytorch \
  --config_name pi0_base
```

### Key TrainConfig Fields

| Field | Default | Description |
|-------|---------|-------------|
| `model` | `Pi0Config()` | Model config (Pi0Config or Pi0FASTConfig) |
| `data` | `FakeDataConfig()` | Data config factory |
| `batch_size` | `32` | Global batch size |
| `num_train_steps` | `30_000` | Total training steps |
| `lr_schedule` | `CosineDecaySchedule(peak_lr=2.5e-5)` | LR schedule |
| `optimizer` | `AdamW(b1=0.9, b2=0.95, clip_gradient_norm=1.0)` | Optimizer |
| `ema_decay` | `0.99` | EMA for weights (set `None` for LoRA) |
| `save_interval` | `1000` | Checkpoint save frequency |
| `freeze_filter` | `nnx.Nothing` | Which params to freeze (for LoRA) |
| `fsdp_devices` | `1` | FSDP sharding across N devices |
| `pytorch_weight_path` | `None` | Path to PyTorch checkpoint for PT training |
| `pytorch_training_precision` | `"bfloat16"` | Precision for PyTorch training |

## Code Integration Guide

### Client-Side Inference (Recommended)

The simplest integration path is to run the policy server and connect via `openpi-client`:

```python
# pip install openpi-client
from openpi_client import websocket_client_policy as wcp

policy = wcp.WebsocketClientPolicy(host="SERVER_IP", port=8000)

action = policy.infer({
    "observation/image": camera_image,       # (H, W, 3) uint8
    "observation/state": robot_state,        # (state_dim,) float32
    "prompt": "pick up the red cup",
})["actions"]  # shape: (horizon, action_dim) float32
```

### Direct Python API (In-Process)

```python
from openpi.training import config as _config
from openpi.policies import policy_config
from openpi.shared import download

# Load config and checkpoint
config = _config.get_config("pi05_droid")
ckpt_dir = download.maybe_download("gs://openpi-assets/checkpoints/pi05_droid")

# create_trained_policy auto-detects JAX vs PyTorch checkpoint
policy = policy_config.create_trained_policy(config, ckpt_dir)

# Run inference
import numpy as np
result = policy.infer({
    "observation/exterior_image_1_left": np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8),
    "observation/wrist_image_left": np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8),
    "observation/joint_position": np.zeros(7, dtype=np.float32),
    "observation/gripper_position": np.zeros(1, dtype=np.float32),
    "prompt": "pick up the block",
})
actions = result["actions"]  # (horizon, action_dim)
```

### Data Format

Input observation dict (after repack transforms):

| Field | Shape / Type | Description |
|-------|-------------|-------------|
| `image/base_0_rgb` | `(224, 224, 3)` float32 in [-1,1] or uint8 [0,255] | Base camera RGB |
| `image/left_wrist_0_rgb` | `(224, 224, 3)` | Left wrist camera (optional, masked if absent) |
| `image/right_wrist_0_rgb` | `(224, 224, 3)` | Right wrist camera (optional, masked if absent) |
| `image_mask/*` | `bool` scalar | True if corresponding image is valid |
| `state` | `(action_dim,)` float32 | Robot proprioceptive state |
| `actions` | `(action_horizon, action_dim)` float32 | Target action chunk (training only) |
| `tokenized_prompt` | `(max_token_len,)` int32 | Tokenized language (added by model transforms) |

**Standard 16-dim action space** (used by ALOHA-type configs):

| Dims | Meaning |
|------|---------|
| 0-5 | Left arm joints (rad) |
| 6 | Left gripper (0=open, 1=closed) |
| 7-12 | Right arm joints (rad) |
| 13 | Right gripper |
| 14-15 | Mobile base velocity |

### Data Pipeline

```
Raw dataset -> Repack transforms -> Data transforms -> Normalize -> Model transforms -> Model
                (key remapping)     (robot-specific)   (z-score     (tokenize, resize,
                                                        or quantile) pad)
```

Defined in `DataConfig` with three `transforms.Group` fields: `repack_transforms`, `data_transforms`, `model_transforms`. Each group has `inputs` (applied before model) and `outputs` (applied after model, inference only).

### Integration Notes

- The repo uses `uv` for dependency management; running scripts outside `uv` requires manual path/dependency setup.
- Image inputs can be uint8 [0, 255] -- `Observation.from_dict()` auto-converts to float32 [-1, 1].
- The `openpi-client` package (`packages/openpi-client/`) is independently installable via `pip install openpi-client`.
- For PyTorch models, `create_trained_policy()` auto-detects by checking for `model.safetensors` in the checkpoint dir.
- Different robot platforms require different observation key names; check the corresponding `*_policy.py` files and repack transforms.

## Config System

**Dataclass-based** with **Tyro** CLI parsing (not Hydra/YAML).

```python
from openpi.training import config as _config

# Load a named config
config = _config.get_config("pi05_libero")

# CLI: tyro.extras.overridable_config_cli(...)
config = _config.cli()
```

All configs are defined in `_CONFIGS` list in `src/openpi/training/config.py`. Key data config factories:

| Factory | Purpose |
|---------|---------|
| `LeRobotLiberoDataConfig` | LIBERO tasks (LeRobot format) |
| `LeRobotAlohaDataConfig` | ALOHA tasks (with `adapt_to_pi` for PI runtime joint space) |
| `RLDSDroidDataConfig` | Full DROID dataset (RLDS/TFRecords, ~1.8 TB) |
| `LeRobotDROIDDataConfig` | Custom DROID subsets (LeRobot format) |
| `SimpleDataConfig` | Generic config with pluggable transform factories |

## Core Architecture

```
Images ──> SigLip So400m/14 ──┐
                               ├──> PaliGemma (Gemma 2B, prefix-LM attn) ──┐
Language prompt ───────────────┘                                            │
                                                                            v
                                                               ┌─── Action Expert (Gemma 300M) ───┐
                                                               │  pi0:   flow matching             │
                                                               │         state_proj + action_time_  │
                                                               │         mlp merges timestep+action │
                                                               │  pi0.5: adaRMSNorm injects        │
                                                               │         timestep; no state_proj    │
                                                               │  FAST:  autoregressive decoding    │
                                                               │         with FAST tokenizer        │
                                                               └───────────────────────────────────┘
                                                                            │
                                                                  Action chunk output
                                                               (action_horizon x action_dim)
```

**Flow matching** (pi0/pi0.5): Time sampled from Beta(1.5, 1), noisy actions `x_t = t*noise + (1-t)*actions`, velocity target `u_t = noise - actions`. Inference: Euler ODE integration from t=1 (noise) to t=0 (clean) with KV-cached prefix.

**Autoregressive** (pi0-FAST): Actions tokenized by FAST tokenizer into discrete tokens, predicted via standard next-token prediction with cross-entropy loss. EOS token (id=1) for early stopping.

## Repo Structure

| Path | Purpose |
|------|---------|
| `src/openpi/models/pi0.py` | Pi0/Pi0.5 model: `Pi0` class with `compute_loss`, `sample_actions` |
| `src/openpi/models/pi0_fast.py` | Pi0-FAST model: `Pi0FAST` class, `Pi0FASTConfig` |
| `src/openpi/models/pi0_config.py` | `Pi0Config` dataclass (shared by pi0 and pi0.5) |
| `src/openpi/models/model.py` | `BaseModel`, `BaseModelConfig`, `Observation`, `Actions`, `restore_params` |
| `src/openpi/models/gemma.py` | Gemma LLM (Flax/Linen), dual-config for PaliGemma + action expert |
| `src/openpi/models/siglip.py` | SigLip vision encoder |
| `src/openpi/models/lora.py` | `LoRAConfig`, `Einsum` with LoRA support |
| `src/openpi/models/tokenizer.py` | `PaligemmaTokenizer`, `FASTTokenizer` |
| `src/openpi/models_pytorch/pi0_pytorch.py` | `PI0Pytorch` -- PyTorch implementation for DDP training |
| `src/openpi/training/config.py` | `TrainConfig`, all named configs (`_CONFIGS`), `get_config()`, `cli()` |
| `src/openpi/training/optimizer.py` | `CosineDecaySchedule`, `AdamW` config |
| `src/openpi/training/data_loader.py` | Unified data loader (LeRobot + RLDS) |
| `src/openpi/transforms.py` | Transform primitives: `RepackTransform`, `Normalize`, `DeltaActions`, `ResizeImages`, `TokenizePrompt`, `PadStatesAndActions` |
| `src/openpi/policies/policy.py` | `Policy` class wrapping model + transforms for inference |
| `src/openpi/policies/policy_config.py` | `create_trained_policy()` -- loads checkpoint and builds Policy |
| `src/openpi/policies/libero_policy.py` | LIBERO-specific input/output transforms |
| `src/openpi/policies/droid_policy.py` | DROID-specific transforms |
| `src/openpi/policies/aloha_policy.py` | ALOHA-specific transforms (with `adapt_to_pi` joint mapping) |
| `scripts/train.py` | JAX training entry point |
| `scripts/train_pytorch.py` | PyTorch DDP training entry point |
| `scripts/serve_policy.py` | WebSocket policy server |
| `scripts/compute_norm_stats.py` | Compute normalization statistics for a config |
| `packages/openpi-client/` | Standalone client package (`pip install openpi-client`) |
| `examples/libero/main.py` | LIBERO evaluation script |
| `examples/simple_client/main.py` | Timing benchmark client |
| `examples/convert_jax_model_to_pytorch.py` | JAX-to-PyTorch checkpoint converter |
| `examples/aloha_real/` | Real ALOHA robot integration |
| `examples/droid/` | DROID data conversion and evaluation |

## Fine-Tuning Configs Reference

| Config | Model | Dataset | Method | Notes |
|--------|-------|---------|--------|-------|
| `pi0_libero` | pi0 | LIBERO | Full | Base example for custom fine-tuning |
| `pi0_libero_low_mem_finetune` | pi0 | LIBERO | LoRA | `gemma_2b_lora` + `gemma_300m_lora`, ~22.5 GB VRAM |
| `pi0_fast_libero` | pi0-FAST | LIBERO | Full | `action_dim=7, action_horizon=10, max_token_len=180` |
| `pi0_fast_libero_low_mem_finetune` | pi0-FAST | LIBERO | LoRA | `gemma_2b_lora` variant |
| `pi05_libero` | pi0.5 | LIBERO | Full | `batch_size=256, peak_lr=5e-5, ema_decay=0.999` |
| `pi0_aloha_pen_uncap` | pi0 | ALOHA | Full | Pen uncapping, 20k steps |
| `pi05_aloha_pen_uncap` | pi0.5 | ALOHA | Full | `batch_size=64` |
| `pi0_fast_full_droid_finetune` | pi0-FAST | DROID (RLDS, ~1.8 TB) | Full | ~2d on 8xH100, `num_workers=0` required |
| `pi05_full_droid_finetune` | pi0.5 | DROID (RLDS) | Full | 100k steps, `batch_size=256` |
| `pi05_droid_finetune` | pi0.5 | DROID (LeRobot) | Full | For custom DROID subsets |
| `pi0_aloha_sim` | pi0 | ALOHA sim | Full | Transfer cube demo |

## Tips & Gotchas

- **Always run `compute_norm_stats.py` before training on new data.** Training will use incorrect normalization without it.
- Set `XLA_PYTHON_CLIENT_MEM_FRACTION=0.9` for JAX training to avoid OOM.
- Use `GIT_LFS_SKIP_SMUDGE=1` during install -- weights download on demand from GCS.
- LoRA reduces VRAM from ~70 GB to ~22.5 GB with minimal quality loss. Set `ema_decay=None` when using LoRA.
- Checkpoints auto-download from GCS on first use and cache to `~/.cache/openpi/`.
- Pi0.5 generally outperforms pi0 due to knowledge insulation (adaRMSNorm decouples timestep injection).
- For custom robots: provide normalization stats matching your action/state dims. Use `AssetsConfig(assets_dir=..., asset_id=...)` to reuse existing stats.
- RLDS data loader requires `num_workers=0` -- it handles multi-processing internally.
- The `max_token_len` for pi0-FAST should be ~180 for single-arm robots, ~250 for dual-arm. Too small clips tokens; too large wastes memory.
- Pi0/pi0.5 use `action_dim=32` by default (padded); pi0-FAST uses the actual action dim (e.g., 7 for single-arm).
- Flow matching uses t=1 for noise and t=0 for clean data (opposite of the pi0 paper convention).
- Gemma variants: `"gemma_2b"` (PaliGemma backbone), `"gemma_300m"` (action expert), `"gemma_2b_lora"` / `"gemma_300m_lora"` (LoRA versions), `"dummy"` (for debugging).
- PyTorch training does not support EMA; use JAX training for EMA-based fine-tuning.
- For DDP PyTorch training, batch size is automatically split across GPUs (`effective_batch_size = batch_size // world_size`).
