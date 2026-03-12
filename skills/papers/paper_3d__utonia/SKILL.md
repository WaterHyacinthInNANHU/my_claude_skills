---
name: paper_3d__utonia
description: Cross-domain pre-trained Point Transformer V3 encoder for 3D point cloud tasks.
---

# paper_3d__utonia

Unified cross-domain point cloud encoder based on Point Transformer V3. One pretrained model handles indoor, outdoor, object, remote-sensing, and video-lifted point clouds.

## When to Use

- Need a pretrained 3D point cloud encoder for downstream tasks (segmentation, classification, manipulation, VLM grounding)
- Working with diverse point cloud domains and want a single backbone
- Need robust features even when color or normal modalities are missing

## Quick Reference

| Item | Value |
|------|-------|
| Paper | [arXiv:2603.03283](https://arxiv.org/abs/2603.03283) (Mar 2026) |
| Repo | [Pointcept/Utonia](https://github.com/Pointcept/Utonia) |
| Weights | [HuggingFace](https://huggingface.co/Pointcept/Utonia) |
| Homepage | https://pointcept.github.io/Utonia/ |
| License | Code: Apache 2.0, Weights: CC-BY-NC 4.0 |
| Architecture | Point Transformer V3 (encoder-only, ~137M params) |
| Pretraining | Self-distillation on 250k+ cross-domain point clouds + 1M Cap3D objects |
| GPU used for training | 64x NVIDIA H20 |
| Built on | Pointcept, Sonata, Concerto frameworks |

## Key Contributions

1. **First unified encoder** trained jointly across 5 point cloud domains
2. **Causal Modality Blinding** — random per-sample and per-point dropout of color/normal channels; robust to missing modalities
3. **Perceptual Granularity Rescale** — normalizes coordinate systems across domains to shared perceptual scale
4. **3D RoPE** — rotary positional embeddings on granularity-aligned coordinates with jitter+scale augmentation

## Architecture

```
Input Point Cloud (coord, color, normal — any subset)
  │
  ├── Perceptual Granularity Rescale (normalize coord scale across domains)
  ├── Causal Modality Blinding (random dropout of color/normal)
  │
  ▼
Point Transformer V3 + 3D RoPE
  │
  ├── Hierarchical encoder (grid-based pooling, stride=2 per stage)
  ├── Attention with axis-separable RoPE (x, y, z)
  │   └── channels must be divisible by 6
  │
  ▼
Hierarchical Point Features (multi-scale)
```

### Encoder Details (default "utonia" checkpoint)

PTv3 is a **sparse point transformer** — it operates on irregular point sets, NOT fixed grids. Even at the bottleneck, the output is a *set of points with features*, not a single vector.

```
enc_channels = (48, 96, 192, 384, 512)   # but "utonia" ckpt uses 576 at bottleneck
enc_depths   = (3, 3, 3, 12, 3)
enc_num_head = (3, 6, 12, 24, 32)
stride       = (2, 2, 2, 2)              # 4 grid-based pooling stages
```

Example with 4096 input points and manipulation transform (scale=4.0):
```
4096 raw points
  → GridSample(0.01) → ~4096 voxels (few merges at this scale)
  → Stage 0 (C=48):    ~4096 points
  → GridPool stride=2
  → Stage 1 (C=96):    ~4086 points
  → GridPool stride=2
  → Stage 2 (C=192):   ~2452 points
  → GridPool stride=2
  → Stage 3 (C=384):   ~723 points
  → GridPool stride=2
  → Stage 4 (C=576):   ~723 bottleneck points, each (576,)
```

### enc_mode=True (encoder-only)

When loaded with `enc_mode=True`, the decoder (GridUnpooling) is **not constructed**. The forward pass returns bottleneck-level features only:

```python
model = utonia.load("utonia", custom_config=dict(enc_mode=True))
output = model(point)
output.feat   # (N_bottleneck, 576) — NOT full resolution
output.coord  # (N_bottleneck, 3)
```

The output `Point` object contains `pooling_parent` and `pooling_inverse` keys that allow manual unpooling back to voxel resolution (see "Map features back" section below).

### Global feature extraction (for RL policies, classification)

To get a single global vector per point cloud, max-pool over bottleneck points:
```python
feat = output.feat          # (N_bottleneck, 576)
offset = output.offset      # (B,) cumulative point counts
starts = torch.cat([torch.tensor([0]), offset[:-1]])
global_feat = torch.stack([
    feat[starts[i]:offset[i]].max(dim=0)[0]
    for i in range(B)
])  # (B, 576)
```

## Installation

### Standalone (recommended for inference)

```bash
conda env create -f environment.yml --verbose
conda activate utonia
# Requires CUDA 12.4, PyTorch 2.5.0, FlashAttention included
```

### Package mode (integrate into your codebase)

```bash
# Prerequisites: CUDA and PyTorch already installed
pip install spconv-cu${CUDA_VERSION}
pip install torch-scatter -f https://data.pyg.org/whl/torch-{TORCH_VERSION}+cu${CUDA_VERSION}.html
pip install git+https://github.com/Dao-AILab/flash-attention.git
pip install huggingface_hub timm
cd Utonia && python setup.py install
```

### Demo extras

```bash
pip install open3d fast_pytorch_kmeans psutil addict scipy camtools natsort opencv-python trimesh gradio numpy==1.26.4
# NOTE: open3d does not support numpy 2.x
```

## Usage

### Load model

```python
import utonia

# From HuggingFace (auto-downloads to ~/.cache/utonia/ckpt)
model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()

# Alternative
from utonia.model import PointTransformerV3
model = PointTransformerV3.from_pretrained("Pointcept/Utonia").cuda()

# From local checkpoint
model = utonia.model.load("ckpt/utonia.pth").cuda()
```

### Input format

```python
import numpy as np

# Single point cloud
point = {
    "coord":   np.array(...),  # (N, 3) required
    "color":   np.array(...),  # (N, 3) optional
    "normal":  np.array(...),  # (N, 3) optional
    "segment": np.array(...),  # (N,)   optional labels
}

# Batched point clouds — add "batch" key
point["batch"] = np.array(...)  # (N,) batch index per point
```

### Transform and forward pass

```python
# Default transform (adjust scale for resolution)
transform = utonia.transform.default(
    scale=4.0,                 # see scale guide below
    apply_z_positive=True,     # True for indoor/outdoor scenes
    normalize_coord=False,     # True for single objects
)

point = transform(point)
for key in point.keys():
    if isinstance(point[key], torch.Tensor):
        point[key] = point[key].cuda(non_blocking=True)

point = model(point)  # hierarchical features in point.feat
```

### CRITICAL: Transform scale selection

The `scale` parameter controls the effective voxel resolution: `effective_voxel_size = grid_size / scale` (grid_size is always 0.01). This directly determines whether PTv3's hierarchical pooling actually happens.

**The scale must be chosen so that stride-2 grid pooling merges points at each stage.** If scale is too large, no pooling occurs and the multi-scale hierarchy (which PTv3 was pretrained with) is bypassed — features will be degraded.

The `default()` transform pipeline is:
```python
def default(scale=1.0, apply_z_positive=True, normalize_coord=False):
    # 1. NormalizeCoord (optional): center + divide by max radius → coords in [-1, 1]
    # 2. RandomScale([scale, scale]): multiply coords by scale
    # 3. CenterShift(apply_z=True) (optional): shift z so min=0
    # 4. GridSample(grid_size=0.01): voxelize
    # 5. NormalizeColor: divide color by 255
    # 6. ToTensor + Collect
```

**Official demo scales (from Utonia repo):**

| Domain | Scale | NormalizeCoord | Coord range | Effective voxel |
|--------|-------|----------------|-------------|-----------------|
| Indoor (demo 0) | `0.5` | No | meters (~10m) | 20mm |
| **Manipulation (demo 5)** | **`4.0`** | **No** | meters (~1.5m) | 2.5mm |
| Object (demo 6) | `1.0` | No | ~1m | 10mm |

**Common mistake — DO NOT use NormalizeCoord + large scale together:**
- `NormalizeCoord` maps coords to [-1, 1], then `scale=50` maps to [-50, 50]
- Effective voxel = 0.01/50 = 0.2mm → absurdly fine, no points merge
- Result: all points survive all stages, NO hierarchical pooling occurs
- Features are degraded because PTv3 was pretrained with real multi-scale pooling

**Verified example (4096 pts, manipulation workspace ~1.5m):**
```
scale=4.0, no NormalizeCoord → 4096 → 4086 → 2452 → 723 bottleneck ✓ (proper hierarchy)
scale=50 + NormalizeCoord    → 4096 → 4096 → 4096 → 4096 bottleneck ✗ (no pooling!)
```

### Map features back to original resolution

For per-point tasks (segmentation, visualization), unpool from bottleneck back to input resolution:

```python
# Method 1: Concatenation for first 2 levels (richer features, used in official demos)
for _ in range(2):
    parent = point.pop("pooling_parent")
    inverse = point.pop("pooling_inverse")
    parent.feat = torch.cat([parent.feat, point.feat[inverse]], dim=-1)
    point = parent

# Nearest-neighbor for remaining levels
while "pooling_parent" in point.keys():
    parent = point.pop("pooling_parent")
    inverse = point.pop("pooling_inverse")
    parent.feat = point.feat[inverse]
    point = parent

feat = point.feat[point.inverse]  # (N_original, C) features at input resolution
```

```python
# Method 2: Simple nearest-neighbor all the way (simpler, used for visualization)
while "pooling_parent" in point.keys():
    parent = point.pop("pooling_parent")
    inverse = point.pooling_inverse
    parent.feat = point.feat[inverse]
    point = parent
# point.feat is now (N_voxel, 576), point.coord is (N_voxel, 3)
```

### Domain-specific tips

| Domain | Scale | NormalizeCoord | Notes |
|--------|-------|----------------|-------|
| Indoor scenes | `0.5` | No | `apply_z_positive=True`, include `CenterShift` |
| **Robotic manipulation** | **`4.0`** | **No** | Coords in meters, workspace ~1-2m |
| Single objects | `1.0` | No | Or use `normalize_coord=True` with small scale |
| Outdoor LiDAR | `50` | No | Large scenes need fine grid; remove `CenterShift` |
| Missing color/normal | any | — | Model handles gracefully via Causal Modality Blinding |

## Key Results

### Semantic Segmentation (mIoU)

| Dataset | Utonia | Concerto | Domain |
|---------|--------|----------|--------|
| ScanNet | 81.1 | 80.7 | Indoor |
| ScanNet200 | 39.6 | 39.2 | Indoor |
| S3DIS Area 5 | 78.1 | 77.4 | Indoor |
| NuScenes | 82.2 | 82.0 | Outdoor |
| Waymo | 71.4 | 69.2 | Outdoor |
| SemanticKITTI | 72.0 | 71.2 | Outdoor |

### Other tasks

| Task | Dataset | Utonia | Previous Best |
|------|---------|--------|---------------|
| Classification | ModelNet40 | 92.4 mAcc | — |
| Robotic Manipulation | — | 82.1% success | 80.0% (Concerto) |
| Open-world Part Seg | PartObjaverse-Tiny | 57.95 mIoU | 55.57 (Sonata) |
| Spatial QA | ScanQA | 30.5 EM | 29.6 (Concerto) |

## Repo Structure

```
Utonia/
├── demo/                  # 9 visualization/inference demos
│   ├── 0_pca_indoor.py    # PCA vis for indoor scenes
│   ├── 1_similarity.py    # Feature similarity
│   ├── 2_sem_seg.py       # ScanNet linear probe
│   ├── 3_batch_forward.py # Batched inference
│   ├── 8_pca_video.py     # Video lifting (needs VGGT)
│   └── ...
├── utonia/
│   ├── data/              # Data loading (utonia.data.load("sample1"))
│   ├── model/             # PTv3 + loading utilities
│   └── transform/         # Transform pipeline
├── environment.yml        # Conda env (CUDA 12.4, PyTorch 2.5.0)
└── setup.py               # pip-installable package
```

## Related Projects

| Project | Role |
|---------|------|
| [Pointcept](https://github.com/Pointcept/Pointcept) | Base framework for training |
| [Point Transformer V3](https://github.com/Pointcept/PointTransformerV3) | Backbone architecture |
| [Sonata](https://github.com/facebookresearch/sonata) | Pretraining recipe (CVPR 2025) |
| [Concerto](https://pointcept.github.io/Concerto/) | Multi-domain predecessor (NeurIPS 2025) |
| [VGGT](https://github.com/facebookresearch/vggt) | Video-to-pointcloud lifting |
