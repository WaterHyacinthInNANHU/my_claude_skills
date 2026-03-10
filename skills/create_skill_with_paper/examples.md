# Examples

## Example 1: User provides arXiv link

**User**: Create a skill for this paper: https://arxiv.org/abs/2303.12345 — code is at https://github.com/author/cool-method

**What you do**:

1. Fetch the arXiv abstract page to get title, authors, summary
2. Read the PDF for method details, architecture, key results
3. Browse the GitHub repo for dependencies, entry points, configs
4. Determine domain → 3D vision → prefix `paper_3d__`
5. Method is called "CoolMethod" → skill name: `paper_3d__cool_method`
6. Create the skill:

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
3. Read paper + repo
4. Domain: generative models → `paper_gen__ddpm`
5. Create the skill at `skills/papers/paper_gen__ddpm/`

## Example 3: User provides a PDF file

**User**: Create a skill from /home/user/papers/some_method.pdf

**What you do**:

1. Read the PDF directly
2. Extract title, search for code repo
3. Determine domain + short name → e.g. `paper_seg__sam`
4. Create the skill

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

## Core Architecture

    Input Images (N views)
        │
        ▼
    DINOv2 Encoder (frozen or fine-tuned)
        │
        ▼
    Cross-View Transformer (6 layers)
        │
        ▼
    Triplane Feature Volume
        │
        ▼
    NeRF MLP Decoder → RGB + Density
        │
        ▼
    Volume Rendering → Novel View

## Repo Structure

| Path | Purpose |
|------|---------|
| `models/encoder.py` | Vision transformer encoder |
| `models/transformer.py` | Cross-view attention |
| `models/nerf.py` | NeRF decoder + rendering |
| `datasets/` | Data loading & augmentation |
| `configs/` | Hydra config files |
| `train.py` | Training entry point |
| `predict.py` | Inference entry point |

## Tips & Gotchas

- Requires ~24GB VRAM for training at 256 resolution
- Use `--backbone dinov2_vits14` for lower memory
- Input images should have known camera poses (use COLMAP if needed)
- Batch size > 4 may cause OOM on single GPU — use DDP
```
