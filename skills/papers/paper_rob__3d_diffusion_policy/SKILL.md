# 3D Diffusion Policy (DP3)

Compact 3D visual representations + diffusion-based action generation for visuomotor policy learning with minimal demonstrations.

## When to Use

- Building visuomotor policies from point cloud observations
- Imitation learning with few demonstrations (as few as 10)
- Dexterous manipulation, deformable object manipulation
- When you need appearance/viewpoint invariant policies (3D > 2D)

## Quick Reference

| Field | Value |
|-------|-------|
| Paper | [arXiv 2403.03954](https://arxiv.org/abs/2403.03954) (Ze et al., 2024) |
| Repo | [github.com/YanjieZe/3D-Diffusion-Policy](https://github.com/YanjieZe/3D-Diffusion-Policy) |
| Project page | [3d-diffusion-policy.github.io](https://3d-diffusion-policy.github.io) |
| Framework | PyTorch, Hydra 1.2.0, HuggingFace diffusers 0.11.1 |
| Python | 3.8 |
| GPU mem | ~10 GB (tested on A40) |
| Training time | ~3h (dp3), ~1-2h (simple_dp3) |
| License | MIT |

## Architecture Overview

```
Depth Image --> Point Cloud (FPS downsample to 512-1024 pts)
                    |
              PointNet Encoder (3-layer MLP, max-pool) --> 64-dim visual feature
                    |
              + Agent State MLP (2-layer, 64-dim)
                    |
              Global Conditioning Vector
                    |
         Conditional UNet1D (DDIM, 100 train / 10 inference steps)
                    |
              Action Trajectory (horizon H)
```

**Key insight**: Use compact 3D point cloud representation (64-dim) instead of high-dim 2D image features. This gives:
- Viewpoint invariance
- Appearance generalization
- Efficient inference (comparable speed to 2D diffusion policy)

## Core Components

### DP3Encoder (`model/vision/pointnet_extractor.py`)
- `PointNetEncoderXYZ`: 3-ch input (XYZ only, no color for appearance invariance)
- Layers: `3 -> 64 -> 128 -> 256`, LayerNorm between layers
- Max-pool over points -> projection head `256 -> 64`
- Agent state: 2-layer MLP `(state_dim -> 64 -> 64)`

### Diffusion Backbone (`model/diffusion/conditional_unet1d.py`)
- `ConditionalUnet1D`: 1D UNet with FiLM conditioning at all levels
- Down dims: `[256, 512, 1024]`
- Sinusoidal timestep embedding
- DDIM scheduler (from HuggingFace diffusers)
- **Sample prediction** (not epsilon), better for high-dim actions

### Key Hyperparameters (default `dp3.yaml`)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `horizon` | 16 | prediction horizon |
| `n_obs_steps` | 2 | observation history |
| `n_action_steps` | 8 | executed action chunk |
| `batch_size` | 128 | |
| `lr` | 1e-4 | AdamW |
| `num_epochs` | 3000 | |
| `num_points` | 512 or 1024 | FPS-downsampled points |
| `use_ema` | True | EMA model for inference |
| `condition_type` | film | FiLM conditioning |
| Training diffusion steps | 100 | |
| Inference diffusion steps | 10 | DDIM |

## Config System

**Hydra 1.2.0** with OmegaConf. Two-level config:
- **Top-level**: `dp3.yaml` / `simple_dp3.yaml` (architecture, training)
- **Task-level**: `task/<task_name>.yaml` (data paths, env, shapes)

Key config files: `3D-Diffusion-Policy/diffusion_policy_3d/config/`

## Data Format

**Zarr archives** with per-episode arrays:

| Key | Shape | Description |
|-----|-------|-------------|
| `point_cloud` | `(T, N_pts, 3 or 6)` | XYZ [+ RGB] |
| `state` / `agent_pos` | `(T, state_dim)` | joint positions etc. |
| `action` | `(T, action_dim)` | control commands |
| `img` | `(T, H, W, 3)` | optional images |

For real robot: use `scripts/convert_real_robot_data.py` to convert to zarr.

## Repo Structure (Key Files)

```
3D-Diffusion-Policy/
├── 3D-Diffusion-Policy/
│   ├── train.py                    # training entry point
│   ├── eval.py                     # evaluation entry point
│   └── diffusion_policy_3d/
│       ├── config/                 # Hydra configs
│       │   ├── dp3.yaml            # main config
│       │   ├── simple_dp3.yaml     # fast variant
│       │   └── task/               # 57 task configs
│       ├── policy/dp3.py           # DP3 policy class
│       ├── model/
│       │   ├── diffusion/conditional_unet1d.py
│       │   └── vision/pointnet_extractor.py
│       ├── dataset/                # per-env dataset classes
│       └── env_runner/             # per-env evaluation runners
├── scripts/                        # train/eval/demo-gen shell scripts
├── third_party/                    # pinned deps (gym, mujoco-py, etc.)
└── visualizer/                     # point cloud visualization
```

## Supported Environments (57 tasks)

| Environment | Tasks | Action Dim | Notes |
|-------------|-------|------------|-------|
| Adroit | door, hammer, pen | 26-28 | MuJoCo, dexterous hand |
| DexArt | bucket, faucet, laptop, toilet | varies | SAPIEN, articulated objects |
| MetaWorld | 50 tasks (easy/med/hard/vhard) | varies | MuJoCo, tabletop |
| RealDex | drill, dumpling, pour, roll | 7 | Real robot (Allegro + Franka) |

## Key Results

- **55.3% relative improvement** over 2D Diffusion Policy across 72 sim tasks with only 10 demos
- **85% success rate** in real-world tasks (40 demos)
- Inference speed comparable to 2D Diffusion Policy despite 3D processing
- Zero safety violations in real-world deployment

## Gotchas & Tips

1. **Must use bundled Gym 0.21.0** from `third_party/` -- other versions break
2. **Point cloud cropping is critical** for real-world: crop out table/background, keep only task-relevant points
3. **Camera quality matters**: RealSense D435 fails, use L515 or equivalent high-quality depth sensor
4. **Demo quality >> quantity**: Re-generate bad demos rather than adding more
5. **Try larger horizons** (16/32) and global position actions for your task
6. **simple_dp3 is ~2x faster** (25 FPS) but dp3 has better performance
7. **WandB required**: `wandb login` before training; metrics logged there (not eval script)
8. **setuptools pinning**: Use `setuptools==59.5.0` to avoid distutils errors
9. **pytorch3d**: Use `third_party/pytorch3d_simplified`, not official pytorch3d
10. **huggingface_hub**: Pin to `0.25.2` if `cached_download` import fails
