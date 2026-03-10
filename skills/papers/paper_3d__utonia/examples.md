# Utonia Examples

## 1. Basic Feature Extraction (Single Point Cloud)

```python
import torch
import numpy as np
import utonia

# Load model
model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# Load sample or your own data
point = utonia.data.load("sample1")
# Or:
# point = {"coord": np.load("my_coords.npy"), "color": np.load("my_colors.npy")}

# Transform (indoor scene)
transform = utonia.transform.default(scale=50, apply_z_positive=True, normalize_coord=False)
point = transform(point)
for key in point.keys():
    if isinstance(point[key], torch.Tensor):
        point[key] = point[key].cuda(non_blocking=True)

with torch.no_grad():
    point = model(point)

# Get per-point features at original resolution
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

feat = point.feat[point.inverse]  # (N, C)
print(f"Features shape: {feat.shape}")
```

## 2. Batched Inference

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

transform = utonia.transform.default(scale=50, apply_z_positive=True)
point = transform(point)
for key in point.keys():
    if isinstance(point[key], torch.Tensor):
        point[key] = point[key].cuda(non_blocking=True)

with torch.no_grad():
    point = model(point)
```

## 3. Object-Level Inference (Single Object / CAD Model)

```python
import utonia
import numpy as np

model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# For single objects, use normalize_coord=True
transform = utonia.transform.default(
    scale=50,
    apply_z_positive=True,
    normalize_coord=True,  # Key difference for objects
)

point = {
    "coord": np.load("object_xyz.npy"),
    "normal": np.load("object_normals.npy"),  # color optional
}
# ... transform and forward as above
```

## 4. Outdoor LiDAR Inference

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

## 5. Run Demos

```bash
cd Utonia
export PYTHONPATH=./

# PCA visualization of indoor features
python demo/0_pca_indoor.py

# Feature similarity search
python demo/1_similarity.py

# ScanNet semantic segmentation (linear probe)
python demo/2_sem_seg.py

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

## 6. Fine-tuning with Pointcept

For full fine-tuning on downstream tasks, use the [Pointcept](https://github.com/Pointcept/Pointcept) framework:

```bash
# Clone Pointcept
git clone https://github.com/Pointcept/Pointcept.git
cd Pointcept

# Use Utonia checkpoint as pretrained backbone
# Edit config to point weight to downloaded Utonia checkpoint
# Example: configs/scannet/semseg-pt-v3m1-0-base.py
# Set model.backbone.init_cfg.checkpoint = "path/to/utonia.pth"
```

## 7. Integration Pattern for Custom Projects

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
        self.head = nn.Linear(512, num_classes)  # adjust feat dim

    def forward(self, point):
        point = self.backbone(point)
        # unpool to original resolution ...
        feat = point.feat[point.inverse]
        return self.head(feat)
```
