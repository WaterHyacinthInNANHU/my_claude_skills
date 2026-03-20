# Any3D-VLA -- Enhancing VLA Robustness via Diverse Point Clouds

| Field | Value |
|-------|-------|
| Paper | [Any3D-VLA: Enhancing VLA Robustness via Diverse Point Clouds](https://arxiv.org/abs/2602.00807) |
| Authors | Xianzhe Fan, Shengliang Deng, Xiaoyang Wu, Yuxiang Lu, Zhuoling Li, Mi Yan, Yujia Zhang, Zhizheng Zhang, He Wang, Hengshuang Zhao |
| Year/Venue | 2026, arXiv |
| Repo | [XianzheFan/Any3D-VLA](https://github.com/XianzheFan/Any3D-VLA) |
| Weights | [HuggingFace: XianzheFan/Any3D-VLA](https://huggingface.co/XianzheFan/Any3D-VLA) |
| Real-world controller | [XianzheFan/Any3D-VLA-real-world-controller](https://github.com/XianzheFan/Any3D-VLA-real-world-controller) |
| License | See repo |

## Problem & Contribution

VLA models using only 2D images have limited spatial understanding. Any3D-VLA incorporates 3D point clouds to enhance robustness by:

1. **Unifying diverse point cloud sources** -- simulator-generated, real sensor, and model-estimated (monocular depth) point clouds in one training pipeline
2. **Domain-agnostic 3D feature learning** -- gated residual fusion of Concerto (3D encoder) features with DINOv2+SigLIP (2D) features to mitigate depth-scale and cross-environment domain gaps
3. **CoT + flow matching** -- chain-of-thought autoregressive generation (bbox/goal tokens) followed by flow-matching-based action generation

## Architecture Overview

```
                        Language Instruction
                              |
                              v
Input Images (front+wrist) --> DINOv2 + SigLIP ViT --> 2D features (L patches, dim=2304)
                                                              |
Depth Maps --> Monocular Depth Estimator --> Point Cloud      |
   (or simulator/sensor point cloud)        |                 |
                                            v                 |
                                    Concerto (3D encoder)     |
                                    (PTv3-based, dim=1728)    |
                                            |                 |
                                            v                 v
                                    Gated Residual Fusion ---------> Fused Features (dim=2304)
                                                                         |
                                                                         v
                                                               FusedMLPProjector --> LLM dim
                                                                         |
                                                                         v
                                                               InternLM2 1.8B (LLM backbone)
                                                                    |          |
                                                                    v          v
                                                          CoT tokens     Action Expert (smaller LLM)
                                                         (bbox, goal)        |
                                                                             v
                                                                    Flow Matching Module
                                                                             |
                                                                             v
                                                                    Action (7-DoF x chunk_len)
```

## Key Components

### 1. 2D Backbone: DINOv2 + SigLIP (`ConcertoDinoSigLIPViTMonoBackbone`)

| Detail | Value |
|--------|-------|
| File | `vla_network/model/backbone_2d/dinosiglip_vit_simulated_concerto_mono.py` |
| Class | `ConcertoDinoSigLIPViTMonoBackbone` |
| DINOv2 model | `vit_large_patch14_reg4_dinov2.lvd142m` (timm) |
| SigLIP model | `vit_so400m_patch14_siglip_224` (timm) |
| Image size | 224x224 |
| Feature dim | 2304 (DINOv2 1024 + SigLIP 1152, after removing CLS, concat) |
| Frozen | Yes (by default) |

### 2. 3D Backbone: Concerto (`PCEncoder32`)

| Detail | Value |
|--------|-------|
| File | `vla_network/model/backbone_2d/dinosiglip_vit_simulated_concerto_mono.py` |
| Model | `concerto.load("concerto_large", repo_id="Pointcept/Concerto")` |
| Feature dim | 1728 (after pooling hierarchy unroll) |
| Partial unfreeze | Last 4 spconv layers trainable |
| Point format | coord(3) + color(3) + normal(3) + grid(3) + cam_id(1) + patch_idx(1) + batch(1) = 15 dims |
| Grid size | 0.01 |
| Input struct | `concerto.structure.Point` dict with keys: coord, color, normal, feat, grid_coord, batch |

### 3. Gated Residual Fusion

```python
# Learnable gate initialized at sigmoid(-2.1972) ~ 0.1
fuse_gate = nn.Parameter(torch.full((1,), -2.1972))
# Fusion: image_feat + sigmoid(gate) * LayerNorm(MLP(cat(pc_feat, image_feat)))
fused = image_feats + sigmoid(fuse_gate) * fuse_ln(fuse_mlp(cat(pc_feats, image_feats)))
```

When no point cloud is available, `empty_pc_token` (learned parameter) is used as fallback.

### 4. Projector (`FusedMLPProjector`)

| Detail | Value |
|--------|-------|
| File | `vla_network/model/vla/projector.py` |
| Architecture | Linear(2304, 9216) -> GELU -> Linear(9216, llm_dim) -> GELU -> Linear(llm_dim, llm_dim) |

### 5. LLM Backbone (`LLMBackbone`)

| Detail | Value |
|--------|-------|
| File | `vla_network/model/backbone_llm/__init__.py` |
| Default model | InternLM2 1.8B (`internlm/internlm2-1_8b`) |
| Also supports | LLaMA-2-7B, Qwen2-1.5B |
| Attention | `flex_attention` (for action expert block-attention) |
| Dtype | bfloat16 |

### 6. Action Expert

A smaller LLM (same architecture, scaled down hidden/intermediate sizes) that processes action tokens with cross-attention (via KV cache) to the main LLM's prefix output.

| Detail | Value |
|--------|-------|
| File | `vla_network/model/vla/__init__.py:109` (`create_action_expert_from_llm`) |
| Config | `hidden_size_scale`, `intermediate_size_scale` (divisors of LLM dims) |
| Attention | `flex_attention` (enforced) |

### 7. Flow Matching Module (`VLAFlowMatchingModule`)

| Detail | Value |
|--------|-------|
| File | `vla_network/model/vla/flow_matching.py` |
| Class | `VLAFlowMatchingModule` |
| Time sampling | Beta distribution with params `beta_alpha`, `beta_beta`, scaled to `[time_min, time_max]` |
| Action embedding | `Linear(action_dim, llm_dim)` + time MLP: `Linear(2*llm_dim, llm_dim) -> SiLU -> Linear(llm_dim, llm_dim)` |
| Proprio embedding | `Linear(proprio_dim, llm_dim)` |
| Output projection | `Linear(llm_dim, action_dim)` |
| Denoising | Euler integration, default 10 steps at inference |
| Flow | `x_t = t * noise + (1-t) * x_1`; velocity `u_t = noise - x_1` |

### 8. Prediction Modes

| Mode | Description |
|------|-------------|
| `flow_matching` | Pure flow matching action generation |
| `cot_flow_matching` | **Default**: autoregressive CoT (bbox + goal tokens) then flow matching for actions |
| `cot_bbox_flow_matching` | CoT with bbox only, then flow matching |
| `cotrain_flow_matching` | Co-training variant |
| `token_pred` | Pure autoregressive token prediction for actions |

### 9. Point Cloud Preprocessing (in `DataPreprocessor`)

| Detail | Value |
|--------|-------|
| File | `vla_network/dataset/preprocess.py` |
| Depth estimation | DepthAnything3 (`depth_anything_3.api.DepthAnything3`) or MapAnything |
| PC from depth | Lifts depth map to point cloud using camera intrinsics |
| Concerto transform | GridSample(0.01) -> NormalizeColor -> ToTensor |
| Each point gets | xyz, rgb, normal, grid_coord, cam_id, patch_idx (which ViT patch), batch_idx |

## Paper-Code Mapping

| Paper Concept | Code Location |
|---------------|---------------|
| 2D+3D backbone fusion | `backbone_2d/dinosiglip_vit_simulated_concerto_mono.py:ConcertoDinoSigLIPViTMonoBackbone.forward()` |
| Concerto 3D encoder | `concerto` package, loaded via `concerto.load("concerto_large")` |
| Gated residual fusion | `dinosiglip_vit_simulated_concerto_mono.py:141-148` (fuse_ln, fuse_mlp, fuse_gate) |
| Domain-agnostic 3D learning | Diverse PC sources (sim/sensor/model-estimated) + partial Concerto fine-tuning (last 4 spconv layers) |
| CoT generation | `vla/__init__.py:VLA.generate()` -> `generate_autoregressive()` for CoT tokens |
| Flow matching action gen | `vla/__init__.py:VLA.generate_flow_matching()` using `VLAFlowMatchingModule` |
| Action expert | `vla/__init__.py:VLA.create_action_expert_from_llm()` -- smaller LLM with KV cache from main LLM |
| Action tokenizer | `dataset/tokenizer.py:RatioMinMaxUniformRobotTokenizer` (normalize then uniform discretize) |
| Inference server | `scripts/serve.py` -- ZMQ-based server, `VLAAgent` wraps full pipeline |

## Key Hyperparameters

| Parameter | Default/Typical | Source |
|-----------|----------------|--------|
| Image size | 224 | backbone config |
| Action dim | 7 (xyz, rpy, gripper) | data config |
| Proprio dim | 7 or 13 (depends on `robot_rep`) | data config |
| Action chunk length | set in model config | `VLAModelConfig.action_len` |
| Flow matching iterations (inference) | 10 | `VLA.generate(flow_matching_iter=10)` |
| Grid size (Concerto) | 0.01 | preprocessing |
| LLM | InternLM2 1.8B | `VLAModelConfig.llm.name` |
| Attention | flex_attention | `LLMConfig.attn_implementation` |
| Training | DeepSpeed, bf16 | `BasicTrainConfig` |

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.12 | Runtime |
| CUDA | 11.8 | GPU |
| PyTorch | 2.5.1 | Framework |
| timm | 1.0.15 | DINOv2/SigLIP ViT models |
| transformers | 4.47.0 | LLM backbone |
| flash-attn | 2.7.0 | Efficient attention |
| concerto | (Pointcept) | 3D point cloud encoder |
| depth_anything_3 | (bundled) | Monocular depth estimation |
| torch_scatter | - | Scatter operations for PC->patch aggregation |
| spconv | - | Sparse convolution (Concerto dependency) |
| accelerate | 1.5.1 | Training |
| deepspeed | 0.16.4 | Distributed training |
| wandb | 0.19.8 | Logging |
| zmq (pyzmq) | 26.3.0 | Inference server communication |

## Installation

```bash
conda create -n any3dvla_env python=3.12 -y
conda activate any3dvla_env

pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cu118

# Install core package
pip install -e src/vla_network

# Install Concerto (3D encoder)
git clone https://github.com/Pointcept/Concerto.git
cd Concerto && pip install -e . && cd ..
```

## Inference

### Server mode (ZMQ)

```bash
# Download checkpoint from HuggingFace: XianzheFan/Any3D-VLA
# Expected path: storage/ckpt/exp/grit-Concerto-mono-dinosiglip-16-128-40000/checkpoint-340000/model.safetensors

bash serve_mono.sh          # default port 6666
bash serve_mono.sh --compile  # ~50% faster inference, ~3min warmup
```

### Python API

```python
from vla_network.model.vla import VLAAgent
import numpy as np

# Load model
agent = VLAAgent(path="path/to/model.safetensors", compile=False)
agent.preprocessor.config.robot_rep = "identity"

# Prepare input
sample = {
    'text': 'pick up elephant',
    'image_array': [np.zeros((256, 256, 3), dtype=np.uint8)],      # front camera
    'image_wrist_array': [np.zeros((256, 256, 3), dtype=np.uint8)], # wrist camera
    'depth_array': [np.zeros((256, 256, 1), dtype=np.float32)],
    'depth_wrist_array': [np.zeros((256, 256, 1), dtype=np.float32)],
    'proprio_array': [np.zeros((7,), dtype=np.float32)] * 4,       # 4 history steps
    'traj_metadata': None,
    'env_id': 1,
}

# Get action
results = agent([sample])
# results[0]['action']: np.ndarray of shape (action_len * dt_steps, 7)
#   columns: [dx, dy, dz, droll, dpitch, dyaw, gripper]
# results[0].get('goal'): (xyz, rpy) tuple if CoT mode
# results[0].get('bbox'): bounding boxes if CoT mode
```

### Supported instructions

- `pick up {object}`
- `pick up {color} {object}`
- `stack {color} bowl onto {color} bowl`
- `stack {color} cube onto {color} cube`
- `move {object} to {container}`
- `move {object} to {color} {container}`

## Gotchas & Tips

- **flex_attention required** for action expert -- the code enforces this; if your LLM doesn't support it, you must use a non-action-expert config
- **Concerto runs in float32** -- wrapped in `PCEncoder32` to prevent dtype casting issues with mixed precision training
- **Point cloud preprocessing is heavy** -- the `DataPreprocessor` runs monocular depth estimation (DepthAnything3) at inference time if real depth is not available
- **serve_mono.sh sets `HF_ENDPOINT` to hf-mirror.com** -- change this for non-China networks
- **`gx_utils`** -- the code depends on a private `gx_utils` package for logging, file management, robot configs, and data types; this is bundled with the checkpoint/config but not in the public repo
- **Action interpolation** -- at inference, predicted delta actions are interpolated by `dt_steps` using axis-angle decomposition (`transforms3d`)
- **Gripper discretization** -- predicted gripper values are discretized to {-1, 0, 1} at inference
