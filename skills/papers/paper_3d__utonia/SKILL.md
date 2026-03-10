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
  ├── Hierarchical encoder (grid-based pooling)
  ├── Attention with axis-separable RoPE (x, y, z)
  │   └── channels must be divisible by 6
  │
  ▼
Hierarchical Point Features (multi-scale)
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
    scale=50,                  # larger = finer grid
    apply_z_positive=True,     # True for indoor/outdoor scenes
    normalize_coord=False,     # True for single objects
)

point = transform(point)
for key in point.keys():
    if isinstance(point[key], torch.Tensor):
        point[key] = point[key].cuda(non_blocking=True)

point = model(point)  # hierarchical features in point.feat
```

### Map features back to original resolution

```python
# Unpool 2 levels with concatenation (for downstream heads)
for _ in range(2):
    parent = point.pop("pooling_parent")
    inverse = point.pop("pooling_inverse")
    parent.feat = torch.cat([parent.feat, point.feat[inverse]], dim=-1)
    point = parent

# Unpool remaining levels (nearest neighbor)
while "pooling_parent" in point.keys():
    parent = point.pop("pooling_parent")
    inverse = point.pop("pooling_inverse")
    parent.feat = point.feat[inverse]
    point = parent

feat = point.feat[point.inverse]  # (N_original, C) features at input resolution
```

### Domain-specific tips

| Domain | Transform Notes |
|--------|----------------|
| Indoor scenes | `apply_z_positive=True`, `normalize_coord=False`, include `CenterShift` |
| Outdoor LiDAR | Remove `CenterShift`, ego-vehicle at origin, road aligned to xy-plane |
| Single objects | `normalize_coord=True` |
| Missing color/normal | Model handles gracefully; pass `--wo_color --wo_normal` in demos |

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
