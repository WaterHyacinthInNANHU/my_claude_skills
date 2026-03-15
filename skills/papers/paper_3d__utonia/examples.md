# Utonia Examples

Practical recipes for using Utonia's pre-trained PTv3 encoder. All code patterns are derived from the actual repo code.

## 1. Basic Feature Extraction (Indoor Scene)

```python
import torch
import numpy as np
import utonia

# Load model
model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# Load sample indoor data
point = utonia.data.load("sample1")
point.pop("segment200")
segment = point.pop("segment20")
point["segment"] = segment

# Transform: scale=0.5 for indoor scenes (from demo/0_pca_indoor.py)
transform = utonia.transform.default(scale=0.5)
original_coord = point["coord"].copy()
point = transform(point)

# Inference
with torch.inference_mode():
    for key in point.keys():
        if isinstance(point[key], torch.Tensor):
            point[key] = point[key].cuda(non_blocking=True)
    point = model(point)

    # Unpool: concat first 2 levels for richer features, nearest-neighbor copy for rest
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

    # Map features to original (pre-GridSample) resolution
    feat_original = point.feat[point.inverse]
    # feat_original: (N, 336) -- 48+96+192 from 2-level concat unpooling
    print(f"Features shape: {feat_original.shape}")
```

## 2. Frozen Encoder for Robotic Manipulation (RL Integration)

```python
import torch
import numpy as np
import utonia

# Load model and freeze all parameters
model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()
for p in model.parameters():
    p.requires_grad = False

# Manipulation transform: scale=4.0 (from demo/5_pca_manipulation.py)
transform = utonia.transform.default(scale=4.0)

def extract_global_feature(coord, color=None, normal=None):
    """Extract a single global feature vector from a manipulation scene.

    Args:
        coord: (N, 3) numpy array, XYZ in meters
        color: (N, 3) numpy array, RGB in [0,255], or None (zeros used)
        normal: (N, 3) numpy array, or None (zeros used)
    Returns:
        global_feat: (512,) tensor on CUDA
    """
    point = {
        "coord": coord.astype(np.float32),
        "color": (color if color is not None else np.zeros_like(coord)).astype(np.float32),
        "normal": (normal if normal is not None else np.zeros_like(coord)).astype(np.float32),
    }
    point = transform(point)
    with torch.inference_mode():
        for key in point.keys():
            if isinstance(point[key], torch.Tensor):
                point[key] = point[key].cuda(non_blocking=True)
        point = model(point)
        # point.feat is (M', 512) at deepest encoder stage
        global_feat = point.feat.max(dim=0).values  # (512,)
    return global_feat

# Example usage
N = 5000
coord = np.random.randn(N, 3).astype(np.float32) * 0.1  # ~10cm workspace
feat = extract_global_feature(coord)
print(f"Global feature shape: {feat.shape}")  # (512,)
```

## 3. Batched Inference

```python
import copy
import torch
import utonia

model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

transform = utonia.transform.default(scale=0.5)

# Load and transform two point clouds independently
point1 = utonia.data.load("sample1")
point1.pop("segment200"); point1["segment"] = point1.pop("segment20")
point2 = copy.deepcopy(point1)

point1 = transform(point1)
point2 = transform(point2)

# Collate into a batch using utonia's collate_fn (handles offset-based batching)
batch = utonia.data.collate_fn([point1, point2])

with torch.inference_mode():
    for key in batch.keys():
        if isinstance(batch[key], torch.Tensor):
            batch[key] = batch[key].cuda(non_blocking=True)
    result = model(batch)
    # result.batch: per-point batch indices (0 or 1)
    # result.offset: cumulative counts, e.g. tensor([M1, M1+M2])
    print(f"Total points: {result.feat.shape[0]}, Batches: {result.batch.unique().tolist()}")
```

## 4. Object-Level Inference

For single objects (CAD models, ShapeNet), use the default scale and estimate normals if needed:

```python
import torch
import numpy as np
import open3d as o3d
import utonia

model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# Load object data (from demo/6_pca_object.py)
point = utonia.data.load("sample3_object")

# Estimate normals with Open3D if not available
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(point["coord"])
pcd.colors = o3d.utility.Vector3dVector(point["color"])
pcd.estimate_normals()
point["normal"] = np.asarray(pcd.normals)

# Object transform: scale=1.0 (default from demo/6_pca_object.py)
# For normalized objects, you can also use: default(scale=1.0, normalize_coord=True)
transform = utonia.transform.default()
point = transform(point)

with torch.inference_mode():
    for key in point.keys():
        if isinstance(point[key], torch.Tensor):
            point[key] = point[key].cuda(non_blocking=True)
    point = model(point)
    # Global object feature via max-pool
    obj_feat = point.feat.max(dim=0).values  # (512,)
    print(f"Object feature: {obj_feat.shape}")
```

## 5. Outdoor LiDAR

```python
import torch
import numpy as np
import utonia

model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# Outdoor LiDAR: scale=0.2, apply_z_positive=False (from demo/7_pca_outdoor.py)
# Keep ego-vehicle at origin, road on xy-plane
transform = utonia.transform.default(scale=0.2, apply_z_positive=False)

point = utonia.data.load("sample2_outdoor_multiframe")
original_coord = point["coord"].copy()
point = transform(point)

with torch.inference_mode():
    for key in point.keys():
        if isinstance(point[key], torch.Tensor):
            point[key] = point[key].cuda(non_blocking=True)
    point = model(point)

    # Unpool to full resolution
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

    feat = point.feat[point.inverse]
    print(f"Outdoor features: {feat.shape}")  # (N, 336)
```

## 6. PCA Visualization

The official PCA visualization method used across all demos:

```python
import torch
import numpy as np
import utonia

def get_pca_color(feat, brightness=1.25, center=True):
    """Convert high-dim features to RGB via PCA (from demo/0_pca_indoor.py)."""
    u, s, v = torch.pca_lowrank(feat, center=center, q=6, niter=5)
    projection = feat @ v
    projection = projection[:, :3] * 0.6 + projection[:, 3:6] * 0.4
    min_val = projection.min(dim=-2, keepdim=True)[0]
    max_val = projection.max(dim=-2, keepdim=True)[0]
    div = torch.clamp(max_val - min_val, min=1e-6)
    color = (projection - min_val) / div * brightness
    return color.clamp(0.0, 1.0)

utonia.utils.set_seed(37)  # PCA colors are seed-dependent
model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

transform = utonia.transform.default(scale=0.5)
point = utonia.data.load("sample1")
point.pop("segment200"); point["segment"] = point.pop("segment20")
original_coord = point["coord"].copy()
point = transform(point)

with torch.inference_mode():
    for key in point.keys():
        if isinstance(point[key], torch.Tensor):
            point[key] = point[key].cuda(non_blocking=True)
    point = model(point)
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

    pca_color = get_pca_color(point.feat, brightness=1.2)

# Map back to original scale
original_pca = pca_color[point.inverse]  # (N, 3) RGB in [0,1]

# Save as PLY with Open3D:
import open3d as o3d
pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(original_coord)
pcd.colors = o3d.utility.Vector3dVector(original_pca.cpu().numpy())
o3d.io.write_point_cloud("pca.ply", pcd)
```

## 7. Running Official Demos

```bash
cd Utonia
export PYTHONPATH=./

# Indoor PCA (scale=0.5)
python demo/0_pca_indoor.py

# Similarity heatmap
python demo/1_similarity.py

# Semantic segmentation with linear probe head
python demo/2_sem_seg.py

# Batched forward
python demo/3_batch_forward.py

# Hong Kong scene (scale=0.5)
python demo/4_pca_hk.py

# Manipulation scene (scale=4.0)
python demo/5_pca_manipulation.py

# Object PCA (scale=1.0)
python demo/6_pca_object.py

# Outdoor LiDAR (scale=0.2, no CenterShift)
python demo/7_pca_outdoor.py

# Video (requires VGGT installed separately)
python demo/8_pca_video.py --input_video path/to/video.mp4

# Disable color/normal modalities:
python demo/0_pca_indoor.py --wo_color --wo_normal
```

## 8. Fine-tuning with Pointcept

Utonia's inference repo does not include training code. For fine-tuning, use the full Pointcept framework:

```bash
git clone https://github.com/Pointcept/Pointcept.git
cd Pointcept
# Follow Pointcept installation instructions

# Download Utonia checkpoint to cache
python -c "import utonia; utonia.model.load('utonia')"
# Checkpoint is now at ~/.cache/utonia/ckpt/utonia.pth

# In your Pointcept config, load PTv3 backbone with Utonia weights:
# model:
#   type: PointTransformerV3
#   in_channels: 6
#   enc_channels: [48, 96, 192, 384, 512]
#   enc_depths: [3, 3, 3, 12, 3]
#   enc_num_head: [3, 6, 12, 24, 32]
#   ...
#   weight: ~/.cache/utonia/ckpt/utonia.pth
```

## 9. Integration Pattern for Custom Projects

```python
"""
Minimal integration of Utonia encoder into a custom project.
No need to clone the full repo -- just pip install or copy utonia/ folder.
"""
import torch
import torch.nn as nn
import numpy as np
import utonia

class MyModel(nn.Module):
    def __init__(self, num_classes=20):
        super().__init__()
        # Load pre-trained encoder
        self.encoder = utonia.model.load("utonia", repo_id="Pointcept/Utonia")
        self.encoder.eval()
        # Freeze encoder
        for p in self.encoder.parameters():
            p.requires_grad = False
        # Task head: 336-dim after 2-level concat unpool
        self.head = nn.Linear(336, num_classes)

    def _unpool(self, point):
        """Unpool with 2-level concat + remaining nearest-neighbor copy."""
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
        return point

    def forward(self, data_dict):
        with torch.no_grad():
            point = self.encoder(data_dict)
            point = self._unpool(point)
        logits = self.head(point.feat)  # (M, num_classes) at voxel resolution
        return logits, point

# Usage
model = MyModel(num_classes=20).cuda()
transform = utonia.transform.default(scale=0.5)

raw_point = {
    "coord": np.random.randn(10000, 3).astype(np.float32),
    "color": np.random.randint(0, 256, (10000, 3)).astype(np.float32),
    "normal": np.zeros((10000, 3), dtype=np.float32),
}
data = transform(raw_point)
for k in data:
    if isinstance(data[k], torch.Tensor):
        data[k] = data[k].cuda()

logits, point = model(data)
print(f"Logits shape: {logits.shape}")  # (M, 20) at grid-sampled resolution
# Map back to original resolution: logits_orig = logits[point.inverse]
```

## 10. Semantic Segmentation with Linear Probe Head

Using the pre-trained linear probe head for ScanNet 20-class segmentation (from demo/2_sem_seg.py):

```python
import torch
import torch.nn as nn
import numpy as np
import utonia

# Load encoder
model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# Load pre-trained linear probe head checkpoint (returns raw dict)
ckpt = utonia.model.load("utonia_linear_prob_head_sc", repo_id="Pointcept/Utonia", ckpt_only=True)

class SegHead(nn.Module):
    def __init__(self, backbone_out_channels, num_classes):
        super().__init__()
        self.seg_head = nn.Linear(backbone_out_channels, num_classes)
    def forward(self, x):
        return self.seg_head(x)

seg_head = SegHead(**ckpt["config"]).cuda()
seg_head.load_state_dict(ckpt["state_dict"])
seg_head.eval()

# Run
transform = utonia.transform.default(scale=0.5)
point = utonia.data.load("sample1")
point.pop("segment200"); point["segment"] = point.pop("segment20")
point = transform(point)

with torch.inference_mode():
    for key in point.keys():
        if isinstance(point[key], torch.Tensor):
            point[key] = point[key].cuda(non_blocking=True)
    point = model(point)

    # Full unpool with concat at all levels (seg head expects this dim)
    while "pooling_parent" in point.keys():
        parent = point.pop("pooling_parent")
        inverse = point.pop("pooling_inverse")
        parent.feat = torch.cat([parent.feat, point.feat[inverse]], dim=-1)
        point = parent

    seg_logits = seg_head(point.feat)
    pred = seg_logits.argmax(dim=-1)  # (M,) per-voxel class predictions
    print(f"Predictions: {pred.shape}, unique classes: {pred.unique().shape[0]}")
```

## 11. Custom Data from PLY Files

```python
import numpy as np
import open3d as o3d
import torch
import utonia

# Load from PLY
pcd = o3d.io.read_point_cloud("my_scene.ply")
coords = np.asarray(pcd.points).astype(np.float32)
colors = (np.asarray(pcd.colors) * 255).astype(np.float32)  # must be [0, 255]

# Estimate normals if not in the PLY
pcd.estimate_normals()
normals = np.asarray(pcd.normals).astype(np.float32)

point = {"coord": coords, "color": colors, "normal": normals}

# Choose transform based on your domain:
# Indoor room: scale=0.5
# Manipulation: scale=4.0
# Outdoor LiDAR: scale=0.2, apply_z_positive=False
# Object: scale=1.0, normalize_coord=True
transform = utonia.transform.default(scale=0.5)
point = transform(point)

model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

with torch.inference_mode():
    for key in point.keys():
        if isinstance(point[key], torch.Tensor):
            point[key] = point[key].cuda(non_blocking=True)
    point = model(point)
    # unpool as needed (see examples 1, 5, 6 above)
```

## 12. Without FlashAttention

```python
import utonia

# Override config to disable flash_attn
custom_config = dict(
    enc_patch_size=[1024, 1024, 1024, 1024, 1024],  # can reduce to [512]*5 for less memory
    enable_flash=False,
)
model = utonia.model.load(
    "utonia", repo_id="Pointcept/Utonia",
    custom_config=custom_config,
).cuda()
model.eval()

# Everything else (transform, forward, unpool) is identical
```
