# Examples

## Example 1: User provides arXiv link

**User**: Create a skill for this paper: https://arxiv.org/abs/2303.12345 — code is at https://github.com/author/cool-method

**What you do**:

1. Fetch the arXiv abstract page to get title, authors, summary
2. Read the PDF for method details, architecture, key results
3. **Clone the repo** to `/tmp/paper_skill_cool_method`
4. **Read core source files** — find model classes, loss functions, data loaders
5. **Cross-reference paper ↔ code** — map paper sections to specific files/classes
6. **Trace integration patterns** — how to import and use the model in external code
7. Determine domain → 3D vision → prefix `paper_3d__`
8. Method is called "CoolMethod" → skill name: `paper_3d__cool_method`
9. Create the skill, then clean up `/tmp/paper_skill_cool_method`

```
skills/papers/paper_3d__cool_method/
├── SKILL.md
├── examples.md
└── templates/
    └── train_config.yaml
```

## Example 2: User provides only a paper title

**User**: Make a skill for "Denoising Diffusion Probabilistic Models"

**What you do**:

1. Web-search for the paper → find arXiv link
2. Search for official code repo (check paper, Papers With Code, GitHub)
3. Read the paper PDF
4. **Clone the repo**, read the core implementation files
5. **Map paper concepts → code**: e.g. "forward diffusion (Eq 2) → `diffusion.py:GaussianDiffusion.q_sample()`"
6. Domain: generative models → `paper_gen__ddpm`
7. Create the skill at `skills/papers/paper_gen__ddpm/`

## Example 3: User provides a PDF file

**User**: Create a skill from /home/user/papers/some_method.pdf

**What you do**:

1. Read the PDF directly
2. Extract title, **search for code repo** (required — ask user if not found)
3. **Clone and deep-read the code**
4. Determine domain + short name → e.g. `paper_seg__sam`
5. Create the skill with Paper-Code Mapping and Code Integration Guide

## How Grouping Looks at Scale

```
skills/
├── create_skill/                       # ← core skills
├── create_skill_with_paper/
├── ucr_hpcc_cluster/
└── papers/                             # ← all paper skills in subfolder
    ├── paper_3d__gaussian_splatting/
    ├── paper_3d__instant_ngp/
    ├── paper_3d__nerfacto/
    ├── paper_det__detr/
    ├── paper_det__yolov9/
    ├── paper_gen__ddpm/
    ├── paper_gen__flow_matching/
    ├── paper_gen__stable_diffusion/
    ├── paper_llm__llama3/
    ├── paper_rl__grpo/
    ├── paper_rob__act/
    ├── paper_rob__diffusion_policy/
    ├── paper_seg__sam/
    ├── paper_vlm__clip/
    └── paper_vlm__llava/
```

Papers live in `skills/papers/` in the repo, but get installed flat into `~/.claude/skills/` where the `paper_` prefix groups them.

Papers in the same domain sort together alphabetically, making it easy to browse.

## Example Skill Output

Below is a representative `SKILL.md` for a hypothetical paper:

```markdown
---
name: paper_3d__example_method
description: Fast 3D reconstruction from sparse views using neural radiance fields.
---

# paper_3d__example_method

Fast 3D reconstruction from sparse views (3-5 images) using a feed-forward transformer + NeRF decoder.

## Paper Info

| Field | Value |
|-------|-------|
| Title | ExampleMethod: Fast Sparse-View 3D Reconstruction |
| Authors | Smith et al. |
| Year | 2024 |
| Venue | CVPR 2024 |
| Paper | https://arxiv.org/abs/2401.XXXXX |
| Code | https://github.com/smith/example-method |
| Weights | https://github.com/smith/example-method/releases |

## Method Overview

1. Encode input images with a vision transformer (DINOv2 backbone)
2. Cross-attend between views to build a 3D-aware feature volume
3. Decode novel views with a lightweight NeRF MLP
4. Train end-to-end with photometric + perceptual loss

Key insight: replaces per-scene optimization with a single forward pass.

## Paper-Code Mapping

| Paper Concept | Code Location | Notes |
|---------------|---------------|-------|
| Image encoder (Sec 3.1) | `models/encoder.py:ImageEncoder` | Wraps DINOv2 ViT-B/14, outputs `(B, N, 768)` tokens |
| Cross-view attention (Sec 3.2) | `models/transformer.py:CrossViewTransformer` | 6-layer transformer, `n_heads=12`, `dim=768` |
| Triplane projection (Sec 3.3) | `models/transformer.py:TriplaneProjection` | Projects tokens → 3 feature planes `(B, C, H, W)` |
| NeRF decoder (Sec 3.4) | `models/nerf.py:NeRFMLP` | 4-layer MLP, `hidden_dim=256`, outputs RGB+σ |
| Volume rendering (Eq 5) | `models/nerf.py:volume_render()` | Uses nerfacc for ray marching |
| Photometric loss (Eq 7) | `losses/reconstruction.py:PhotometricLoss` | L1 + LPIPS (weight=0.1) |
| Training schedule (Sec 4.1) | `configs/default.yaml` | lr=1e-4, cosine decay, 100k steps |

## Setup

### Dependencies

- Python 3.9+
- PyTorch 2.1+
- CUDA 11.8+
- Key packages: `torchvision`, `einops`, `timm`, `nerfacc`

### Installation

    git clone https://github.com/smith/example-method
    cd example-method
    pip install -r requirements.txt

### Pre-trained Weights

    # Download from releases
    wget https://github.com/smith/example-method/releases/download/v1.0/checkpoint.pth

## Usage Scenarios

### Inference on Custom Images

    python predict.py --input_dir ./my_images --checkpoint checkpoint.pth --output_dir ./results

### Training on Custom Dataset

    python train.py --config configs/custom.yaml --data_root /path/to/data --gpus 4

### Key Config Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--num_views` | 4 | Number of input views |
| `--resolution` | 256 | Render resolution |
| `--backbone` | dinov2_vitb14 | Image encoder |
| `--lr` | 1e-4 | Learning rate |

## Code Integration Guide

How to use ExampleMethod's model in your own project.

### Minimal Imports

    import sys
    sys.path.append("/path/to/example-method")

    from models.encoder import ImageEncoder
    from models.transformer import CrossViewTransformer
    from models.nerf import NeRFMLP, volume_render

### Model Instantiation & Inference

    import torch

    # Build components (matches constructor signatures in the repo)
    encoder = ImageEncoder(backbone="dinov2_vitb14", freeze_backbone=True)
    transformer = CrossViewTransformer(dim=768, n_heads=12, n_layers=6)
    decoder = NeRFMLP(in_dim=768, hidden_dim=256, out_dim=4)

    # Or use the unified wrapper
    from models import ExampleModel
    model = ExampleModel.from_config("configs/default.yaml")

    # Load pre-trained weights
    ckpt = torch.load("checkpoint.pth", map_location="cpu")
    model.load_state_dict(ckpt["model"])
    model.cuda().eval()

    # Input: (B, N, 3, 224, 224) float32, ImageNet-normalized
    # cameras: dict with 'intrinsics' (B, N, 3, 3), 'extrinsics' (B, N, 4, 4)
    # Output: (B, 3, H, W) float32, range [0, 1]
    novel_view = model(images, cameras, target_camera)

### Data Format

| Field | Shape / Type | Description |
|-------|-------------|-------------|
| `images` | `(B, N, 3, 224, 224)` float32 | ImageNet-normalized (mean=[0.485,0.456,0.406]) |
| `cameras.intrinsics` | `(B, N, 3, 3)` float32 | Camera intrinsic matrices |
| `cameras.extrinsics` | `(B, N, 4, 4)` float32 | Camera-to-world transforms |
| output | `(B, 3, H, W)` float32 | Rendered RGB, range [0, 1] |

### Integration Notes

- The repo uses relative imports within `models/` — add the repo root to `sys.path`
- `ImageEncoder` downloads DINOv2 weights on first use (requires internet)
- Inference requires ~8GB VRAM for 4 input views at 256×256

## Core Architecture

    Input Images (N views)
        │
        ▼
    ImageEncoder (DINOv2 ViT-B/14, frozen)
        │  Output: (B, N, 257, 768) patch tokens
        ▼
    CrossViewTransformer (6 layers, 12 heads)
        │  Output: (B, N, 257, 768) cross-attended tokens
        ▼
    TriplaneProjection
        │  Output: 3 × (B, 256, 64, 64) feature planes
        ▼
    NeRFMLP (4 layers, hidden=256) → RGB(3) + σ(1)
        │
        ▼
    volume_render() (nerfacc) → (B, 3, H, W) Novel View

## Repo Structure

| Path | Purpose |
|------|---------|
| `models/encoder.py` | `ImageEncoder` — DINOv2 wrapper |
| `models/transformer.py` | `CrossViewTransformer`, `TriplaneProjection` |
| `models/nerf.py` | `NeRFMLP`, `volume_render()` |
| `models/__init__.py` | `ExampleModel` — unified wrapper |
| `losses/reconstruction.py` | `PhotometricLoss` (L1 + LPIPS) |
| `datasets/` | Data loading & augmentation |
| `configs/` | Hydra config files |
| `train.py` | Training entry point |
| `predict.py` | Inference entry point |

## Tips & Gotchas

- Requires ~24GB VRAM for training at 256 resolution
- Use `--backbone dinov2_vits14` for lower memory
- Input images should have known camera poses (use COLMAP if needed)
- Batch size > 4 may cause OOM on single GPU — use DDP
- To extract just the model for your project, copy the `models/` dir and `pip install einops timm nerfacc`
```
