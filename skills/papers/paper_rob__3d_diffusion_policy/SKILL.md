---
name: paper_rob__3d_diffusion_policy
description: 3D Diffusion Policy (DP3) -- visuomotor imitation learning via sparse point cloud representations and diffusion-based action generation
---

# paper_rob__3d_diffusion_policy

3D Diffusion Policy (DP3) combines compact 3D visual representations from sparse point clouds with diffusion-based action generation for robotic imitation learning. It achieves 24.2% improvement over baselines across 72 simulation tasks with only 10 demonstrations, and 85% success on real robot tasks.

## Paper Info

| Field | Value |
|-------|-------|
| Title | 3D Diffusion Policy: Generalizable Visuomotor Policy Learning via Simple 3D Representations |
| Authors | Yanjie Ze et al. |
| Year | 2024 |
| Venue | RSS 2024 |
| Paper | https://arxiv.org/abs/2403.03954 |
| Code | https://github.com/YanjieZe/3D-Diffusion-Policy |
| Data | https://drive.google.com/file/d/1G5MP6Nzykku9sDDdzy7tlRqMBnKb253O (real robot data) |

## Method Overview

1. **Point cloud observation**: Sparse point clouds (512 or 1024 points) are extracted from depth cameras. Only XYZ coordinates are used by default (no color), providing appearance invariance.
2. **DP3Encoder**: A PointNet-based encoder processes the point cloud via a 3-layer MLP [64, 128, 256] with max-pooling and projection to a compact 64-dim feature. A separate 2-layer MLP encodes the robot's proprioceptive state (agent_pos) into 64 dims. These are concatenated into a 128-dim observation feature.
3. **Conditional UNet1D diffusion**: The observation feature (flattened across n_obs_steps to 256-dim) conditions a 1D UNet via FiLM modulation to iteratively denoise a random trajectory into an action chunk. DDIM scheduler with 100 training / 10 inference steps, predicting the clean sample directly.
4. **Action chunking**: The model predicts a horizon of 16 actions but executes only 8 (n_action_steps), starting from timestep offset `n_obs_steps - 1 = 1`.

Key insight: A simple PointNet encoder producing a compact 64-dim 3D feature is sufficient for diffusion policy conditioning -- no need for complex 3D backbones, NeRFs, or dense representations.

## Paper-Code Mapping

| Paper Concept | Code Location | Notes |
|---------------|---------------|-------|
| DP3 policy (Sec 3) | `diffusion_policy_3d/policy/dp3.py:DP3` | Main policy: `predict_action()`, `compute_loss()`, `conditional_sample()` |
| Simple DP3 variant | `diffusion_policy_3d/policy/simple_dp3.py:SimpleDP3` | Lighter UNet (1 resblock/level, 1 mid block), 25 FPS inference |
| DP3Encoder (Sec 3.1) | `diffusion_policy_3d/model/vision/pointnet_extractor.py:DP3Encoder` | Wraps PointNet + state MLP, output_shape() returns 128 (64+64) |
| PointNet encoder (XYZ) | `pointnet_extractor.py:PointNetEncoderXYZ` | MLP [3->64->128->256], LayerNorm, max-pool, Linear(256->64)+LayerNorm |
| PointNet encoder (XYZRGB) | `pointnet_extractor.py:PointNetEncoderXYZRGB` | MLP [6->64->128->256->512], max-pool, Linear(512->64)+LayerNorm |
| Conditional UNet1D (Sec 3.2) | `diffusion_policy_3d/model/diffusion/conditional_unet1d.py:ConditionalUnet1D` | FiLM-conditioned 1D UNet, 2 resblocks/level, 2 mid blocks |
| Simple UNet1D | `diffusion_policy_3d/model/diffusion/simple_conditional_unet1d.py:ConditionalUnet1D` | 1 resblock/level, 1 mid block |
| FiLM conditioning (Eq 4) | `conditional_unet1d.py:ConditionalResidualBlock1D` | `condition_type='film'`: scale/bias modulation; also supports add, cross_attention_add/film, mlp_film |
| DDIM noise schedule | `dp3.yaml:noise_scheduler` | `DDIMScheduler`, 100 train / 10 inference steps, `prediction_type: sample` |
| Diffusion timestep embed | `diffusion_policy_3d/model/diffusion/positional_embedding.py:SinusoidalPosEmb` | Sinusoidal -> Linear(d, 4d) -> Mish -> Linear(4d, d) |
| Normalizer | `diffusion_policy_3d/model/common/normalizer.py:LinearNormalizer` | Per-field linear normalization fitted from dataset |
| EMA model | `diffusion_policy_3d/model/diffusion/ema_model.py:EMAModel` | Exponential moving average for stable eval |
| Action masking | `diffusion_policy_3d/model/diffusion/mask_generator.py:LowdimMaskGenerator` | Inpainting mask: actions invisible, obs visible (when not global_cond) |
| Zarr dataset | `diffusion_policy_3d/dataset/adroit_dataset.py:AdroitDataset` | Loads `.zarr`, returns `{obs: {point_cloud, agent_pos}, action}` |
| Training workspace | `train.py:TrainDP3Workspace` | Hydra-based: model init, training loop, WandB, checkpointing |

## Setup

### Dependencies

- Python 3.8
- PyTorch (CUDA 11.7+ or 12.1+)
- Hydra 1.2.0
- Key packages: `diffusers==0.11.1`, `zarr==2.12.0`, `einops==0.4.1`, `dill==0.3.5.1`, `numba==0.56.4`, `wandb`, `pytorch3d` (simplified version in repo)
- Simulation: `gym==0.21.0` (pinned, from `third_party/`), `mujoco-py==2.1.2.14` (from `third_party/`), MuJoCo 2.1.0

### Installation

```bash
git clone https://github.com/YanjieZe/3D-Diffusion-Policy.git
cd 3D-Diffusion-Policy

# 1. Create conda env
conda create -n dp3 python=3.8 && conda activate dp3

# 2. Install PyTorch (match your CUDA)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. Install DP3 package
cd 3D-Diffusion-Policy && pip install -e . && cd ..

# 4. Install MuJoCo 2.1.0
mkdir -p ~/.mujoco && cd ~/.mujoco
wget https://github.com/deepmind/mujoco/releases/download/2.1.0/mujoco210-linux-x86_64.tar.gz -O mujoco210.tar.gz
tar -xvzf mujoco210.tar.gz
# Add to ~/.bashrc:
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${HOME}/.mujoco/mujoco210/bin:/usr/lib/nvidia:/usr/local/cuda/lib64
# export MUJOCO_GL=egl

# 5. Install third-party deps (order matters)
pip install setuptools==59.5.0 Cython==0.29.35 patchelf==0.17.2.0
cd third_party
cd mujoco-py-2.1.2.14 && pip install -e . && cd ..
cd gym-0.21.0 && pip install -e . && cd ..
cd dexart-release && pip install -e . && cd ..
cd Metaworld && pip install -e . && cd ..
cd rrl-dependencies && pip install -e mj_envs/. && pip install -e mjrl/. && cd ..
cd pytorch3d_simplified && pip install -e . && cd ../..

# 6. Install remaining packages
pip install zarr==2.12.0 wandb ipdb gpustat dm_control omegaconf hydra-core==1.2.0 \
    dill==0.3.5.1 einops==0.4.1 diffusers==0.11.1 numba==0.56.4 moviepy imageio av \
    matplotlib termcolor
```

### External Assets

- **Adroit RL experts**: Download from [OneDrive](https://1drv.ms/u/s!Ag5QsBIFtRnTlFWqYWtS2wMMPKNX) or [Google Drive](https://drive.google.com/file/d/1iNkSrLD_N4NrezLx58L1YoBBqYYg-33u) -> unzip `ckpts/` into `third_party/VRL3/`
- **DexArt assets**: Download from [Google Drive](https://drive.google.com/file/d/1DxRfB4087PeM3Aejd6cR-RQVgOKdNrL4) -> unzip `assets/` into `third_party/dexart-release/`
- **Real robot data**: Download from [Google Drive](https://drive.google.com/file/d/1G5MP6Nzykku9sDDdzy7tlRqMBnKb253O) -> place zarr files into `3D-Diffusion-Policy/data/`

## Usage Scenarios

### Generate Demonstrations

```bash
# Adroit (door, hammer, pen) -- 10 episodes via VRL3 expert
bash scripts/gen_demonstration_adroit.sh hammer

# DexArt (laptop, faucet, bucket, toilet) -- 100 episodes via RL checkpoint
bash scripts/gen_demonstration_dexart.sh laptop

# MetaWorld (50 tasks) -- 10 episodes via built-in expert
bash scripts/gen_demonstration_metaworld.sh basketball
```

Data saved to `3D-Diffusion-Policy/data/<env>_<task>_expert.zarr`.

### Train a Policy

```bash
# Usage: bash scripts/train_policy.sh <alg> <task> <tag> <seed> <gpu_id>
bash scripts/train_policy.sh dp3 adroit_hammer 0322 0 0
bash scripts/train_policy.sh simple_dp3 adroit_hammer 0322 0 0
bash scripts/train_policy.sh dp3 metaworld_basketball 0602 0 0
bash scripts/train_policy.sh dp3 realdex_drill 0112 0 0
```

Internally runs: `cd 3D-Diffusion-Policy && python train.py --config-name=dp3.yaml task=adroit_hammer ...`

### Evaluate a Saved Policy

```bash
# Same args as training
bash scripts/eval_policy.sh dp3 adroit_hammer 0322 0 0
```

Loads `latest.ckpt` from the output directory and runs rollouts. For benchmarking use WandB metrics from training, not this script.

### Key Config Flags

| Flag / Override | Default | Description |
|------|---------|-------------|
| `horizon` | 16 | Total prediction horizon (action chunk length) |
| `n_obs_steps` | 2 | Number of observation steps fed to encoder |
| `n_action_steps` | 8 | Number of actions executed per inference call |
| `policy.encoder_output_dim` | 64 | PointNet output dimensionality |
| `policy.down_dims` | [512,1024,2048] (dp3) / [128,256,384] (simple) | UNet channel widths per level |
| `policy.diffusion_step_embed_dim` | 128 | Diffusion timestep embedding dim |
| `policy.num_inference_steps` | 10 | DDIM denoising steps at inference |
| `policy.condition_type` | `film` | Options: film, add, cross_attention_add, cross_attention_film, mlp_film |
| `policy.use_pc_color` | false | Use XYZRGB (6-ch) vs XYZ (3-ch) point clouds |
| `training.num_epochs` | 3000 | Training epochs |
| `training.use_ema` | true | Use EMA model for evaluation |
| `training.lr_scheduler` | cosine | LR schedule with 500-step warmup |
| `training.rollout_every` | 200 | Epochs between evaluation rollouts |
| `dataloader.batch_size` | 128 | Batch size |
| `optimizer.lr` | 1e-4 | AdamW learning rate |
| `checkpoint.save_ckpt` | false | Set true to persist checkpoints |

## Code Integration Guide

### Minimal Imports

```python
import sys
sys.path.append("/path/to/3D-Diffusion-Policy/3D-Diffusion-Policy")

from diffusion_policy_3d.policy.dp3 import DP3
from diffusion_policy_3d.model.vision.pointnet_extractor import DP3Encoder, PointNetEncoderXYZ
from diffusion_policy_3d.model.diffusion.conditional_unet1d import ConditionalUnet1D
from diffusion_policy_3d.model.common.normalizer import LinearNormalizer
```

### Model Instantiation & Inference

```python
import torch
import dill
from omegaconf import OmegaConf
from diffusers.schedulers.scheduling_ddim import DDIMScheduler

# Define shape metadata (must match your task)
shape_meta = {
    'obs': {
        'point_cloud': {'shape': [512, 3], 'type': 'point_cloud'},
        'agent_pos': {'shape': [24], 'type': 'low_dim'},
    },
    'action': {'shape': [26]}
}

noise_scheduler = DDIMScheduler(
    num_train_timesteps=100,
    beta_start=0.0001, beta_end=0.02,
    beta_schedule='squaredcos_cap_v2',
    clip_sample=True, set_alpha_to_one=True,
    prediction_type='sample'
)

pc_cfg = OmegaConf.create({
    'in_channels': 3,
    'out_channels': 64,
    'use_layernorm': True,
    'final_norm': 'layernorm',
    'normal_channel': False,
})

policy = DP3(
    shape_meta=shape_meta,
    noise_scheduler=noise_scheduler,
    horizon=16,
    n_action_steps=8,
    n_obs_steps=2,
    num_inference_steps=10,
    obs_as_global_cond=True,
    diffusion_step_embed_dim=128,
    down_dims=[512, 1024, 2048],
    kernel_size=5,
    n_groups=8,
    condition_type='film',
    encoder_output_dim=64,
    use_pc_color=False,
    pointnet_type='pointnet',
    pointcloud_encoder_cfg=pc_cfg,
)

# Load checkpoint (dill required)
ckpt = torch.load("path/to/latest.ckpt", pickle_module=dill, map_location='cpu')
policy.load_state_dict(ckpt['state_dicts']['model'])
# Also load EMA model if available:
# ema_policy.load_state_dict(ckpt['state_dicts']['ema_model'])
policy.eval().cuda()

# Inference -- obs_dict values must have shape (B, T=n_obs_steps, ...)
obs_dict = {
    'point_cloud': torch.randn(1, 2, 512, 3).cuda(),  # (B, T, N_pts, 3)
    'agent_pos': torch.randn(1, 2, 24).cuda(),         # (B, T, D_state)
}
result = policy.predict_action(obs_dict)
action = result['action']           # (B, n_action_steps, D_action) = (1, 8, 26)
action_pred = result['action_pred'] # (B, horizon, D_action) = (1, 16, 26)
```

### Data Format

| Field | Shape / Type | Description |
|-------|-------------|-------------|
| `obs.point_cloud` | `(B, T, N_pts, 3)` float32 | XYZ point cloud; N_pts=512 (sim) or 1024 (real) |
| `obs.agent_pos` | `(B, T, D_state)` float32 | Robot proprioceptive state |
| `obs.imagin_robot` | `(B, T, N_imag, 3)` float32 | Optional imagined robot points (concatenated with point_cloud in encoder) |
| `action` | `(B, T, D_action)` float32 | Action trajectory |

#### Zarr Archive Structure

```
data/<task>.zarr/
  data/
    state       (N_total, D_state)   float32  -- robot state (mapped to obs.agent_pos)
    action      (N_total, D_action)  float32  -- actions
    point_cloud (N_total, N_pts, 3+) float64  -- point clouds
    img         (N_total, H, W, 3)   uint8    -- images (optional)
  meta/
    episode_ends (N_episodes,)       int64    -- cumulative step indices marking episode boundaries
```

### Integration Notes

- The repo uses a nested directory layout: the outer `3D-Diffusion-Policy/` is the repo root, the inner `3D-Diffusion-Policy/` is the Python package. `train.py` and `eval.py` live in the inner directory. Scripts run from the outer root; the entry points do `sys.path.append(ROOT_DIR)` where ROOT_DIR is the outer directory.
- Hydra config resolution requires `OmegaConf.register_new_resolver("eval", eval, replace=True)` for expressions like `${eval:'${n_obs_steps}-1'}`.
- `DP3Encoder.forward()` expects a dict with keys `point_cloud` (required) and `agent_pos` (required). If `imagin_robot` key exists in `observation_space`, those points are concatenated with `point_cloud` before encoding.
- Point clouds are NOT normalized by the PointNet encoder. Normalization happens via `LinearNormalizer` set on the policy via `policy.set_normalizer()`. The normalizer is fitted from the dataset and saved inside the checkpoint.
- Checkpoints are saved via `dill` (not plain pickle). Loading requires `pickle_module=dill` in `torch.load()`.
- The `DP3` constructor accepts `**kwargs` which are forwarded to `noise_scheduler.step()` during inference.

## Core Architecture

```
                         Point Cloud (B, N, 3)
                               |
                    PointNetEncoderXYZ
                    [Linear 3->64, LN, ReLU]
                    [Linear 64->128, LN, ReLU]
                    [Linear 128->256, LN, ReLU]
                    [max-pool over N points]
                    [Linear 256->64, LN]
                               |
                         pn_feat (B, 64)
                               |
    Agent State (B, D) --> StateMLP [D->64, ReLU, 64->64] --> state_feat (B, 64)
                               |                                    |
                               +-------------concat-----------------+
                               |
                    obs_feature (B, 128)   <-- computed per obs step
                               |
                    [flatten n_obs_steps=2 -> 256]
                               |
                         global_cond (B, 256)
                               |
                    +----------+----------+
                    |                     |
             timestep_embed          global_cond
             SinusoidalPosEmb(128)        |
             -> MLP -> 128-dim            |
                    |                     |
                    +------concat---------+
                    |
              cond_feature (B, 128+256=384)
                    |
              ConditionalUnet1D (dp3 variant)
              [Down: action_dim->512->1024->2048, 2 ResBlocks/level, FiLM]
              [Mid: 2x ResBlock at 2048]
              [Up: 2048->1024->512, skip connections, 2 ResBlocks/level]
              [Final: Conv1dBlock + Conv1d -> action_dim]
                    |
              denoised actions (B, horizon=16, D_action)
                    |
              take steps [1:9] -> executed actions (B, 8, D_action)
```

## Repo Structure

| Path | Purpose |
|------|---------|
| `3D-Diffusion-Policy/train.py` | Training entry with `TrainDP3Workspace` (model init, training loop, checkpointing) |
| `3D-Diffusion-Policy/eval.py` | Evaluation entry (loads latest.ckpt, runs env rollouts) |
| `diffusion_policy_3d/policy/dp3.py` | `DP3` policy class: encoder + UNet diffusion + action chunking |
| `diffusion_policy_3d/policy/simple_dp3.py` | `SimpleDP3`: same API, uses lighter simple UNet |
| `diffusion_policy_3d/policy/base_policy.py` | `BasePolicy` base class (extends `ModuleAttrMixin`) |
| `diffusion_policy_3d/model/vision/pointnet_extractor.py` | `DP3Encoder`, `PointNetEncoderXYZ`, `PointNetEncoderXYZRGB` |
| `diffusion_policy_3d/model/diffusion/conditional_unet1d.py` | `ConditionalUnet1D` (full), `ConditionalResidualBlock1D`, `CrossAttention` |
| `diffusion_policy_3d/model/diffusion/simple_conditional_unet1d.py` | `ConditionalUnet1D` (simple: 1 resblock/level) |
| `diffusion_policy_3d/model/diffusion/conv1d_components.py` | `Conv1dBlock`, `Downsample1d`, `Upsample1d` |
| `diffusion_policy_3d/model/diffusion/positional_embedding.py` | `SinusoidalPosEmb` |
| `diffusion_policy_3d/model/diffusion/ema_model.py` | `EMAModel` for exponential moving average |
| `diffusion_policy_3d/model/diffusion/mask_generator.py` | `LowdimMaskGenerator` for inpainting-style action masking |
| `diffusion_policy_3d/model/common/normalizer.py` | `LinearNormalizer`, `SingleFieldLinearNormalizer` |
| `diffusion_policy_3d/model/common/lr_scheduler.py` | `get_scheduler()` (cosine, linear, constant) |
| `diffusion_policy_3d/config/dp3.yaml` | Main Hydra config (dp3 variant) |
| `diffusion_policy_3d/config/simple_dp3.yaml` | Simple DP3 Hydra config |
| `diffusion_policy_3d/config/task/` | 61 task configs: 3 Adroit + 4 DexArt + 50 MetaWorld + 4 RealDex |
| `diffusion_policy_3d/dataset/adroit_dataset.py` | `AdroitDataset(BaseDataset)` -- zarr-backed |
| `diffusion_policy_3d/dataset/dexart_dataset.py` | `DexArtDataset(BaseDataset)` |
| `diffusion_policy_3d/dataset/metaworld_dataset.py` | `MetaworldDataset(BaseDataset)` |
| `diffusion_policy_3d/dataset/realdex_dataset.py` | `RealDexDataset(BaseDataset)` -- real robot data |
| `diffusion_policy_3d/dataset/base_dataset.py` | `BaseDataset` interface: `get_normalizer()`, `__getitem__()` |
| `diffusion_policy_3d/env_runner/adroit_runner.py` | `AdroitRunner(BaseRunner)` -- rollout evaluation |
| `diffusion_policy_3d/env_runner/dexart_runner.py` | `DexArtRunner(BaseRunner)` |
| `diffusion_policy_3d/env_runner/metaworld_runner.py` | `MetaworldRunner(BaseRunner)` |
| `diffusion_policy_3d/common/replay_buffer.py` | Zarr-backed `ReplayBuffer` |
| `diffusion_policy_3d/common/sampler.py` | `SequenceSampler`, `get_val_mask`, `downsample_mask` |
| `diffusion_policy_3d/common/pytorch_util.py` | `dict_apply`, `optimizer_to` utilities |
| `diffusion_policy_3d/common/checkpoint_util.py` | `TopKCheckpointManager` |
| `scripts/train_policy.sh` | Training launcher (Hydra overrides) |
| `scripts/eval_policy.sh` | Evaluation launcher |
| `scripts/gen_demonstration_adroit.sh` | Adroit demo generation (VRL3 expert, 10 episodes) |
| `scripts/gen_demonstration_dexart.sh` | DexArt demo generation (RL checkpoint, 100 episodes) |
| `scripts/gen_demonstration_metaworld.sh` | MetaWorld demo generation (built-in expert, 10 episodes) |
| `scripts/convert_real_robot_data.py` | Convert raw real robot data (pickle) to zarr format with FPS + cropping |
| `third_party/` | Pinned deps: gym-0.21.0, mujoco-py-2.1.2.14, Metaworld, dexart-release, VRL3, pytorch3d_simplified |
| `visualizer/` | Optional plotly-based point cloud visualizer (`pip install -e .`) |

## Supported Environments (61 task configs)

| Suite | Tasks | Point Cloud Shape | Action Dim | State Dim |
|-------|-------|------------------|------------|-----------|
| Adroit | door, hammer, pen | (512, 3) | 26-28 | 24-30 |
| DexArt | bucket, faucet, laptop, toilet | (512, 3) | varies | varies |
| MetaWorld | 50 tasks (assembly, basketball, pick-place, etc.) | (512, 3) | varies | varies |
| RealDex | drill, dumpling, pour, roll | (1024, 3) | 22 | 22 |

## Tips & Gotchas

- **GPU memory**: DP3 uses ~10 GB GPU memory; training takes ~3 hours on A40. Simple DP3 is faster (1-2 hours) with comparable performance.
- **simple_dp3 vs dp3**: Simple DP3 uses UNet channels [128,256,384] with 1 resblock per level (vs [512,1024,2048] with 2). Recommended for real robot work due to 25 FPS inference speed.
- **Longer horizons help**: The authors recommend trying horizon=8/16/32 and n_action_steps=8/16 for better results on custom tasks.
- **Use global position actions**: Absolute end-effector position as action space works better than relative position.
- **Point cloud cropping is critical**: For real robot, crop out the table/background -- keep only task-relevant points. Use bounding box cropping + FPS downsampling (see `scripts/convert_real_robot_data.py`).
- **Camera quality**: RealSense L515 is recommended; D435 produces poor point clouds that cause DP3 to fail.
- **gym version is critical**: Must use the pinned `gym==0.21.0` from `third_party/`. Other versions break environment wrappers.
- **pip version**: If gym-0.21.0 fails to install with pip>=24, downgrade to `pip install pip==21`.
- **opencv-python spec**: The gym-0.21.0 `setup.py` line 20 has `opencv-python>=3.` (missing minor version). Edit to `opencv-python>=3.0` if installation fails.
- **pytorch3d CUDA errors**: If you get "no kernel image is available", reinstall from `third_party/pytorch3d_simplified`.
- **huggingface_hub**: Use version <= 0.25.2 (`pip install huggingface_hub==0.25.2`) to avoid `cached_download` import error from diffusers.
- **OpenGL/rendering errors**: Run `unset LD_PRELOAD` and set `export MUJOCO_GL=egl` for headless rendering.
- **Demonstration quality matters**: Results depend heavily on demo quality. Re-generate if you get bad demonstrations rather than adding more.
- **WandB**: Results are logged to WandB; run `wandb login` before training. Use `logging.mode=offline` for debugging.
- **Checkpoints use dill**: All checkpoints are saved with `pickle_module=dill`. Use `torch.load(path, pickle_module=dill)` to load.
- **Real robot deployment**: For deployment inference loop code, refer to [iDP3](https://github.com/YanjieZe/Improved-3D-Diffusion-Policy).
- **Custom tasks**: Need to implement: (1) env wrapper in `env/`, (2) env runner in `env_runner/`, (3) dataset class in `dataset/`, (4) task config YAML in `config/task/`. See Adroit implementations as reference.
- **Nested repo layout**: The inner `3D-Diffusion-Policy/` is the package directory. Scripts in `scripts/` do `cd 3D-Diffusion-Policy` internally. Running `train.py` directly requires being in the inner dir or adjusting sys.path.
