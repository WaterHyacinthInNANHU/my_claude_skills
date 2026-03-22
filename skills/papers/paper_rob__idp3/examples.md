# iDP3 — Examples & Recipes

## 1. Installation

```bash
conda create -n idp3 python=3.8
conda activate idp3

# PyTorch (CUDA 12.1)
pip3 install torch==2.1.0 torchvision --index-url https://download.pytorch.org/whl/cu121

# Clone repo
git clone https://github.com/YanjieZe/Improved-3D-Diffusion-Policy
cd Improved-3D-Diffusion-Policy

# Install dependencies
cd third_party/visualizer && pip install -e . && cd ../..
pip install kaleido plotly open3d tyro termcolor h5py

pip install --no-cache-dir wandb ipdb gpustat visdom notebook mediapy torch_geometric \
    natsort scikit-video easydict pandas moviepy imageio imageio-ffmpeg termcolor av \
    open3d dm_control dill==0.3.5.1 hydra-core==1.2.0 einops==0.4.1 diffusers==0.11.1 \
    zarr==2.12.0 numba==0.56.4 pygame==2.1.2 shapely==1.8.4 tensorboard==2.10.1 \
    tensorboardx==2.5.1 absl-py==0.13.0 pyparsing==2.4.7 jupyterlab==3.0.14 \
    scikit-image yapf==0.31.0 opencv-python==4.5.3.56 psutil av matplotlib setuptools==59.5.0

cd Improved-3D-Diffusion-Policy && pip install -e . && cd ..

# Optional: image-based policy
pip install timm==0.9.7
cd third_party/r3m && pip install -e . && cd ../..

# Optional: deployment camera
pip install pyrealsense2==2.54.2.5684
```

## 2. Train iDP3 (3D Policy)

```bash
# Download example data from Google Drive:
# https://drive.google.com/file/d/1c-rDOe1CcJM8iUuT1ecXKjDYAn-afy2e

# Edit scripts/train_policy.sh to set dataset_path
# Then:
bash scripts/train_policy.sh idp3 gr1_dex-3d 0913_example

# This runs:
# python train.py --config-name=idp3.yaml task=gr1_dex-3d \
#     exp_name=gr1_dex-3d-idp3-0913_example \
#     task.dataset.zarr_path=$dataset_path
```

Training logs to WandB by default. Checkpoints saved every 100 epochs.

## 3. Train Image-Based Baseline (2D Policy)

```bash
bash scripts/train_policy.sh dp_224x224_r3m gr1_dex-image 0913_example
```

## 4. Deploy on Robot

```bash
# After training, deploy with:
bash scripts/deploy_policy.sh idp3 gr1_dex-3d 0913_example

# The script loads the latest checkpoint and runs inference.
# Modify deploy.py for your robot's API — the default targets Fourier GR1.
```

## 5. Visualize Training Data

```bash
# Set dataset path in scripts/vis_dataset.sh, then:
bash scripts/vis_dataset.sh

# For point cloud rendering:
# Set vis_cloud=1 in the script
```

## 6. Use iDP3 Components in Your Own Project

### Load a trained policy

```python
import hydra
from diffusion_policy_3d.workspace.idp3_workspace import iDP3Workspace

# Load checkpoint
workspace = iDP3Workspace.from_checkpoint('/path/to/checkpoint.ckpt')
policy = workspace.get_model()
policy.eval()
policy.to('cuda')

# Run inference
import torch
obs_dict = {
    'point_cloud': torch.randn(1, 2, 4096, 3).cuda(),  # [B, T_obs, N, 3]
    'agent_pos': torch.randn(1, 2, 32).cuda(),          # [B, T_obs, state_dim]
}
with torch.no_grad():
    result = policy.predict_action(obs_dict)
    action = result['action']  # [1, 15, 25]
```

### Use the MultiStagePointNet encoder standalone

```python
from diffusion_policy_3d.model.vision_3d.multi_stage_pointnet import MultiStagePointNetEncoder

encoder = MultiStagePointNetEncoder(
    h_dim=128,
    out_channels=128,
    num_layers=4,
)

points = torch.randn(8, 4096, 3)  # [B, N, 3]
features = encoder(points)         # [B, 128]
```

### Use the full iDP3Encoder (point cloud + state)

```python
from diffusion_policy_3d.model.vision_3d.pointnet_extractor import iDP3Encoder

observation_space = {
    'point_cloud': (4096, 3),
    'agent_pos': (32,),
}

encoder = iDP3Encoder(
    observation_space=observation_space,
    state_mlp_size=(64, 64),
    pointnet_type='multi_stage_pointnet',
    pointcloud_encoder_cfg={
        'in_channels': 3,
        'out_channels': 128,
        'num_points': 4096,
        'use_layernorm': True,
        'final_norm': 'layernorm',
    },
    use_pc_color=False,
    point_downsample=True,
)

observations = {
    'point_cloud': torch.randn(8, 2, 4096, 3),  # [B, T, N, 3]
    'agent_pos': torch.randn(8, 2, 32),          # [B, T, state_dim]
}
features = encoder(observations)  # [B, 192] (128 point + 64 state)
```

### Prepare your own Zarr dataset

```python
import zarr
import numpy as np

# Create zarr dataset matching iDP3 format
root = zarr.open('/path/to/my_dataset.zarr', 'w')
data = root.create_group('data')

# Per episode: store state, action, point_cloud
ep = data.create_group('episode_0')
T = 100  # trajectory length
ep.create_dataset('state', data=np.random.randn(T, 32).astype(np.float32))
ep.create_dataset('action', data=np.random.randn(T, 25).astype(np.float32))
ep.create_dataset('point_cloud', data=np.random.randn(T, 4096, 3).astype(np.float32))

# Meta info
meta = root.create_group('meta')
meta.create_dataset('episode_ends', data=np.array([T]))  # cumulative episode ends
```

## 7. Adapt for a Different Robot

Key changes needed:

1. **Action/state dimensions**: Modify `shape_meta` in task YAML config
2. **Camera setup**: Replace `MultiRealSense` in `deploy.py` with your camera driver
3. **Robot comm**: Replace `upbody_comm.set_pos()` with your robot's action API
4. **Data collection**: Use your own teleoperation system or adapt the [Humanoid-Teleoperation repo](https://github.com/YanjieZe/Humanoid-Teleoperation)

The core iDP3 algorithm (encoder + diffusion policy) is robot-agnostic.

## 8. Config Overrides (Hydra CLI)

```bash
# Change number of points
python train.py --config-name=idp3.yaml \
    policy.pointcloud_encoder_cfg.num_points=2048

# Change learning rate
python train.py --config-name=idp3.yaml \
    optimizer.lr=3e-4

# Change horizon
python train.py --config-name=idp3.yaml \
    horizon=32 n_obs_steps=3 n_action_steps=30

# Use a different GPU
python train.py --config-name=idp3.yaml \
    training.device=cuda:1
```
