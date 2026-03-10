# DP3 Usage Examples

## Installation

```bash
# 1. Create environment
conda create -n dp3 python=3.8 && conda activate dp3

# 2. PyTorch (match your CUDA version)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. Clone and install DP3
git clone https://github.com/YanjieZe/3D-Diffusion-Policy.git
cd 3D-Diffusion-Policy/3D-Diffusion-Policy && pip install -e . && cd ../..

# 4. MuJoCo 2.1.0
mkdir -p ~/.mujoco && cd ~/.mujoco
wget https://github.com/deepmind/mujoco/releases/download/2.1.0/mujoco210-linux-x86_64.tar.gz -O mujoco210.tar.gz --no-check-certificate
tar -xvzf mujoco210.tar.gz

# Add to ~/.bashrc:
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/.mujoco/mujoco210/bin:/usr/lib/nvidia:/usr/local/cuda/lib64
export MUJOCO_GL=egl

# 5. Install pinned third-party deps
cd 3D-Diffusion-Policy
pip install setuptools==59.5.0 Cython==0.29.35 patchelf==0.17.2.0
cd third_party/mujoco-py-2.1.2.14 && pip install -e . && cd ../..
cd third_party/gym-0.21.0 && pip install -e . && cd ../..
cd third_party/Metaworld && pip install -e . && cd ../..
cd third_party/dexart-release && pip install -e . && cd ../..
cd third_party/rrl-dependencies && pip install -e mj_envs/. && pip install -e mjrl/. && cd ../..
cd third_party/pytorch3d_simplified && pip install -e . && cd ../..

# 6. Remaining packages
pip install zarr==2.12.0 wandb ipdb gpustat dm_control omegaconf \
    hydra-core==1.2.0 dill==0.3.5.1 einops==0.4.1 diffusers==0.11.1 \
    numba==0.56.4 moviepy imageio av matplotlib termcolor

# 7. Login to WandB
wandb login
```

## Download Assets

```bash
# Adroit RL experts (for generating demos)
# Download from: https://1drv.ms/u/s!Ag5QsBIFtRnTlFWqYWtS2wMMPKNX?e=dw8hsS
# or: https://drive.google.com/file/d/1iNkSrLD_N4NrezLx58L1YoBBqYYg-33u/view
# Unzip ckpts/ into third_party/VRL3/

# DexArt assets
# Download from: https://drive.google.com/file/d/1DxRfB4087PeM3Aejd6cR-RQVgOKdNrL4/view
# Unzip assets/ into third_party/dexart-release/

# Real robot demo data
# Download from: https://drive.google.com/file/d/1G5MP6Nzykku9sDDdzy7tlRqMBnKb253O/view
# Place in 3D-Diffusion-Policy/data/
```

## Generate Demonstrations

```bash
# Adroit (door, hammer, pen)
bash scripts/gen_demonstration_adroit.sh hammer

# DexArt (bucket, faucet, laptop, toilet)
bash scripts/gen_demonstration_dexart.sh bucket

# MetaWorld (50 tasks)
bash scripts/gen_demonstration_metaworld.sh assembly
```

## Training

```bash
# Format: bash scripts/train_policy.sh <alg> <task> <run_id> <seed> <gpu_id>

# DP3 on Adroit hammer
bash scripts/train_policy.sh dp3 adroit_hammer exp01 0 0

# Simple DP3 (faster, ~25 FPS inference)
bash scripts/train_policy.sh simple_dp3 adroit_hammer exp01 0 0

# MetaWorld task
bash scripts/train_policy.sh dp3 metaworld_assembly exp01 0 0

# DexArt task
bash scripts/train_policy.sh dp3 dexart_bucket exp01 0 0
```

### What the training script does internally:

```bash
cd 3D-Diffusion-Policy
python train.py --config-name=dp3.yaml \
    task=adroit_hammer \
    hydra.run.dir=data/outputs/${exp_name}_seed${seed} \
    training.debug=False \
    training.seed=0 \
    training.device="cuda:0" \
    exp_name=adroit_hammer-dp3-exp01 \
    logging.mode=online \
    checkpoint.save_ckpt=True
```

## Evaluation

```bash
# Format: bash scripts/eval_policy.sh <alg> <task> <run_id> <seed> <gpu_id>
bash scripts/eval_policy.sh dp3 adroit_hammer exp01 0 0
```

> **Note**: For benchmarking, use WandB metrics from training. The eval script is mainly for deployment/visualization.

## Real Robot Deployment

### Data collection format (per episode of length T)
```python
{
    'point_cloud': np.array,  # (T, N_points, 6) -- [x, y, z, r, g, b]
    'image': np.array,        # (T, H, W, 3)
    'depth': np.array,        # (T, H, W)
    'agent_pos': np.array,    # (T, state_dim)
    'action': np.array,       # (T, action_dim) -- relative control
}
```

### Convert to zarr format
```bash
python scripts/convert_real_robot_data.py
```

### Train on real data
```bash
bash scripts/train_policy.sh dp3 realdex_pour exp01 0 0
```

## Custom Task Integration

### 1. Create a task config (`config/task/my_task.yaml`)
```yaml
defaults:
  - _self_
  - /env_runner: my_task_runner  # or skip if no online eval

name: my_task
dataset_type: my_task
shape_meta:
  obs:
    point_cloud:
      shape: [512, 3]    # N_points, channels (3=XYZ, 6=XYZRGB)
    agent_pos:
      shape: [7]          # your robot state dim
  action:
    shape: [7]            # your action dim

dataset:
  zarr_path: data/my_task.zarr
  horizon: ${horizon}
  pad_before: ${eval:'${n_obs_steps}-1'}
  pad_after: ${eval:'${n_action_steps}-1'}
  seed: ${training.seed}
  val_ratio: 0.02
```

### 2. Create a dataset class (`dataset/my_task_dataset.py`)
Follow the pattern in `adroit_dataset.py`:
- Inherit from `BaseDataset`
- Implement `_sample_to_data()` to return dict with `obs.point_cloud`, `obs.agent_pos`, `action`

### 3. Key considerations
- **Point cloud preprocessing**: Crop to task-relevant region, FPS downsample to 512-1024 points
- **Action space**: Try both relative and global position
- **Horizons**: Start with `horizon=16, n_obs_steps=2, n_action_steps=8`; tune as needed

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: distutils` | `pip install setuptools==59.5.0` |
| mujoco-py compilation fails | `pip install Cython==0.29.35` |
| gym install fails with pip 24 | `pip install pip==21` then reinstall gym |
| `ImportError: cached_download` | `pip install huggingface_hub==0.25.2` |
| OpenGL failures | `unset LD_PRELOAD` and set `MUJOCO_GL=egl` |
| pytorch3d CUDA errors | Reinstall from `third_party/pytorch3d_simplified` |
| PathNotFoundError | Run from repo root; scripts `cd` internally |
