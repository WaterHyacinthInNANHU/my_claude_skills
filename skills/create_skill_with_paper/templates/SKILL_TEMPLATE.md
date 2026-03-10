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
