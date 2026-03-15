---
name: paper_3d__utonia
description: Utonia - unified cross-domain point cloud encoder (PTv3-based, self-supervised, 5 domains)
---

# paper_3d__utonia

Utonia trains a single self-supervised Point Transformer V3 (PTv3) encoder across five diverse point cloud domains (remote sensing, outdoor LiDAR, indoor RGB-D, object CAD, RGB-video-lifted), producing universal 3D representations that transfer to segmentation, robotic manipulation, and multimodal reasoning.

## Paper Info

| Field | Value |
|-------|-------|
| Title | Utonia: Toward One Encoder for All Point Clouds |
| Authors | Yujia Zhang, Xiaoyang Wu et al. |
| Year | 2026 |
| Venue | arXiv (cs.CV) |
| Paper | https://arxiv.org/abs/2603.03283 |
| Code | https://github.com/Pointcept/Utonia |
| Weights | https://huggingface.co/Pointcept/Utonia (model), https://huggingface.co/datasets/pointcept/demo (sample data) |

## Method Overview

Utonia is a cross-domain pre-trained PTv3 encoder that harmonizes point clouds with distinct sensing geometries, densities, and modality priors. The pipeline is:

1. **Data preparation**: Raw point clouds (coord, color, normal) are normalized and grid-sampled at 0.01m resolution. A domain-dependent **scale** parameter controls Perceptual Granularity Rescale -- the key mechanism for unifying different point cloud densities.
2. **Serialization**: Grid coordinates are serialized via z-order or Hilbert curves to create 1D sequences for efficient attention.
3. **Encoder**: A 5-stage hierarchical PTv3 with serialized patch attention, 3D RoPE positional encoding, and sparse convolution CPE. Stages are connected by GridPooling (stride-2 downsampling).
4. **Output**: The encoder produces a hierarchical `Point` object; features can be unpooled back to the original resolution via `pooling_inverse` and `pooling_parent` chains.

Key insight: A single encoder can learn universal 3D representations across wildly different domains by rescaling point cloud granularity through a per-domain scale factor applied before grid sampling.

## Scale / Domain Table (CRITICAL)

The `scale` parameter in the transform pipeline controls the effective voxel resolution. Choosing the right scale per domain is essential:

| Domain | scale | `apply_z_positive` | `normalize_coord` | Notes |
|--------|-------|--------------------|--------------------|-------|
| Indoor scene (ScanNet) | 0.5 | True | False | Default for rooms |
| Robotic manipulation | 4.0 | True | False | Tabletop scenes need finer grain |
| Outdoor LiDAR | 0.2 | **False** | False | Keep ego at origin, road on xy-plane |
| Object-centric (CAD) | 1.0 (default) | True | **True** | Enable NormalizeCoord for objects |
| Hong Kong scene | 0.5 | True | False | Similar to indoor |

## Paper-Code Mapping

| Paper Concept | Code Location | Notes |
|---------------|---------------|-------|
| PTv3 Encoder | `utonia/model.py:PointTransformerV3` | Main model class, also `PyTorchModelHubMixin` |
| 3D RoPE | `utonia/model.py:Point3DRoPE` | Splits head_dim into 3 chunks for x,y,z rotation; head_dim must be divisible by 3 |
| Serialized Attention | `utonia/model.py:SerializedAttention` | Patch-based attention with flash_attn varlen support |
| Transformer Block | `utonia/model.py:Block` | CPE (SubMConv3d) + SerializedAttention + MLP with DropPath |
| Grid Pooling (downsampling) | `utonia/model.py:GridPooling` | stride-2, max-reduce, traceable for unpooling |
| Grid Unpooling | `utonia/model.py:GridUnpooling` | Skip-connection based upsampling (decoder only) |
| Embedding | `utonia/model.py:Embedding` | Linear(in_channels -> enc_channels[0]) + LN + GELU, optional mask token |
| Point data structure | `utonia/structure.py:Point` | `addict.Dict` subclass with `serialization()` and `sparsify()` methods |
| Serialization (z-order, Hilbert) | `utonia/serialization/default.py:encode` | Orders: "z", "z-trans", "hilbert", "hilbert-trans" |
| Perceptual Granularity Rescale | `utonia/transform.py:RandomScale` + `GridSample` | scale param controls effective resolution |
| Transform pipeline | `utonia/transform.py:Compose`, `default()` | Configurable transform chain via Registry |
| Data loading | `utonia/data.py:load` | Loads sample .npz from HuggingFace `pointcept/demo` |
| Batch collation | `utonia/data.py:collate_fn` | Handles offset-based batching for variable-size point clouds |
| Model loading | `utonia/model.py:load` | Downloads from HuggingFace `Pointcept/Utonia`, builds model from stored config |
| Linear probe head | `demo/2_sem_seg.py:SegHead` | Simple `nn.Linear` for ScanNet 20-class segmentation |
| RPE (relative pos enc) | `utonia/model.py:RPE` | Table-based RPE (disabled when flash_attn enabled) |
| LayerScale | `utonia/model.py:LayerScale` | Per-channel learnable scaling (optional, controlled by `layer_scale` param) |

## Setup

### Dependencies

- Python 3.10+
- PyTorch 2.5.0+ with CUDA 12.4+
- FlashAttention (strongly recommended, required for default config)
- Key packages: `spconv-cu124`, `torch-scatter`, `flash-attn`, `huggingface_hub`, `timm`, `addict`, `scipy`
- Demo extras: `open3d` (requires numpy<=1.26.4), `fast_pytorch_kmeans`, `psutil`, `camtools`, `trimesh`, `gradio`, `natsort`, `opencv-python`

### Installation

**Standalone mode** (conda env with everything):
```bash
git clone https://github.com/Pointcept/Utonia.git
cd Utonia

# unset CUDA_PATH if you have local CUDA installed
conda env create -f environment.yml --verbose
conda activate utonia
```

**Package mode** (inject into existing env):
```bash
# CUDA_VERSION e.g. 124, TORCH_VERSION e.g. 2.5.0
pip install spconv-cu${CUDA_VERSION}
pip install torch-scatter -f https://data.pyg.org/whl/torch-${TORCH_VERSION}+cu${CUDA_VERSION}.html
pip install git+https://github.com/Dao-AILab/flash-attention.git
pip install huggingface_hub timm addict scipy

# Install utonia as a package (or just copy utonia/ folder to your project)
cd Utonia
python setup.py install
```

### Pre-trained Weights

Weights are auto-downloaded from HuggingFace on first `utonia.model.load()` call.

Available models on `Pointcept/Utonia`:
- `utonia.pth` -- main encoder (enc_mode=True, encoder-only PTv3)
- `utonia_linear_prob_head_sc.pth` -- linear probe segmentation head for ScanNet 20-class

Cache location: `~/.cache/utonia/ckpt` (customizable via `download_root` param).

## Usage Scenarios

### Scenario 1: Feature Extraction (Indoor Scene)
```bash
export PYTHONPATH=./
python demo/0_pca_indoor.py
# With --wo_color or --wo_normal to test modality ablation
```

### Scenario 2: Semantic Segmentation (Linear Probe)
```bash
python demo/2_sem_seg.py
```

### Scenario 3: Batched Inference
```bash
python demo/3_batch_forward.py
```

### Scenario 4: Outdoor LiDAR
```bash
python demo/7_pca_outdoor.py
```

### Scenario 5: Object-level
```bash
python demo/6_pca_object.py
```

### Scenario 6: Robotic Manipulation
```bash
python demo/5_pca_manipulation.py
```

### Scenario 7: Video-lifted Point Clouds (requires VGGT)
```bash
git clone https://github.com/facebookresearch/vggt.git && cd vggt && pip install -e . && cd ..
python demo/8_pca_video.py --input_video ${VIDEO_PATH} --conf_thres 0 \
  --prediction_mode "Depthmap and Camera Branch" --if_TSDF --pca_start 1 --pca_brightness 1.2
```

### Key Config Flags

| Flag / Param | Default | Description |
|------|---------|-------------|
| `enc_mode` | True (in checkpoint) | Encoder-only mode (no decoder); always True for Utonia weights |
| `enable_flash` | True | Use FlashAttention; set False if flash_attn not installed |
| `enc_patch_size` | (1024,1024,1024,1024,1024) | Patch size per stage; reduce if OOM |
| `in_channels` | 6 | Input feature dim (set by checkpoint config) |
| `freeze_encoder` | False | Freeze embedding+encoder params for downstream fine-tuning |
| `scale` (transform) | 1.0 | **Domain-dependent** granularity rescale factor |
| `apply_z_positive` (transform) | True | CenterShift; set False for outdoor LiDAR |
| `normalize_coord` (transform) | False | NormalizeCoord; set True for object-centric data |
| `custom_config` (load) | None | Dict to override any checkpoint config key |
| `ckpt_only` (load) | False | Return raw checkpoint dict instead of model |
| `--wo_color` | False | Zero out color input (demo scripts) |
| `--wo_normal` | False | Zero out normal input (demo scripts) |

## Code Integration Guide

### Minimal Imports

```python
import utonia
# or individually:
from utonia.model import PointTransformerV3, load
from utonia.transform import Compose, default
from utonia.data import collate_fn
from utonia.structure import Point
from utonia.utils import offset2batch, batch2offset, offset2bincount, set_seed
```

### Model Instantiation & Inference

```python
import torch
import utonia

# Load pre-trained encoder from HuggingFace
model = utonia.model.load("utonia", repo_id="Pointcept/Utonia").cuda()
model.eval()

# Alternative: HuggingFace Hub API
# from utonia.model import PointTransformerV3
# model = PointTransformerV3.from_pretrained("Pointcept/Utonia").cuda()

# Without flash_attn:
model = utonia.model.load("utonia", repo_id="Pointcept/Utonia",
    custom_config=dict(enable_flash=False, enc_patch_size=[1024]*5)).cuda()

# From local checkpoint:
model = utonia.model.load("path/to/utonia.pth").cuda()

# Inspect checkpoint config:
ckpt = utonia.model.load("utonia", ckpt_only=True)
print(ckpt["config"])  # dict with all PointTransformerV3 constructor args
```

### Data Format

**Input** (before transform): a dict with numpy arrays.

| Field | Shape / Type | Description |
|-------|-------------|-------------|
| `coord` | `(N, 3)` float | XYZ coordinates in meters (required) |
| `color` | `(N, 3)` float | RGB values in [0, 255]; use zeros if unavailable |
| `normal` | `(N, 3)` float | Surface normals; use zeros if unavailable |
| `segment` | `(N,)` int | Optional ground-truth labels |
| `batch` | `(N,)` int | Optional batch index per point (for pre-batched data) |

**Input** (after transform, ready for model): a dict with torch tensors.

| Field | Shape / Type | Description |
|-------|-------------|-------------|
| `coord` | `(M, 3)` float32 | Grid-sampled, scaled coordinates |
| `grid_coord` | `(M, 3)` int32 | Integer grid coordinates for serialization/sparsification |
| `color` | `(M, 3)` float32 | Normalized to [0, 1] (via NormalizeColor) |
| `feat` | `(M, D)` float32 | Concatenation of feat_keys, e.g. [coord, color, normal] -> D=9 |
| `offset` | `(1,)` int64 | Cumulative point count per sample |
| `inverse` | `(N,)` int64 | Maps original points to grid-sampled points (for upsampling back) |

**Output**: a `Point` object (subclass of `addict.Dict`).

| Field | Shape / Type | Description |
|-------|-------------|-------------|
| `point.feat` | `(M', D_enc)` float32 | Encoded features at deepest encoder stage (D_enc=512) |
| `point.coord` | `(M', 3)` float32 | Coordinates at deepest stage |
| `point.offset` | `(B,)` int64 | Batch offsets |
| `point.batch` | `(M',)` int64 | Batch index per point |
| `point.pooling_parent` | `Point` | Parent point cloud from previous (higher-res) stage |
| `point.pooling_inverse` | `(M',)` int64 | Maps each deepest-stage point to its parent |

Default encoder channel dims per stage: `enc_channels=(48, 96, 192, 384, 512)`.

### Feature Unpooling (CRITICAL)

The encoder output is at the deepest (most downsampled) stage. To recover features at higher resolutions:

```python
# Unpool with concatenation (first K levels for richer features)
for _ in range(K):  # K=2 for visualization, K=4 for full unpool
    parent = point.pop("pooling_parent")
    inverse = point.pop("pooling_inverse")
    parent.feat = torch.cat([parent.feat, point.feat[inverse]], dim=-1)
    point = parent

# Unpool remaining levels with simple nearest-neighbor copy
while "pooling_parent" in point.keys():
    parent = point.pop("pooling_parent")
    inverse = point.pop("pooling_inverse")
    parent.feat = point.feat[inverse]
    point = parent

# Map back to original (pre-GridSample) resolution
feat_original = point.feat[point.inverse]  # (N, D) at original point count
```

Feature dims after concat-unpooling:
- K=2: 48 + 96 + 192 = 336 (stage0_feat + stage1_upcast + stage2_upcast)
- K=4 (all stages): 48 + 96 + 192 + 384 + 512 = 1232

### Global Feature Extraction (for RL, classification)

For tasks needing a single feature vector per point cloud:

```python
# After model forward (before unpooling), max-pool over deepest features
point = model(data_dict)
# point.feat is (M', 512) at deepest stage

# Simple max-pool for single sample:
global_feat = point.feat.max(dim=0).values  # (512,)

# Batched max-pool using offset:
from utonia.utils import offset2bincount
import torch_scatter
bincount = offset2bincount(point.offset)
idx_ptr = torch.cat([bincount.new_zeros(1), torch.cumsum(bincount, dim=0)])
_, indices = torch.sort(torch.arange(point.feat.shape[0], device=point.feat.device))
global_feat = torch_scatter.segment_csr(point.feat[indices], idx_ptr, reduce="max")
# global_feat: (B, 512)
```

### Integration Notes

- The `utonia` package is self-contained (no dependency on full Pointcept). Just copy the `utonia/` folder or `pip install` via setup.py.
- `feat_keys=("coord", "color", "normal")` in the `Collect` transform concatenates these into the `feat` tensor (9-dim). The model's `in_channels` in the checkpoint config determines what the embedding layer expects.
- When color or normal is absent, **fill with zeros** (same shape as coord). Do NOT omit the key.
- The model uses `spconv.SubMConv3d` for the convolutional position encoding (CPE). This is handled internally by `Point.sparsify()`.
- FlashAttention is strongly recommended. Without it, set `enable_flash=False` via `custom_config` and optionally reduce `enc_patch_size`.
- The `Point` class inherits from `addict.Dict` -- attribute access works like dict access (`point.feat` == `point["feat"]`).
- `GridPooling` sets `traceable=True` by default, which stores `pooling_parent` and `pooling_inverse` for unpooling.

## Core Architecture

```
Input dict {coord, color, normal}
    |
    v
[Embedding] Linear(in_channels -> 48) + LN + GELU
    |
    v
[Serialization] z-order / z-trans curve encoding
[Sparsify] -> SparseConvTensor for CPE
    |
    v
+-- Enc Stage 0: 3x Block(48, heads=3, patch=1024) ----> pooling_parent chain
    |  Block = CPE(SubMConv3d) + SerializedAttention(3D_RoPE) + MLP(ratio=4)
    v
[GridPooling stride=2, max-reduce] 48 -> 96
    |
+-- Enc Stage 1: 3x Block(96, heads=6) ----> pooling_parent chain
    v
[GridPooling stride=2] 96 -> 192
    |
+-- Enc Stage 2: 3x Block(192, heads=12) ----> pooling_parent chain
    v
[GridPooling stride=2] 192 -> 384
    |
+-- Enc Stage 3: 12x Block(384, heads=24) ----> pooling_parent chain
    v
[GridPooling stride=2] 384 -> 512
    |
+-- Enc Stage 4: 3x Block(512, heads=32)
    |
    v
Output: Point with feat(512), pooling_parent/pooling_inverse chain
        (enc_mode=True: no decoder, manual unpool via chain)
```

## Repo Structure

| Path | Purpose |
|------|---------|
| `utonia/__init__.py` | Package init; exports `load` and all submodules |
| `utonia/model.py` | `PointTransformerV3`, `load()`, `Point3DRoPE`, `SerializedAttention`, `Block`, `GridPooling`, `GridUnpooling`, `Embedding` |
| `utonia/module.py` | `PointModule`, `PointSequential` -- base classes for Point-aware nn.Module dispatch |
| `utonia/structure.py` | `Point` class (addict.Dict subclass) with `serialization()` and `sparsify()` |
| `utonia/transform.py` | All transforms (`GridSample`, `RandomScale`, `NormalizeColor`, `NormalizeCoord`, `CenterShift`, `Collect`, `ToTensor`, etc.), `Compose`, `default()` |
| `utonia/data.py` | `load()` for sample data from HuggingFace (`pointcept/demo`), `collate_fn()` for offset-based batching |
| `utonia/utils.py` | `offset2batch`, `batch2offset`, `offset2bincount`, `set_seed` |
| `utonia/registry.py` | OpenMMLab-style `Registry` for building transforms from config dicts |
| `utonia/serialization/` | Z-order (`z_order.py`) and Hilbert (`hilbert.py`) curve encoding/decoding; `default.py` dispatches by order name |
| `demo/0_pca_indoor.py` | PCA visualization on indoor ScanNet scene (scale=0.5) |
| `demo/1_similarity.py` | Similarity heatmap visualization |
| `demo/2_sem_seg.py` | Semantic segmentation with `utonia_linear_prob_head_sc` linear probe |
| `demo/3_batch_forward.py` | Batched inference example using `utonia.data.collate_fn` |
| `demo/4_pca_hk.py` | PCA on Hong Kong outdoor scene |
| `demo/5_pca_manipulation.py` | PCA on robotic manipulation scene (scale=4.0) |
| `demo/6_pca_object.py` | PCA on object-centric data with estimated normals |
| `demo/7_pca_outdoor.py` | PCA on outdoor LiDAR (scale=0.2, apply_z_positive=False) |
| `demo/8_pca_video.py` | PCA on video-lifted point clouds (requires VGGT) |
| `demo/visual_util.py` | Visualization utilities |
| `setup.py` | Package installation (name="utonia", version="1.0") |
| `environment.yml` | Conda env spec (Python 3.10, PyTorch 2.5.0, CUDA 12.4) |

## Tips & Gotchas

- **Scale is the most important hyperparameter**. Wrong scale = garbage features. See the Scale / Domain Table above. Indoor=0.5, manipulation=4.0, outdoor=0.2, object=1.0.
- **Outdoor LiDAR**: Must set `apply_z_positive=False` so CenterShift is skipped. Ensure ego-vehicle is at origin with road on xy-plane.
- **Object data**: Set `normalize_coord=True` to enable `NormalizeCoord` transform (centers and normalizes to unit sphere).
- **Missing modalities**: When color or normal is unavailable, pass `np.zeros_like(coord)`. Do NOT omit the key from the dict. The model was trained with Causal Modality Blinding and handles missing inputs gracefully.
- **FlashAttention required by default**: The checkpoint config has `enable_flash=True`. If flash_attn is not installed, pass `custom_config=dict(enable_flash=False)` to `load()`.
- **Memory**: Large scenes can OOM. Reduce `enc_patch_size` (e.g., `[512]*5` or `[256]*5`) to lower memory usage at the cost of attention window size.
- **Unpooling depth matters**: Use `range(2)` concat + remaining copy for visualization. Use `range(4)` concat for quantitative evaluation (all skip features concatenated). The `demo/2_sem_seg.py` uses full concat (`while` loop with concat at every level).
- **Feature dims after unpool**: Concat over K=2 stages gives 48+96+192=336 dims. Full K=4 gives 48+96+192+384+512=1232 dims.
- **Grid size**: Fixed at 0.01m in the default transform. Changing this is not recommended without retraining.
- **Batch collation**: Use `utonia.data.collate_fn()` for batching multiple transformed point clouds. It handles offset-based batching correctly (concatenates coords, builds cumulative offset). Do NOT use PyTorch default collation.
- **Weights license**: CC-BY-NC 4.0 (non-commercial due to HM3D/ArkitScenes dataset restrictions). Code is Apache 2.0.
- **Fine-tuning**: This repo is inference-only. For training/fine-tuning, use the full [Pointcept](https://github.com/Pointcept/Pointcept) codebase with Utonia weights as initialization.
- **`enc_mode=True`**: The Utonia checkpoint is encoder-only. The decoder path in `PointTransformerV3` exists in code but is not used. All feature recovery is done via manual unpooling with `pooling_parent`/`pooling_inverse`.
- **3D RoPE constraint**: `head_dim = channels // num_heads` must be divisible by 3. This is enforced by assertion in `Point3DRoPE.__init__`.
- **Serialization orders**: Default is `("z", "z-trans")`. Blocks alternate between orders via `order_index = i % len(self.order)`.
- **`drop_path`**: Default 0.3 stochastic depth, linearly increasing across encoder depth.
- **`rope_base`**: Default 10 (not the typical 10000 used in NLP RoPE).
