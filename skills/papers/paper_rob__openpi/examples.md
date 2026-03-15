# OpenPI Examples & Recipes

## 1. Serve a Pre-Trained Policy (Inference)

```bash
# DROID robot
uv run scripts/serve_policy.py policy:checkpoint \
  --policy.config=pi05_droid \
  --policy.dir=gs://openpi-assets/checkpoints/pi05_droid

# ALOHA towel folding
uv run scripts/serve_policy.py policy:checkpoint \
  --policy.config=pi0_aloha_towel \
  --policy.dir=gs://openpi-assets/checkpoints/pi0_aloha_towel

# LIBERO benchmark
uv run scripts/serve_policy.py policy:checkpoint \
  --policy.config=pi05_libero \
  --policy.dir=gs://openpi-assets/checkpoints/pi05_libero
```

WebSocket server starts on port 8000 by default.

## 2. Client-Side Robot Control

Install the standalone client package on the robot machine:

```bash
pip install openpi-client
```

### DROID Robot

```python
from openpi_client import websocket_client_policy as wcp
import numpy as np

policy = wcp.WebsocketClientPolicy(host="SERVER_IP", port=8000)

# Observation keys must match the DROID repack transforms
obs = {
    "observation/exterior_image_1_left": camera_image,   # (H, W, 3) uint8
    "observation/wrist_image_left": wrist_image,         # (H, W, 3) uint8
    "observation/joint_position": joint_pos,             # (7,) float32
    "observation/gripper_position": gripper_pos,         # (1,) float32
    "prompt": "pick up the red cup",
}
result = policy.infer(obs)
actions = result["actions"]  # (horizon, action_dim) float32
```

### ALOHA Robot

```python
obs = {
    "state": joint_state,          # (14,) float32
    "images": {
        "cam_high": top_cam,       # (3, 224, 224) uint8 or (224, 224, 3)
        "cam_left_wrist": left,
        "cam_right_wrist": right,
    },
    "prompt": "fold the towel",
}
result = policy.infer(obs)
actions = result["actions"]  # (50, 16) for pi0, (10, 16) for pi0.5
```

### LIBERO Environment

```python
obs = {
    "observation/image": agentview_image,      # (224, 224, 3) uint8
    "observation/wrist_image": wrist_image,    # (224, 224, 3) uint8
    "observation/state": robot_state,          # (8,) float32: eef_pos(3) + eef_axisangle(3) + gripper(2)
    "prompt": task_description,
}
result = policy.infer(obs)
```

## 3. Fine-Tune on LIBERO (Full Fine-Tuning)

```bash
cd openpi

# Step 1: Compute normalization statistics
uv run scripts/compute_norm_stats.py --config-name pi05_libero

# Step 2: Train with JAX
XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run scripts/train.py pi05_libero \
  --exp-name=libero_v1

# Step 3: Serve the trained model
uv run scripts/serve_policy.py policy:checkpoint \
  --policy.config=pi05_libero \
  --policy.dir=checkpoints/pi05_libero/libero_v1/29999
```

## 4. LoRA Fine-Tuning (Low Memory, ~22.5 GB VRAM)

For GPUs with limited VRAM (e.g., RTX 4090):

```bash
# Pi0 with LoRA
uv run scripts/compute_norm_stats.py --config-name pi0_libero_low_mem_finetune

XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run scripts/train.py \
  pi0_libero_low_mem_finetune \
  --exp-name=libero_lora

# Pi0-FAST with LoRA
uv run scripts/compute_norm_stats.py --config-name pi0_fast_libero_low_mem_finetune

XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run scripts/train.py \
  pi0_fast_libero_low_mem_finetune \
  --exp-name=libero_fast_lora
```

The LoRA config uses `paligemma_variant="gemma_2b_lora"` and `action_expert_variant="gemma_300m_lora"` with `ema_decay=None`.

## 5. Fine-Tune on Custom ALOHA Data

```bash
# Step 1: Convert your data to LeRobot format
uv run examples/aloha_real/convert_aloha_data_to_lerobot.py \
  --data_dir /path/to/your/aloha_data

# Step 2: Compute normalization stats
uv run scripts/compute_norm_stats.py --config-name pi0_aloha_pen_uncap

# Step 3: Train (20k steps default)
XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run scripts/train.py pi0_aloha_pen_uncap \
  --exp-name=my_aloha_task
```

See `examples/aloha_real/README.md` for full hardware setup.

## 6. Fine-Tune on Custom DROID Data (LeRobot Format)

```bash
# Step 1: Convert your DROID data to LeRobot format
uv run examples/droid/convert_droid_data_to_lerobot.py \
  --data_dir /path/to/your/droid_data

# Step 2: Compute normalization stats
uv run scripts/compute_norm_stats.py --config-name pi05_droid_finetune

# Step 3: Train
XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run scripts/train.py pi05_droid_finetune \
  --exp-name=my_droid_experiment --overwrite
```

Note: The `pi05_droid_finetune` config reuses the original DROID norm stats from `gs://openpi-assets/checkpoints/pi05_droid/assets`.

## 7. Large-Scale DROID Training (Full Dataset, RLDS)

Requires RLDS format DROID dataset (~1.8 TB) and 8x H100 GPUs (~2 days):

```bash
# Pi0-FAST on full DROID
XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run --group rlds scripts/train.py \
  pi0_fast_full_droid_finetune \
  --exp-name=droid_fast_full --overwrite

# Pi0.5 on full DROID
XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run --group rlds scripts/train.py \
  pi05_full_droid_finetune \
  --exp-name=droid_pi05_full --overwrite
```

Important: RLDS data loader requires `num_workers=0` (set in config); it handles multi-processing internally.

## 8. PyTorch Multi-GPU Training (DDP)

```bash
# Multi-GPU (8 GPUs, single node)
torchrun --standalone --nnodes=1 --nproc_per_node=8 scripts/train_pytorch.py \
  pi05_libero --exp-name=libero_pytorch

# Single GPU
python scripts/train_pytorch.py pi05_libero --exp-name=libero_pytorch_1gpu

# Multi-Node (e.g., 2 nodes x 8 GPUs)
torchrun \
  --nnodes=2 --nproc_per_node=8 --node_rank=0 \
  --master_addr=MASTER_IP --master_port=29500 \
  scripts/train_pytorch.py pi05_libero --exp-name=libero_multinode

# Resume from checkpoint
torchrun --nproc_per_node=8 scripts/train_pytorch.py pi05_libero \
  --exp-name=libero_pytorch --resume
```

PyTorch training saves checkpoints as `model.safetensors` + `optimizer.pt` + `metadata.pt`.

Note: PyTorch training does not support EMA. Set `pytorch_weight_path` in the config to load a converted PyTorch checkpoint as starting weights.

## 9. Convert JAX Checkpoint to PyTorch

```bash
# Convert pi0 DROID
python examples/convert_jax_model_to_pytorch.py \
  --checkpoint_dir gs://openpi-assets/checkpoints/pi0_droid \
  --output_path ./pi0_droid_pytorch \
  --config_name pi0_droid

# Convert pi0.5 DROID
python examples/convert_jax_model_to_pytorch.py \
  --checkpoint_dir gs://openpi-assets/checkpoints/pi05_droid \
  --output_path ./pi05_droid_pytorch \
  --config_name pi05_droid

# Inspect keys only (no conversion)
python examples/convert_jax_model_to_pytorch.py \
  --checkpoint_dir gs://openpi-assets/checkpoints/pi0_base \
  --inspect_only
```

Output is SafeTensors format. Assets (norm stats) are copied to the output directory.

## 10. Python API -- Direct Policy Inference (No Server)

```python
from openpi.training import config as _config
from openpi.policies import policy_config
from openpi.shared import download
import numpy as np

# Load config and download checkpoint
config = _config.get_config("pi05_droid")
ckpt_dir = download.maybe_download("gs://openpi-assets/checkpoints/pi05_droid")

# create_trained_policy auto-detects JAX vs PyTorch checkpoint
policy = policy_config.create_trained_policy(config, ckpt_dir)

# Run inference
result = policy.infer({
    "observation/exterior_image_1_left": np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8),
    "observation/wrist_image_left": np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8),
    "observation/joint_position": np.zeros(7, dtype=np.float32),
    "observation/gripper_position": np.zeros(1, dtype=np.float32),
    "prompt": "pick up the block",
})
actions = result["actions"]   # (horizon, action_dim) numpy array
timing = result["policy_timing"]  # {"infer_ms": float}
```

### With Custom Prompt Override

```python
policy = policy_config.create_trained_policy(
    config, ckpt_dir, default_prompt="grasp the blue object"
)
# The default prompt is injected if "prompt" key is absent from the observation
```

### With PyTorch Checkpoint

```python
# PyTorch checkpoint detected automatically (model.safetensors present)
policy = policy_config.create_trained_policy(
    config, "./pi05_droid_pytorch",
    pytorch_device="cuda:0"  # or "cpu"
)
```

## 11. Custom Dataset Fine-Tuning Workflow

For a new robot platform not covered by existing configs:

### Step 1: Create Data Transforms

Create a new policy file (e.g., `src/openpi/policies/my_robot_policy.py`):

```python
import dataclasses
import numpy as np
from openpi.models import model as _model
from openpi import transforms as _transforms

@dataclasses.dataclass(frozen=True)
class MyRobotInputs(_transforms.DataTransformFn):
    model_type: _model.ModelType = _model.ModelType.PI05

    def __call__(self, data):
        # Map your observation keys to the standard format
        state = np.concatenate([
            data["observation/joint_position"],   # (7,)
            data["observation/gripper_position"],  # (1,)
        ])
        return {
            "image": {
                "base_0_rgb": data["observation/image"],
                "left_wrist_0_rgb": data.get("observation/wrist_image",
                    np.zeros((224, 224, 3), dtype=np.uint8)),
            },
            "image_mask": {
                "base_0_rgb": True,
                "left_wrist_0_rgb": "observation/wrist_image" in data,
            },
            "state": state,
            "actions": data.get("actions", np.zeros(8)),
            "prompt": data.get("prompt", ""),
        }

@dataclasses.dataclass(frozen=True)
class MyRobotOutputs(_transforms.DataTransformFn):
    def __call__(self, data):
        actions = data["actions"]
        return {
            "actions": actions[..., :8],  # Extract your action dims
            "state": data["state"],
        }
```

### Step 2: Add Config

Add to `src/openpi/training/config.py` in the `_CONFIGS` list:

```python
TrainConfig(
    name="pi05_my_robot",
    model=pi0_config.Pi0Config(
        pi05=True,
        action_dim=32,      # Padded to 32 internally
        action_horizon=10,   # Number of future actions to predict
    ),
    data=SimpleDataConfig(
        repo_id="your_hf_username/my_robot_dataset",
        assets=AssetsConfig(
            assets_dir="gs://openpi-assets/checkpoints/pi05_base/assets",
            asset_id="my_robot",  # Will look for norm stats under this ID
        ),
        data_transforms=lambda model: _transforms.Group(
            inputs=[my_robot_policy.MyRobotInputs(model_type=model.model_type)],
            outputs=[my_robot_policy.MyRobotOutputs()],
        ),
        base_config=DataConfig(prompt_from_task=True),
    ),
    weight_loader=weight_loaders.CheckpointWeightLoader(
        "gs://openpi-assets/checkpoints/pi05_base/params"
    ),
    num_train_steps=30_000,
    batch_size=32,
)
```

### Step 3: Train

```bash
uv run scripts/compute_norm_stats.py --config-name pi05_my_robot
XLA_PYTHON_CLIENT_MEM_FRACTION=0.9 uv run scripts/train.py pi05_my_robot \
  --exp-name=v1
```

## 12. LIBERO Evaluation Script

After training, evaluate on the LIBERO benchmark:

```bash
# Terminal 1: Start policy server
uv run scripts/serve_policy.py policy:checkpoint \
  --policy.config=pi05_libero \
  --policy.dir=checkpoints/pi05_libero/libero_v1/29999

# Terminal 2: Run evaluation
uv run examples/libero/main.py \
  --host 0.0.0.0 --port 8000 \
  --task_suite_name libero_spatial \
  --num_trials_per_task 50
```

## Choosing a Model Variant

| Scenario | Recommended | Why |
|----------|-------------|-----|
| General manipulation, new platform | pi0.5 | Best generalization via knowledge insulation (adaRMSNorm) |
| Fast inference needed | pi0-FAST | Autoregressive is faster than flow matching; single forward pass |
| Dexterous tasks (folding, assembly) | pi0 or pi0.5 | Flow matching handles high-freq continuous actions well |
| Limited VRAM (<= 24 GB) | Any + LoRA | LoRA reduces ~70 GB to ~22.5 GB |
| Large-scale pre-training data | pi0.5 + full FT | Best data efficiency at scale |
| Dual-arm robot | pi0 or pi0.5 | Use 16-dim action space, `max_token_len=250` for FAST |
| Single-arm robot | Any | Use 7-8 dim actions, `max_token_len=180` for FAST |
