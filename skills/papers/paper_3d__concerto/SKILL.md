# Concerto — Joint 2D-3D Self-Supervised Learning for Spatial Representations

TRIGGER: When the user mentions Concerto, joint 2D-3D self-supervised learning, PTv3-based pre-training for 3D scene understanding, or point cloud encoders for indoor scenes (especially in the context of DP3/robotic manipulation).

## Quick Reference

| Field | Value |
|-------|-------|
| Paper | [Concerto: Joint 2D-3D Self-Supervised Learning Emerges Spatial Representations](https://arxiv.org/abs/2510.23607) |
| Authors | Yujia Zhang, Xiaoyang Wu, Yixing Lao, Chengyao Wang, Zhuotao Tian, Naiyan Wang, Hengshuang Zhao |
| Venue | NeurIPS 2025 |
| Repo | [Pointcept/Concerto](https://github.com/Pointcept/Concerto) |
| Weights | [HuggingFace: Pointcept/Concerto](https://huggingface.co/Pointcept/Concerto) |
| Project | https://pointcept.github.io/Concerto |
| Backbone | Point Transformer V3 (PTv3) — same as Sonata |
| Pre-training | Intra-modal 3D self-distillation + cross-modal 2D-3D joint embedding (frozen DINOv2) |
| Training data | ScanNet, ScanNet++, Structured3D, S3DIS, ArkitScenes, HM3D (~40k scenes) |

## Model Variants

| Model | Params | enc_channels | enc_depths | SOTA Result |
|-------|--------|-------------|-----------|-------------|
| `concerto_small` | 39M | (48, 96, 192, 384, 512) | (3,3,3,12,3) | — |
| `concerto_base` | 108M | (48, 96, 192, 384, 512) | (3,3,3,12,3) | — |
| `concerto_large` | 208M | (48, 96, 192, 384, 512) | (3,3,3,12,3) | 80.7% mIoU ScanNet |
| `concerto_large_outdoor` | 208M | same | same | outdoor scenes |

Also available: `sonata` (108M), `sonata_small` (39M) — predecessors without 2D-3D joint training.

## Method Summary

Concerto combines two objectives on a shared PTv3 backbone:

1. **Intra-modal 3D self-distillation** (from Sonata): Teacher-student with momentum update + clustering-based loss on augmented 3D views
2. **Cross-modal 2D-3D joint embedding**: Frozen DINOv2 extracts image features; cosine similarity loss aligns predicted 3D point features with corresponding 2D patch features via camera projection

The result is a unified 3D encoder that captures both geometric (from 3D) and semantic (from 2D) information, outperforming standalone 2D/3D models and even their feature concatenation.

## Architecture

```
Input Point Cloud (N, 6: coord + color/normal)
    │
    ▼
[Embedding] ──► (N, 48)
    │
    ▼
[Encoder Stage 0] ──► 3 Blocks, (N, 48)
    │ GridPooling (stride=2)
    ▼
[Encoder Stage 1] ──► 3 Blocks, (N/2, 96)
    │ GridPooling (stride=2)
    ▼
[Encoder Stage 2] ──► 3 Blocks, (N/4, 192)
    │ GridPooling (stride=2)
    ▼
[Encoder Stage 3] ──► 12 Blocks, (N/8, 384)
    │ GridPooling (stride=2)
    ▼
[Encoder Stage 4] ──► 3 Blocks, (N/16, 512)   ◄── output (enc_mode=True)

Each Block = CPE(spconv3d) → SerializedAttention → MLP
Attention: patches of 1024 pts on Z-order/Hilbert serialization
```

## Installation

```bash
conda create -n concerto python=3.10
conda activate concerto
conda install pytorch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 pytorch-cuda=12.4 -c pytorch -c nvidia
conda install nvidia::cuda-toolkit=12.4
conda install conda-forge::gcc=13.2 conda-forge::gxx=13.2

pip install concerto  # Installs the package from PyPI / GitHub
# OR:
pip install git+https://github.com/Pointcept/Concerto.git

# Required sparse ops
pip install spconv-cu124
pip install torch-scatter -f https://data.pyg.org/whl/torch-2.5.0+cu124.html

# Optional but recommended (~2-3x speedup)
pip install flash-attn --no-build-isolation
```

## Core API

### Loading Models

```python
import concerto

# Load pre-trained encoder (encoder-only mode by default)
model = concerto.model.load("concerto_large").cuda()

# Available names: concerto_small, concerto_base, concerto_large,
#                  concerto_large_outdoor, sonata, sonata_small

# Without FlashAttention:
model = concerto.model.load("concerto_large", custom_config={
    "enable_flash": False,
    "enc_patch_size": [1024] * 5,
}).cuda()
```

**`concerto.model.load()` signature:**
```python
def load(
    name: str = "concerto_large",
    repo_id: str = "Pointcept/Concerto",
    download_root: str = None,        # default: ~/.cache/concerto/ckpt
    custom_config: dict = None,
    ckpt_only: bool = False,
) -> PointTransformerV3
```

### Data Preparation

```python
import torch
import concerto

# Option A: Load demo data
point = concerto.data.load("sample1")

# Option B: Your own data
point = {
    "coord": np.array(..., dtype=np.float32),   # (N, 3)
    "color": np.array(..., dtype=np.uint8),      # (N, 3) RGB 0-255
    "normal": np.array(..., dtype=np.float32),   # (N, 3) optional
}

# Apply default transforms (center, grid sample, normalize, tensorize)
transform = concerto.transform.default()
point = transform(point)
```

### Inference

```python
# Move to GPU
for key in point:
    if isinstance(point[key], torch.Tensor):
        point[key] = point[key].cuda()

# Forward pass
with torch.inference_mode():
    output = model(point)
# output.feat: (N_grid, 512) at coarsest encoder scale
```

### Feature Recovery to Original Resolution

```python
# Upsample through hierarchical levels (2 levels with concat, rest with copy)
for _ in range(2):
    parent = output.pop("pooling_parent")
    inverse = output.pop("pooling_inverse")
    parent.feat = torch.cat([parent.feat, output.feat[inverse]], dim=-1)
    output = parent

while "pooling_parent" in output.keys():
    parent = output.pop("pooling_parent")
    inverse = output.pop("pooling_inverse")
    parent.feat = output.feat[inverse]
    output = parent

# Map from grid-sampled to original point resolution
original_feat = output.feat[output.inverse]
```

### Batched Inference

```python
import copy
point1 = transform(concerto.data.load("sample1"))
point2 = copy.deepcopy(point1)
batch = concerto.data.collate_fn([point1, point2])
# batch has concatenated coords with batch indices
```

## Paper-Code Mapping

| Paper Concept | Code Location |
|--------------|---------------|
| PTv3 backbone | `concerto.model.PointTransformerV3` |
| Serialized attention | `concerto.model.SerializedAttention` |
| Contextual Position Encoding (CPE) | `spconv.SubMConv3d` in `Block.__init__` |
| Grid pooling / hierarchical encoding | `concerto.model.GridPooling` |
| Grid unpooling / feature recovery | `concerto.model.GridUnpooling` |
| Point serialization (Z-order/Hilbert) | `concerto.serialization.encode()` |
| Point data structure | `concerto.structure.Point` (extends `addict.Dict`) |

## Key Data Structure: `Point`

```python
class Point(Dict):  # from addict.Dict
    # Required
    coord: Tensor    # (N, 3) float32
    feat: Tensor     # (N, C) float32
    batch: Tensor    # (N,) int64

    # Auto-generated
    offset: Tensor           # (B,) cumulative point counts
    grid_coord: Tensor       # (N, 3) int32 after GridSample
    serialized_order: Tensor # (K, N) sort indices per ordering
    sparse_conv_feat: SparseConvTensor  # for CPE

    # Hierarchical (maintained during forward)
    pooling_parent: Point
    pooling_inverse: Tensor
```

## Key Results

| Benchmark | Concerto-L | Sonata | Improvement |
|-----------|-----------|--------|-------------|
| ScanNet val (mIoU) | **80.7%** | 79.0% | +1.7 |
| ScanNet200 val | **37.8%** | 33.5% | +4.3 |
| ScanNet++ val | **48.3%** | 45.2% | +3.1 |
| S3DIS Area 5 | **75.5%** | 74.5% | +1.0 |
| Linear probe (ScanNet) | outperforms DINOv2 by 14.2%, Sonata by 4.8% |

## Inference Speed Benchmark (from our experiments)

Tested on NVIDIA A100-SXM4-80GB, PyTorch 2.5.0+cu124, batch_size=1, 50 timed runs after 10 warmup.

| Model | Params | Points | Latency (ms) | FPS | GPU Mem (GB) |
|-------|--------|--------|-------------|-----|-------------|
| sonata_small | 39M | 1024 | 55.9 | 17.9 | 0.33 |
| concerto_small | 39M | 1024 | 58.3 | 17.2 | 0.34 |
| sonata | 108M | 1024 | 73.1 | 13.7 | 0.61 |
| concerto_base | 108M | 1024 | 72.3 | 13.8 | 0.62 |
| utonia | 137M | 1024 | 88.3 | 11.3 | 0.79 |
| concerto_large | 208M | 1024 | 90.5 | 11.1 | 1.08 |
| sonata_small | 39M | 4096 | 74.9 | 13.3 | 0.69 |
| concerto_small | 39M | 4096 | 74.8 | 13.4 | 0.69 |
| sonata | 108M | 4096 | 132.0 | 7.6 | 1.21 |
| concerto_base | 108M | 4096 | 132.2 | 7.6 | 1.21 |
| utonia | 137M | 4096 | 151.4 | 6.6 | 1.61 |
| concerto_large | 208M | 4096 | 174.3 | 5.7 | 1.85 |

### Speed Benchmark Takeaways

- **Concerto vs Sonata**: Architecturally identical at inference — same latency for same model size (they share the PTv3 backbone; Concerto's advantage is purely from better pre-training)
- **Scaling**: Latency increases sub-linearly with point count (4x points -> ~1.3-1.8x latency)
- **Memory efficient**: Even concerto_large uses only 1.85 GB at 4096 points on A100
- **For real-time robotics**: concerto_small at ~17 FPS (1024 pts) or ~13 FPS (4096 pts) is the practical choice
- **Utonia comparison**: ~20% slower than concerto_base despite fewer params (137M vs 108M), likely due to cross-domain architecture overhead

## Practical Tips

1. **FlashAttention matters**: Install `flash-attn` for 2-3x speedup; without it, set `enable_flash=False` and specify `enc_patch_size`
2. **Grid size**: Default 0.02m works for indoor scenes; adjust for your scale
3. **Feature levels**: Use level 2-3 features for downstream tasks (level 2 = encoder output; level 3 = one pooling up)
4. **Color input**: Model expects RGB in [0, 255] before transform; `NormalizeColor` scales to [0, 1]
5. **No color/normal**: Model works with coord-only input (fills zeros), but quality degrades
6. **Encoder-only**: Pre-trained models use `enc_mode=True` (no decoder); for segmentation fine-tuning, use full encoder-decoder with `enc_mode=False`
