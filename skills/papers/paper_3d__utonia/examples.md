# Utonia Examples

## 1. Basic Feature Extraction (Indoor Scene)

```python
import torch
import numpy as np
import utonia

# Load model
model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# Load sample or your own data
point = utonia.data.load("sample1")

# Transform (indoor scene — scale=0.5 per official demo/0_pca_indoor.py)
transform = utonia.transform.default(scale=0.5, apply_z_positive=True, normalize_coord=False)
point = transform(point)
for key in point.keys():
    if isinstance(point[key], torch.Tensor):
        point[key] = point[key].cuda(non_blocking=True)

with torch.no_grad():
    point = model(point)

# Get per-point features at voxel resolution (method from official demos)
# Concat first 2 levels for richer features, nearest-neighbor for rest
for _ in range(2):
    parent = point.pop("pooling_parent")
    inverse = point.pop("pooling_inverse")
    parent.feat = torch.cat([parent.feat, point.feat[inverse]], dim=-1)
    point = parent
while "pooling_parent" in point.keys():
    parent = point.pop("pooling_parent")
    inverse = point.pop("pooling_inverse")
    parent.feat = point.feat[inverse]
    point = parent

feat = point.feat[point.inverse]  # (N_original, C) features at input resolution
print(f"Features shape: {feat.shape}")
```

## 2. Robotic Manipulation (Frozen Encoder for RL)

```python
import utonia
import torch
import numpy as np

# Load in encoder-only mode (no decoder, faster)
model = utonia.load(
    "utonia", repo_id="Pointcept/Utonia",
    custom_config=dict(enc_mode=True, enable_flash=False, enc_patch_size=[1024]*5),
).cuda().eval()

# Manipulation transform: scale=4.0, NO NormalizeCoord (per official demo/5_pca_manipulation.py)
transform = utonia.transform.default(scale=4.0)

# Prepare point cloud (coords in meters, no color/normal needed)
coord = np.array(...)  # (N, 3) from depth camera, in meters
point = {
    "coord": coord,
    "color": np.zeros_like(coord, dtype=np.float32),
    "normal": np.zeros_like(coord, dtype=np.float32),
}
point = transform(point)
batch_dict = utonia.data.collate_fn([point])
for k in batch_dict:
    if isinstance(batch_dict[k], torch.Tensor):
        batch_dict[k] = batch_dict[k].cuda(non_blocking=True)

with torch.no_grad():
    output = model(batch_dict)

# output.feat: (N_bottleneck, 576) — e.g., ~723 pts from 4096 input
# output.offset: (B,) cumulative counts per sample

# Global max-pool for RL policy input
feat = output.feat         # (N_bottleneck, 576)
offset = output.offset     # (B,)
starts = torch.cat([torch.tensor([0], device=feat.device), offset[:-1]])
global_features = torch.stack([
    feat[starts[i]:offset[i]].max(dim=0)[0]
    for i in range(len(offset))
])  # (B, 576)
```

**IMPORTANT transform pitfall:** Do NOT use `NormalizeCoord` + large scale (e.g., 50).
This makes the voxel grid too fine, preventing hierarchical pooling — features will be degraded.
```
scale=4.0, no NormalizeCoord → 4096 → 4086 → 2452 → 723 ✓ (proper hierarchy)
scale=50 + NormalizeCoord    → 4096 → 4096 → 4096 → 4096 ✗ (no pooling!)
```

## 3. Batched Inference

```python
import utonia
import numpy as np
import torch

model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# Prepare batch: concatenate points, assign batch indices
points_list = [utonia.data.load("sample1"), utonia.data.load("sample1")]
coords, colors, normals, batches = [], [], [], []
for i, p in enumerate(points_list):
    n = p["coord"].shape[0]
    coords.append(p["coord"])
    colors.append(p.get("color", np.zeros((n, 3))))
    normals.append(p.get("normal", np.zeros((n, 3))))
    batches.append(np.full(n, i))

point = {
    "coord": np.concatenate(coords),
    "color": np.concatenate(colors),
    "normal": np.concatenate(normals),
    "batch": np.concatenate(batches),
}

# Use appropriate scale for your domain
transform = utonia.transform.default(scale=0.5, apply_z_positive=True)
point = transform(point)
for key in point.keys():
    if isinstance(point[key], torch.Tensor):
        point[key] = point[key].cuda(non_blocking=True)

with torch.no_grad():
    point = model(point)
```

## 4. Object-Level Inference (Single Object / CAD Model)

```python
import utonia
import numpy as np

model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# For single objects, scale=1.0 (per official demo/6_pca_object.py)
transform = utonia.transform.default(scale=1.0)

point = {
    "coord": np.load("object_xyz.npy"),
    "normal": np.load("object_normals.npy"),  # color optional
}
# ... transform and forward as above
```

## 5. Outdoor LiDAR Inference

For outdoor LiDAR, use a custom transform (no CenterShift, ego at origin):

```python
import utonia

config = [
    dict(type="RandomScale", scale=[50, 50]),
    dict(
        type="GridSample",
        grid_size=0.01,
        hash_type="fnv",
        mode="train",
        return_grid_coord=True,
        return_inverse=True,
    ),
    dict(type="ToTensor"),
    dict(
        type="Collect",
        keys=("coord", "grid_coord", "inverse"),
        feat_keys=("coord",),  # LiDAR typically has no color/normal
    ),
]
transform = utonia.transform.Compose(config)

point = {"coord": lidar_xyz}  # ego-vehicle at origin, road on xy-plane
# ... transform and forward
```

## 6. PCA Visualization of Per-Point Features

```python
import utonia
import torch
import numpy as np

model = utonia.load(
    "utonia", repo_id="Pointcept/Utonia",
    custom_config=dict(enc_mode=True, enable_flash=False, enc_patch_size=[1024]*5),
).cuda().eval()
transform = utonia.transform.default(scale=4.0)  # manipulation

# Prepare and encode
point = {"coord": coord_np, "color": np.zeros_like(coord_np), "normal": np.zeros_like(coord_np)}
point = transform(point)
batch_dict = utonia.data.collate_fn([point])
for k in batch_dict:
    if isinstance(batch_dict[k], torch.Tensor):
        batch_dict[k] = batch_dict[k].cuda(non_blocking=True)

with torch.no_grad():
    output = model(batch_dict)

# Unpool bottleneck features back to voxel resolution
point = output
while "pooling_parent" in point.keys():
    parent = point.pop("pooling_parent")
    inverse = point.pooling_inverse
    parent.feat = point.feat[inverse]
    point = parent

feat = point.feat   # (N_voxel, 576)
coord = point.coord # (N_voxel, 3)

# PCA → RGB
u, s, v = torch.pca_lowrank(feat, niter=5, q=6)
proj = (feat @ v)[:, :3]
colors = (proj - proj.min(0)[0]) / (proj.max(0)[0] - proj.min(0)[0] + 1e-6)
colors = colors.clamp(0, 1).cpu().numpy()
# Render with matplotlib or open3d
```

## 7. Run Demos

```bash
cd Utonia
export PYTHONPATH=./

# PCA visualization (note: each demo uses domain-appropriate scale)
python demo/0_pca_indoor.py        # indoor, scale=0.5
python demo/5_pca_manipulation.py  # manipulation, scale=4.0
python demo/6_pca_object.py        # object, scale=1.0

# Without color/normal modalities
python demo/0_pca_indoor.py --wo_color --wo_normal

# Video demo (requires VGGT installed)
python demo/8_pca_video.py \
    --input_video path/to/video.mp4 \
    --conf_thres 0 \
    --prediction_mode "Depthmap and Camera Branch" \
    --if_TSDF \
    --pca_start 1 \
    --pca_brightness 1.2
```

## 8. Fine-tuning with Pointcept

```bash
git clone https://github.com/Pointcept/Pointcept.git
cd Pointcept
# Edit config to point weight to downloaded Utonia checkpoint
# Example: configs/scannet/semseg-pt-v3m1-0-base.py
# Set model.backbone.init_cfg.checkpoint = "path/to/utonia.pth"
```

## 9. Integration Pattern for Custom Projects

```python
# utonia as a frozen feature extractor
import utonia
import torch
import torch.nn as nn

class MyDownstreamModel(nn.Module):
    def __init__(self, num_classes, freeze_backbone=True):
        super().__init__()
        self.backbone = utonia.model.load("utonia", repo_id="Pointcept/Utonia")
        if freeze_backbone:
            for p in self.backbone.parameters():
                p.requires_grad = False
        self.head = nn.Linear(576, num_classes)  # bottleneck dim is 576

    def forward(self, point):
        point = self.backbone(point)
        # unpool to original resolution ...
        feat = point.feat[point.inverse]
        return self.head(feat)
```
