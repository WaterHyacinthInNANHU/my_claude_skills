---
name: <skill_name>
description: <One-line summary of the paper's contribution>
---

# <skill_name>

<1-2 sentence summary of what this method does and why it matters.>

## Paper Info

| Field | Value |
|-------|-------|
| Title | <full title> |
| Authors | <first author> et al. |
| Year | <year> |
| Venue | <conference/journal> |
| Paper | <URL> |
| Code | <GitHub URL> |
| Weights | <download URL if available> |

## Method Overview

<High-level description of the approach in 1-2 short paragraphs or a numbered list of steps. Focus on the pipeline, not the math.>

Key insight: <the core novel idea in one sentence>

## Paper-Code Mapping

| Paper Concept | Code Location | Notes |
|---------------|---------------|-------|
| <Model name (Sec X)> | `path/file.py:ClassName` | <brief note> |
| <Loss function (Eq Y)> | `path/file.py:function_name` | <brief note> |
| <Data augmentation (Sec Z)> | `path/file.py:ClassName` | <brief note> |
| <Key hyperparameter (Table W)> | `path/config.yaml` or `path/file.py:L42` | default=<value> |

## Setup

### Dependencies

- Python X.X+
- PyTorch X.X+ / other framework
- CUDA X.X+
- Key packages: `pkg1`, `pkg2`, `pkg3`

### Installation

```bash
git clone <repo_url>
cd <repo_name>
pip install -r requirements.txt  # or conda env create, etc.
```

### Pre-trained Weights

```bash
# <instructions to download weights>
```

## Usage Scenarios

### <Scenario 1: e.g., Inference on Custom Data>

```bash
python <command> --flag value
```

### <Scenario 2: e.g., Training from Scratch>

```bash
python <command> --config <path>
```

### <Scenario 3: e.g., Fine-tuning on Custom Dataset>

```bash
python <command> --flag value
```

### Key Config Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--flag1` | value | what it does |
| `--flag2` | value | what it does |

## Code Integration Guide

How to use this paper's code in your own project (not just run the repo's scripts).

### Minimal Imports

```python
import sys
sys.path.append("/path/to/<repo_name>")

from <module> import <ClassName>
# or: from <package>.<module> import <ClassName>
```

### Model Instantiation & Inference

```python
# Construct the model with key arguments (use actual constructor signature)
model = ClassName(
    arg1=value1,   # <what this controls>
    arg2=value2,   # <what this controls>
)

# Load pre-trained weights
model.load_state_dict(torch.load("checkpoint.pth")["model"])
model.eval()

# Run inference — document exact input format
# Input: <describe shape, dtype, normalization, coordinate convention, etc.>
# Output: <describe shape, dtype, value range, etc.>
output = model(input_tensor)
```

### Data Format

| Field | Shape / Type | Description |
|-------|-------------|-------------|
| <input_name> | `(B, C, H, W)` float32 | <normalization, range, etc.> |
| <output_name> | `(B, N, D)` float32 | <what it represents> |

### Integration Notes

- <Any path/import quirks (e.g., relative imports that require sys.path hacks)>
- <Whether the model can be used standalone or needs the repo's config system>
- <Thread safety, GPU requirements, or other runtime constraints>
- <If the code is entangled with training scripts, document the minimum extraction needed>

## Core Architecture

```
<ASCII diagram of the pipeline / architecture>
```

## Repo Structure

| Path | Purpose |
|------|---------|
| `path/to/file.py` | What it does |
| `path/to/dir/` | What it contains |

## Tips & Gotchas

- <Hardware requirements>
- <Common pitfalls>
- <Useful tricks>
