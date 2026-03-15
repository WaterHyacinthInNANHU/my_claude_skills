---
name: paper_rob__rdd
description: Training-free sub-task decomposition for long-horizon robot tasks via retrieval and dynamic programming.
---

# paper_rob__rdd

Automatically decomposes long-horizon robot demonstrations into sub-tasks by retrieving similar segments from a prior database using ANN search and optimal partitioning via dynamic programming. Training-free — relies on pre-trained visual encoders (LIV, CLIP, R3M).

## Paper Info

| Field | Value |
|-------|-------|
| Title | RDD: Retrieval-Based Demonstration Decomposer for Planner Alignment in Long-Horizon Tasks |
| Authors | Mingxuan Yan, Yuping Wang, Zechun Liu, Jiachen Li |
| Year | 2025 |
| Venue | NeurIPS 2025 |
| Paper | [arXiv:2510.14968](https://arxiv.org/abs/2510.14968) |
| Code | [tasl-lab/Retrieval-Demonstration-Decomposer](https://github.com/tasl-lab/Retrieval-Demonstration-Decomposer) |
| Project | [rdd-neurips.github.io](https://rdd-neurips.github.io/) |
| Weights | None (training-free method) |
| License | MIT |

## Method Overview

RDD addresses planner-visuomotor dataset misalignment in hierarchical VLA frameworks. Instead of relying on human annotations or heuristics (like UVD) for sub-task decomposition, RDD:

1. **Embeds** all frames of a demonstration using a pre-trained visual encoder (LIV/CLIP/R3M)
2. **Retrieves** similar sub-task segments from a prior database via approximate nearest neighbor (ANN) search
3. **Decomposes** the demonstration via dynamic programming that finds the optimal partition maximizing retrieval similarity, subject to length constraints

Key insight: Formulate sub-task decomposition as an optimal partitioning problem where the score of each candidate segment is its similarity to the nearest prior sub-task — achieving near-oracle performance (only 0.2% success rate gap vs expert annotations) with linear time complexity.

## Paper-Code Mapping

| Paper Concept | Code Location | Notes |
|---------------|---------------|-------|
| RDD score function (Eq 3-5) | `rdd/algorithms.py:rdd_score()` | Combines retrieval distance + length penalty + UVD penalty |
| Optimal partitioning (Sec 3.2) | `rdd/algorithms.py:max_sum_partition()` | DP over frame indices, O(T * max_len) |
| Sub-task feature extraction | `rdd/embed.py:subtask_embeds_to_feature` | default: concat(start, end) -> 2N; ood: end only -> N |
| Visual embedding | `rdd/embed.py:uvd_embed()` | Wraps UVD preprocessors (LIV, CLIP, R3M, etc.) |
| ANN search | `rdd/ann.py:AnnoySearcher` | Spotify Annoy wrapper, angular distance, 10 trees |
| UVD baseline | `rdd/uvd_wrapper.py:uvd_decompose()` | Kernel regression + local extrema detection |
| Length divergence penalty | `rdd/algorithms.py:rdd_score()` L30-35 | `alpha * abs(1 - segment_len / nn_duration)` |
| UVD boundary penalty | `rdd/algorithms.py:rdd_score()` L37-45 | `beta * abs(s - uvd_start) / segment_len` |
| Vector database | `rdd/datasets/rlbench.py:RLBenchVecDataset` | SQLModel-backed, stores per-sub-task embeddings |
| ANN index builder | `rdd/datasets/rlbench.py:RLBenchAnnoySearcher` | Multi-view, optional PCA dim reduction |
| Decomposition server | `rdd_server.py` | FastAPI, POST /decompose endpoint |
| Evaluation metrics | `eval_rdd.py:get_accuracy()` | Per-segment IoU with NN matching to ground truth |

## Setup

### Dependencies

- Python 3.9
- PyTorch (with CUDA)
- `annoy>=1.17.0` (Spotify ANN library)
- `fastapi>=0.115.0`, `uvicorn>=0.34.0`
- `sqlmodel>=0.0.24`, `confection>=0.1.0`, `typer>=0.15.0`
- `loguru`, `pyzmq`, `elara`, `scipy`, `scikit-learn`, `opencv-python`, `imageio`
- External: UVD (`github.com/zcczhang/UVD`), LIV (`github.com/penn-pal-lab/LIV`)

### Installation

```bash
# Create environment
conda create -n rdd python==3.9
conda activate rdd

# Clone repo
git clone https://github.com/tasl-lab/Retrieval-Demonstration-Decomposer.git
cd Retrieval-Demonstration-Decomposer

# Install Python deps
pip install -r scripts/setup/requirements.txt

# Clone external model libraries into 3rdparty/
bash scripts/setup/setup_rdd_env.sh
# This clones UVD (e7d657a) and LIV (a12991f) into 3rdparty/
```

## Architecture

```
Input: Long-horizon demonstration (T frames, V views)
  │
  ├─ 1. EMBED: frames -> visual encoder (LIV/CLIP/R3M)
  │      Output: embeds (T, D) per view
  │      Multi-view: concat across views -> (T, D*V)
  │
  ├─ 2. PRIOR DATABASE (built offline from training sub-tasks):
  │      For each annotated sub-task -> extract feature
  │        default mode: concat(start_frame, end_frame) -> (2D*V,)
  │        ood mode: end_frame only -> (D*V,)
  │      Store in Annoy ANN index
  │
  ├─ 3. SCORE each candidate segment [s, e]:
  │      a. Extract sub-task feature -> query ANN -> retrieval_dist
  │      b. Length penalty: alpha * |1 - (e-s) / nn.duration|
  │      c. UVD penalty: beta * |s - uvd_start| / (e-s)
  │      d. score = -(retrieval_dist + penalties) * segment_len
  │
  ├─ 4. DYNAMIC PROGRAMMING: max_sum_partition()
  │      dp[i] = max over j of (dp[j] + score(u[j:i]))
  │      subject to min_len <= i-j <= max_len
  │
  └─ 5. OUTPUT: optimal partition -> list of sub-task segments
         + matched prior sub-tasks (nearest neighbors)
```

## Key Hyperparameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | `1.0` | Length divergence penalty weight (forced to 0 in ood mode) |
| `beta` | `0.1`-`0.25` | UVD boundary alignment penalty weight |
| `max_len` | `100` | Maximum sub-task length in frames |
| `min_len` | `2` | Minimum sub-task length in frames |
| `mode` | `"ood"` | `"default"`: start+end features (2N-dim); `"ood"`: end-only (N-dim), alpha=0 |
| `preprocessor` | `"liv"` | Visual encoder: `liv`, `clip`, `r3m`, `vip`, `vc1`, `dino_v2`, `resnet` |
| `views` | `["front_rgb"]` | Camera views to use |
| `chunk_size` | `64` | Batch size for frame embedding |
| `n_trees` | `10` | Number of Annoy index trees |
| `distance_measure` | `"angular"` | Annoy distance metric |

## Usage Scenarios

### 1. Build Vector Database (offline, one-time)

```bash
python build_vec_database.py <gpu_id> <encoder> <sample_rate> <dataset_path> \
    --name-suffix <name> --views front_rgb --embed-mode ood
```

### 2. Run RDD Server

```bash
uvicorn rdd_server:app --port 8001 --workers 8
```

Endpoints:
- `GET /config` — returns current config
- `POST /decompose` — accepts frame paths, returns segments + nearest neighbors

### 3. Evaluate Decomposition Quality

```bash
python eval_rdd.py <dataset_path> <results_save_path> \
    --worker-num 4 --rdd-port 8001
```

Computes per-segment IoU against ground truth annotations.

## Code Integration Guide

### Minimal Imports

```python
from rdd.algorithms import max_sum_partition, rdd_score
from rdd.datasets.rlbench import RLBenchAnnoySearcher
from rdd.embed import uvd_embed, subtask_embeds_to_feature
```

### Decompose a New Demonstration

```python
import numpy as np

# 1. Embed frames
embeds = uvd_embed(
    frame_paths,                    # list of image file paths
    preprocessor="liv",             # or "clip", "r3m"
    device="cuda",
)  # -> (T, D) np.ndarray

# 2. Load prior sub-task database + ANN index
searcher = RLBenchAnnoySearcher(
    searcher_path="data/vec_databases/franka/train/index.ann",
    vec_database_path="data/vec_databases/franka/train",
    include_views=["front_rgb"],
    n_trees=10,
    distance_measure="angular",
)

# 3. Run optimal partitioning
score, segments = max_sum_partition(
    u=list(range(len(embeds))),
    score_func=rdd_score,
    min_len=2,
    max_len=100,
    searcher=searcher,
    embeds=embeds,
    mode="ood",
    alpha=0.0,          # forced to 0 in ood mode
    beta=0.1,
)
# segments: list of lists, e.g. [[0,1,...,29], [30,31,...,74], ...]
```

### Data Format

| Field | Format | Description |
|-------|--------|-------------|
| Frames | PNG images, any resolution | Resized internally by encoder |
| Sub-task annotations (`info.txt`) | One integer per line | Ending frame index of each sub-task |
| Embeddings | `(T, D)` float32 np.ndarray | D depends on encoder (LIV=1024, R3M=2048) |
| Sub-task feature (default) | `(2*D*V,)` float32 | Concat of start + end frame embeddings across views |
| Sub-task feature (ood) | `(D*V,)` float32 | End frame embedding only, across views |

### Supported Encoders

| Encoder | Embedding Dim | Source |
|---------|--------------|--------|
| LIV | 1024 | `penn-pal-lab/LIV` |
| CLIP | 1024 | via LIV |
| R3M | 2048 | `facebookresearch/r3m` |
| VIP | 1024 | `facebookresearch/vip` |
| VC-1 | 768 | `facebookresearch/eai-vc` |
| DINO v2 | 1024 | `facebookresearch/dinov2` |
| ResNet | 1000 | torchvision |

## Repo Structure

| Path | Purpose |
|------|---------|
| `rdd/algorithms.py` | `rdd_score()`, `max_sum_partition()`, `max_n_partition()` |
| `rdd/ann.py` | `AnnoySearcher` — Annoy ANN wrapper |
| `rdd/embed.py` | `uvd_embed()`, `subtask_embeds_to_feature`, encoder loading |
| `rdd/uvd_wrapper.py` | `uvd_decompose()` — UVD baseline wrapper |
| `rdd/datasets/rlbench.py` | `RLBenchVecDataset`, `RLBenchVecEntry`, `RLBenchAnnoySearcher` |
| `build_vec_database.py` | Entry: build vector DB + ANN index from dataset |
| `rdd_server.py` | Entry: FastAPI decomposition server |
| `eval_rdd.py` | Entry: evaluate decomposition IoU metrics |
| `configs/rdd_server.yaml` | Main config (confection/YAML) |
| `utils/` | Cache, concurrency, config loader, database, file utils |
| `scripts/setup/` | `requirements.txt`, `setup_rdd_env.sh` |
| `scripts/dataset/` | Data conversion scripts (AgiBotWorld, RoboCerebra, video→frames) |
| `resources/` | Demo videos + sub-task annotation examples |

## Key Results

- Only **0.2% success rate gap** compared to expert-annotated (oracle) decompositions
- Outperforms UVD heuristic decomposition on both simulation (RLBench) and real-world tasks
- **Training-free** — no model training required, only pre-trained visual encoders + ANN indexing
- **Linear time complexity** via the optimal partitioning DP algorithm

## Tips & Gotchas

- RDD is **training-free** — no custom weights to train. The "prior" is built from your annotated sub-task dataset via `build_vec_database.py`
- The `mode` parameter matters: `ood` (end-frame only, alpha=0) works better for out-of-distribution tasks; `default` (start+end, with length penalty) is for in-distribution
- UVD and LIV must be cloned into `3rdparty/` via `setup_rdd_env.sh` — they are not pip-installable
- The server architecture (FastAPI) is designed for integration with a higher-level planner that sends decomposition requests
- `beta` controls how much RDD defers to UVD's heuristic boundaries — set higher (0.25) for tasks where UVD works well, lower (0.1) for novel tasks
- Multi-view support: views are concatenated in embedding space, increasing feature dimension proportionally
- `info.txt` annotation format: each line is the **ending** frame index of a sub-task (not the starting index)
- Annoy indexes are not updatable — rebuild with `build_vec_database.py` when adding new sub-tasks
