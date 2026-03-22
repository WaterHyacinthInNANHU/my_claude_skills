# iDP3 — Improved 3D Diffusion Policy

> Generalizable Humanoid Manipulation with 3D Diffusion Policies

| Field | Value |
|-------|-------|
| Authors | Yanjie Ze, Zixuan Chen, Wenhao Wang, Tianyi Chen, Xialin He, Ying Yuan, Xue Bin Peng, Jiajun Wu |
| Affiliations | Stanford, SFU, UPenn, UIUC, CMU |
| Venue | IROS 2025 |
| Paper | https://arxiv.org/abs/2410.10803 |
| Project | https://humanoid-manipulation.github.io/ |
| Code (learning) | https://github.com/YanjieZe/Improved-3D-Diffusion-Policy |
| Code (teleop) | https://github.com/YanjieZe/Humanoid-Teleoperation |
| Data & Weights | [Google Drive](https://drive.google.com/drive/folders/1f5Ln_d14OQ5eSjPDGnD7T4KQpacMhgCB?usp=sharing) |

## Problem & Contribution

Autonomous humanoid manipulation typically requires per-scene data and precise camera calibration. iDP3 is a **calibration-free, segmentation-free** 3D visuomotor policy that:

1. Uses **egocentric 3D point clouds** from a single depth camera (RealSense L515) — no extrinsic calibration or object segmentation needed
2. Learns from **noisy human teleoperation demos** collected in a single scene
3. **Generalizes** to novel objects, viewpoints, and unseen scenes
4. Validated with 2000+ real-world policy rollouts on a 25-DoF Fourier GR1 humanoid

## Method Overview

```
RealSense L515 ──► Raw Point Cloud (4096 pts) ──► MultiStagePointNet ──► 128-d features ─┐
                                                                                           ├──► ConditionalUnet1D ──► Actions [T, 25]
Robot Joints (32-d) ──────────────────────────► State MLP ──────────────► 64-d features ──┘
                                                                     (FiLM conditioning)
                                                                           ▲
                                                                    DDIM diffusion
                                                                    (50 train / 10 infer steps)
```

**Key improvements over DP3 (RSS 2024):**

| Aspect | DP3 | iDP3 |
|--------|-----|------|
| Camera | Requires calibration | Egocentric, no calibration |
| Segmentation | Needed | Not needed |
| Point encoder | Single-stage PointNet | Multi-stage PointNet (hierarchical) |
| Conditioning | Basic | FiLM conditioning at all U-Net levels |
| Target platform | Table-top arms | Full-sized humanoid (25 DoF) |

## Architecture Details

### MultiStagePointNetEncoder
- 4 Conv1d stages, each with global max-pool
- Multi-scale features concatenated before final projection
- Input: `[B, N, 3]` → Output: `[B, 128]`
- Config: `h_dim=128, out_channels=128, num_layers=4`

### ConditionalUnet1D (Diffusion Backbone)
- 1D U-Net over action trajectory dimension
- FiLM conditioning from encoder output at down/mid/up paths
- Down dims: `[256, 512, 1024]`, kernel size 5
- Timestep embedding: sinusoidal → MLP

### Diffusion Schedule
- Scheduler: DDIM (`diffusers.DDIMScheduler`)
- Train timesteps: 50, inference steps: 10
- Beta schedule: `squaredcos_cap_v2`
- Prediction type: `sample` (predicts clean trajectory)

## Paper-Code Mapping

| Paper Concept | Code Location |
|---------------|---------------|
| iDP3 policy | `diffusion_policy_3d.policy.diffusion_pointcloud_policy:DiffusionPointcloudPolicy` |
| 3D encoder (iDP3Encoder) | `diffusion_policy_3d.model.vision_3d.pointnet_extractor:iDP3Encoder` |
| Multi-stage PointNet | `diffusion_policy_3d.model.vision_3d.multi_stage_pointnet:MultiStagePointNetEncoder` |
| Conditional U-Net | `diffusion_policy_3d.model.diffusion.conditional_unet1d:ConditionalUnet1D` |
| Training workspace | `diffusion_policy_3d.workspace.idp3_workspace:iDP3Workspace` |
| Dataset (3D) | `diffusion_policy_3d.dataset.gr1_dex_dataset_3d:GR1DexDataset3D` |
| EMA model | `diffusion_policy_3d.model.diffusion.ema_model:EMAModel` |
| Normalizer | `diffusion_policy_3d.model.common.normalizer:LinearNormalizer` |
| Point sampling | `diffusion_policy_3d.model.vision_3d.point_process:uniform_sampling_torch` |
| RealSense wrapper | `diffusion_policy_3d.common.multi_realsense:MultiRealSense` |

## Key Hyperparameters

| Parameter | Value | Config Key |
|-----------|-------|------------|
| Horizon (trajectory length) | 16 | `horizon` |
| Observation steps | 2 | `n_obs_steps` |
| Action steps | 15 | `n_action_steps` |
| Num points | 4096 | `pointcloud_encoder_cfg.num_points` |
| Point encoder out dim | 128 | `pointcloud_encoder_cfg.out_channels` |
| State dim | 32 | `shape_meta.obs.agent_pos.shape` |
| Action dim | 25 | `shape_meta.action.shape` |
| Learning rate | 1e-4 | `optimizer.lr` |
| Weight decay | 1e-6 | `optimizer.weight_decay` |
| Epochs | 301 | `training.num_epochs` |
| LR warmup steps | 500 | `training.lr_warmup_steps` |
| Batch size | 256 | `dataloader.batch_size` |
| EMA | enabled | `training.use_ema` |
| Diffusion steps (train) | 50 | `noise_scheduler.num_train_timesteps` |
| Diffusion steps (infer) | 10 | `num_inference_steps` |

## Data Format

Zarr dataset with arrays:

| Array | Shape | Description |
|-------|-------|-------------|
| `state` | `[T, 32]` | Robot joint positions (14 arm + 12 hand + waist DOFs) |
| `action` | `[T, 25]` | Robot actions |
| `point_cloud` | `[T, N, 3]` or `[T, N, 6]` | XYZ or XYZ+RGB egocentric point cloud |

Normalization: actions are linearly normalized; point clouds and agent_pos use identity (no normalization).

## Input/Output Shapes

```python
# Observation dict
obs_dict = {
    'point_cloud': torch.Tensor,  # [B, n_obs_steps, 4096, 3]
    'agent_pos':   torch.Tensor,  # [B, n_obs_steps, 32]
}

# Action output
action = policy.predict_action(obs_dict)['action']  # [B, n_action_steps, 25]
```

## Dependencies

```
python==3.8
torch==2.1.0 (CUDA 12.1)
diffusers==0.11.1
hydra-core==1.2.0
einops==0.4.1
open3d
zarr==2.12.0
numba==0.56.4
wandb
```

Hardware: Training on RTX 4090 (24GB). Deployment on CPU (onboard compute).
Sensor: Intel RealSense L515 (LiDAR). **Do NOT use RealSense D435** — imprecise depth.

## Gotchas & Tips

- The repo uses Hydra for config. Override via CLI: `python train.py task.dataset.zarr_path=/path/to/data`
- Point clouds are **not normalized** — the encoder handles raw egocentric coordinates
- `n_action_steps = horizon - n_obs_steps + 1 = 16 - 2 + 1 = 15`
- Deployment uses **CPU inference** on the robot's onboard computer
- The `deploy.py` is specific to Fourier GR1 — adapt `env.step()` for your robot
- `communication.py` (robot comms) lives in the [Humanoid-Teleoperation repo](https://github.com/YanjieZe/Humanoid-Teleoperation/tree/main/humanoid_teleoperation/teleop-zenoh)
- Data collection uses Apple Vision Pro for whole-upper-body teleoperation
- Community extension: [PointVLA (arXiv 2503.07511)](https://arxiv.org/abs/2503.07511) uses the iDP3 encoder in a 3D VLA
