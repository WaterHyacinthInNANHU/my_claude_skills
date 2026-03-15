# DP3 Usage Examples

## Installation

```bash
# 1. Create environment
conda create -n dp3 python=3.8 && conda activate dp3

# 2. PyTorch (match your CUDA version)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. Clone and install DP3
git clone https://github.com/YanjieZe/3D-Diffusion-Policy.git
cd 3D-Diffusion-Policy
cd 3D-Diffusion-Policy && pip install -e . && cd ..

# 4. MuJoCo 2.1.0
mkdir -p ~/.mujoco && cd ~/.mujoco
wget https://github.com/deepmind/mujoco/releases/download/2.1.0/mujoco210-linux-x86_64.tar.gz -O mujoco210.tar.gz --no-check-certificate
tar -xvzf mujoco210.tar.gz && cd -

# Add to ~/.bashrc:
#   export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/.mujoco/mujoco210/bin:/usr/lib/nvidia:/usr/local/cuda/lib64
#   export MUJOCO_GL=egl

# 5. Install pinned third-party deps (order matters)
pip install setuptools==59.5.0 Cython==0.29.35 patchelf==0.17.2.0
cd third_party/mujoco-py-2.1.2.14 && pip install -e . && cd ../..
cd third_party/gym-0.21.0 && pip install -e . && cd ../..
cd third_party/dexart-release && pip install -e . && cd ../..
cd third_party/Metaworld && pip install -e . && cd ../..
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
# Adroit RL experts (needed for generating Adroit demos)
# Download from: https://1drv.ms/u/s!Ag5QsBIFtRnTlFWqYWtS2wMMPKNX?e=dw8hsS
# or: https://drive.google.com/file/d/1iNkSrLD_N4NrezLx58L1YoBBqYYg-33u/view
# Unzip ckpts/ into third_party/VRL3/

# DexArt assets (needed for DexArt envs)
# Download from: https://drive.google.com/file/d/1DxRfB4087PeM3Aejd6cR-RQVgOKdNrL4/view
# Unzip assets/ into third_party/dexart-release/

# Real robot demo data (optional)
# Download from: https://drive.google.com/file/d/1G5MP6Nzykku9sDDdzy7tlRqMBnKb253O/view
# Place zarr files in 3D-Diffusion-Policy/data/
```

---

## Scenario 1: Generate Demonstrations

```bash
# Adroit tasks (door, hammer, pen) -- 10 episodes each
bash scripts/gen_demonstration_adroit.sh hammer
# Internally runs: cd third_party/VRL3/src && python gen_demonstration_expert.py \
#   --env_name hammer --num_episodes 10 \
#   --root_dir "../../../3D-Diffusion-Policy/data/" \
#   --expert_ckpt_path "../ckpts/vrl3_hammer.pt" \
#   --img_size 84 --not_use_multi_view --use_point_crop

# DexArt tasks (bucket, faucet, laptop, toilet) -- 100 episodes each
bash scripts/gen_demonstration_dexart.sh bucket
# Internally runs: cd third_party/dexart-release && python examples/gen_demonstration_expert.py \
#   --task_name=bucket --num_episodes 100 --root_dir ../../3D-Diffusion-Policy/data/ \
#   --img_size 84 --num_points 1024

# MetaWorld tasks (50 tasks) -- 10 episodes each
bash scripts/gen_demonstration_metaworld.sh assembly
# Internally runs: cd third_party/Metaworld && python gen_demonstration_expert.py \
#   --env_name=assembly --num_episodes 10 --root_dir "../../3D-Diffusion-Policy/data/"
```

Data is saved as zarr archives in `3D-Diffusion-Policy/data/`.

---

## Scenario 2: Train DP3

```bash
# Format: bash scripts/train_policy.sh <alg> <task> <tag> <seed> <gpu_id>

# DP3 on Adroit hammer (3h on A40, ~10GB VRAM)
bash scripts/train_policy.sh dp3 adroit_hammer exp01 0 0

# Simple DP3 -- faster (1-2h), 25 FPS inference, slightly less accurate
bash scripts/train_policy.sh simple_dp3 adroit_hammer exp01 0 0

# MetaWorld task
bash scripts/train_policy.sh dp3 metaworld_assembly exp01 0 0

# DexArt task
bash scripts/train_policy.sh dp3 dexart_bucket exp01 0 0
```

### What the training script does internally

```bash
cd 3D-Diffusion-Policy
export HYDRA_FULL_ERROR=1
export CUDA_VISIBLE_DEVICES=0
python train.py --config-name=dp3.yaml \
    task=adroit_hammer \
    hydra.run.dir=data/outputs/adroit_hammer-dp3-exp01_seed0 \
    training.debug=False \
    training.seed=0 \
    training.device="cuda:0" \
    exp_name=adroit_hammer-dp3-exp01 \
    logging.mode=online \
    checkpoint.save_ckpt=True
```

### Override common hyperparameters

```bash
# Change horizon and action steps
python train.py --config-name=dp3.yaml \
    task=adroit_hammer \
    horizon=32 n_action_steps=16 \
    training.num_epochs=5000

# Use debug mode (100 epochs, 10 train steps, fast iteration)
python train.py --config-name=dp3.yaml \
    task=adroit_hammer \
    training.debug=True

# Offline WandB logging
python train.py --config-name=dp3.yaml \
    task=adroit_hammer \
    logging.mode=offline
```

---

## Scenario 3: Evaluate a Saved Policy

```bash
# Same arguments as training
bash scripts/eval_policy.sh dp3 adroit_hammer exp01 0 0
```

This loads `data/outputs/adroit_hammer-dp3-exp01_seed0/checkpoints/latest.ckpt` and runs 20 rollout episodes (configurable via `env_runner.eval_episodes` in the task config).

**Note**: For benchmarking, use WandB metrics from training. The eval script is for deployment/visualization.

---

## Scenario 4: Real Robot Data & Training

### Collect data in the expected format

Each episode (length T) should be a dictionary:

```python
episode = {
    'point_cloud': np.array,  # (T, N_points, 6) -- [x, y, z, r, g, b]
    'image': np.array,        # (T, H, W, 3)
    'depth': np.array,        # (T, H, W)
    'agent_pos': np.array,    # (T, state_dim) -- e.g. 22 for Franka+Allegro
    'action': np.array,       # (T, action_dim) -- relative EE pos + joint angles
}
```

### Convert raw data to zarr

Edit paths in `scripts/convert_real_robot_data.py`, then:

```bash
python scripts/convert_real_robot_data.py
```

This script:
1. Applies extrinsics transform to point clouds
2. Crops to workspace bounding box
3. FPS downsamples to 1024 points
4. Resizes images to 84x84
5. Saves as zarr with `data/{img, point_cloud, depth, action, state}` and `meta/episode_ends`

### Train on real data

```bash
bash scripts/train_policy.sh dp3 realdex_drill exp01 0 0
```

The `realdex_*` task configs set `env_runner: null` (no sim evaluation), so only training loss and train_action_mse are logged.

### Deploy

For real-time inference loop, refer to [iDP3](https://github.com/YanjieZe/Improved-3D-Diffusion-Policy).

---

## Scenario 5: Add a Custom Task

### Step 1: Create task config

Create `diffusion_policy_3d/config/task/my_task.yaml`:

```yaml
name: my_task

task_name: my_task

shape_meta: &shape_meta
  obs:
    point_cloud:
      shape: [512, 3]       # N_points, channels (3=XYZ, 6=XYZRGB)
      type: point_cloud
    agent_pos:
      shape: [7]             # your robot state dim
      type: low_dim
  action:
    shape: [7]               # your action dim

env_runner: null              # or implement a custom runner

dataset:
  _target_: diffusion_policy_3d.dataset.my_task_dataset.MyTaskDataset
  zarr_path: data/my_task.zarr
  horizon: ${horizon}
  pad_before: ${eval:'${n_obs_steps}-1'}
  pad_after: ${eval:'${n_action_steps}-1'}
  seed: 42
  val_ratio: 0.02
  max_train_episodes: 90
```

### Step 2: Create dataset class

Create `diffusion_policy_3d/dataset/my_task_dataset.py` following `adroit_dataset.py`:

```python
from typing import Dict
import torch
import numpy as np
import copy
from diffusion_policy_3d.common.pytorch_util import dict_apply
from diffusion_policy_3d.common.replay_buffer import ReplayBuffer
from diffusion_policy_3d.common.sampler import SequenceSampler, get_val_mask, downsample_mask
from diffusion_policy_3d.model.common.normalizer import LinearNormalizer, SingleFieldLinearNormalizer
from diffusion_policy_3d.dataset.base_dataset import BaseDataset

class MyTaskDataset(BaseDataset):
    def __init__(self, zarr_path, horizon=1, pad_before=0, pad_after=0,
                 seed=42, val_ratio=0.0, max_train_episodes=None):
        super().__init__()
        self.replay_buffer = ReplayBuffer.copy_from_path(
            zarr_path, keys=['state', 'action', 'point_cloud'])
        val_mask = get_val_mask(
            n_episodes=self.replay_buffer.n_episodes,
            val_ratio=val_ratio, seed=seed)
        train_mask = ~val_mask
        train_mask = downsample_mask(mask=train_mask, max_n=max_train_episodes, seed=seed)

        self.sampler = SequenceSampler(
            replay_buffer=self.replay_buffer,
            sequence_length=horizon,
            pad_before=pad_before, pad_after=pad_after,
            episode_mask=train_mask)
        self.train_mask = train_mask
        self.horizon = horizon
        self.pad_before = pad_before
        self.pad_after = pad_after

    def get_validation_dataset(self):
        val_set = copy.copy(self)
        val_set.sampler = SequenceSampler(
            replay_buffer=self.replay_buffer,
            sequence_length=self.horizon,
            pad_before=self.pad_before, pad_after=self.pad_after,
            episode_mask=~self.train_mask)
        val_set.train_mask = ~self.train_mask
        return val_set

    def get_normalizer(self, mode='limits', **kwargs):
        data = {
            'action': self.replay_buffer['action'],
            'agent_pos': self.replay_buffer['state'],
            'point_cloud': self.replay_buffer['point_cloud'],
        }
        normalizer = LinearNormalizer()
        normalizer.fit(data=data, last_n_dims=1, mode=mode, **kwargs)
        return normalizer

    def __len__(self):
        return len(self.sampler)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.sampler.sample_sequence(idx)
        data = {
            'obs': {
                'point_cloud': sample['point_cloud'].astype(np.float32),
                'agent_pos': sample['state'].astype(np.float32),
            },
            'action': sample['action'].astype(np.float32),
        }
        return dict_apply(data, torch.from_numpy)
```

### Step 3: Prepare zarr data

```python
import zarr
import numpy as np

# Collect your episodes, each with:
#   point_clouds: list of (T_i, N_pts, 3) arrays
#   states:       list of (T_i, D_state) arrays
#   actions:      list of (T_i, D_action) arrays

all_pc, all_state, all_action = [], [], []
episode_ends = []
total = 0
for pc, st, act in zip(point_clouds, states, actions):
    total += len(pc)
    all_pc.append(pc)
    all_state.append(st)
    all_action.append(act)
    episode_ends.append(total)

all_pc = np.concatenate(all_pc, axis=0)         # (N_total, N_pts, 3)
all_state = np.concatenate(all_state, axis=0)    # (N_total, D_state)
all_action = np.concatenate(all_action, axis=0)  # (N_total, D_action)
episode_ends = np.array(episode_ends)

zarr_root = zarr.group('data/my_task.zarr')
zarr_data = zarr_root.create_group('data')
zarr_meta = zarr_root.create_group('meta')
compressor = zarr.Blosc(cname='zstd', clevel=3, shuffle=1)
zarr_data.create_dataset('point_cloud', data=all_pc, chunks=(100,)+all_pc.shape[1:],
                         dtype='float32', compressor=compressor)
zarr_data.create_dataset('state', data=all_state, chunks=(100, all_state.shape[1]),
                         dtype='float32', compressor=compressor)
zarr_data.create_dataset('action', data=all_action, chunks=(100, all_action.shape[1]),
                         dtype='float32', compressor=compressor)
zarr_meta.create_dataset('episode_ends', data=episode_ends, chunks=(100,),
                         dtype='int64', compressor=compressor)
```

### Step 4: Train

```bash
bash scripts/train_policy.sh dp3 my_task exp01 0 0
```

---

## Scenario 6: Standalone PointNet Encoder Usage

```python
import sys
sys.path.append("/path/to/3D-Diffusion-Policy/3D-Diffusion-Policy")

import torch
from diffusion_policy_3d.model.vision.pointnet_extractor import PointNetEncoderXYZ

encoder = PointNetEncoderXYZ(
    in_channels=3,
    out_channels=64,
    use_layernorm=True,
    final_norm='layernorm',
)
encoder.eval().cuda()

# Input: (B, N_points, 3) -- XYZ coordinates
points = torch.randn(4, 512, 3).cuda()
features = encoder(points)  # (4, 64) -- compact point cloud features
```

---

## Scenario 7: Visualize Point Clouds

```bash
cd visualizer && pip install -e . && cd ..
pip install kaleido plotly
```

```python
import visualizer
import numpy as np

# Shape (N, 3) for XYZ or (N, 6) for XYZRGB
pointcloud = np.random.randn(512, 3)
visualizer.visualize_pointcloud(pointcloud)  # Opens in web browser
```

---

## Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `AttributeError: module 'distutils' has no attribute 'version'` | `pip install setuptools==59.5.0` |
| mujoco-py Cython compilation error | `pip install Cython==0.29.35` |
| `GL/glew.h: No such file or directory` | `sudo apt-get install libglew-dev` |
| `RuntimeError: Ninja is required` | `sudo apt-get install ninja-build` |
| gym-0.21.0 install fails with pip>=24 | `pip install pip==21` then reinstall gym |
| gym `extras_require` metadata error | Same as above: downgrade pip |
| gym `opencv-python>=3.` invalid spec | Edit `third_party/gym-0.21.0/setup.py` line 20: change `>=3.` to `>=3.0` |
| `ImportError: cannot import name 'cached_download'` | `pip install huggingface_hub==0.25.2` |
| `RuntimeError: Fail to initialize OpenGL` | `unset LD_PRELOAD` |
| mujoco rendering not using GPU | Set `export MUJOCO_GL=egl` |
| `RuntimeError: CUDA error: no kernel image` (pytorch3d) | `pip uninstall pytorch3d && cd third_party/pytorch3d_simplified && pip install -e .` |
| `ImportError: cannot import name '_C'` (pytorch3d) | Same as above: reinstall pytorch3d |
| `GLIBCXX_3.4.29 not found` | `sudo apt-get install libstdc++6` (upgrade libstdc++) |
| wandb `BadAccess` GLX error | `export QT_GRAPHICSSYSTEM=native` |
| `PathNotFoundError` when running `python -m train` | Must run from the inner `3D-Diffusion-Policy/` directory, or use the shell scripts |
| `SystemError: initialization of _internal failed` (numba) | `pip uninstall numba && pip install -U numba` |
| `AssertionError: Default values can only be a CfgNode` | `pip install yacs==0.1.8` |
| `Can't get attribute '_make_function'` (cloudpickle) | `pip install cloudpickle --upgrade` |
