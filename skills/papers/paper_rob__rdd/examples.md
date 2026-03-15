# RDD Examples & Recipes

## 1. Full Pipeline: Build Database + Decompose + Evaluate

```bash
cd Retrieval-Demonstration-Decomposer
conda activate rdd

# Step 1: Build vector database from training sub-tasks
python build_vec_database.py 0 liv 1 data/rlbench/splits/train \
    --name-suffix franka_liv --views front_rgb --embed-mode ood

# Step 2: Start decomposition server
# Edit configs/rdd_server.yaml first:
#   vec_database_path: "data/vec_databases/franka/train"
#   preprocessor: "liv"
#   mode: "ood"
#   alpha: 1.0
#   beta: 0.1
uvicorn rdd_server:app --port 8001 --workers 8

# Step 3: Evaluate on validation set (in another terminal)
python eval_rdd.py data/rlbench/splits/val results/rdd_eval \
    --worker-num 4 --rdd-port 8001
```

## 2. Python API: Decompose a Single Demonstration

```python
from rdd.algorithms import max_sum_partition, rdd_score
from rdd.datasets.rlbench import RLBenchAnnoySearcher
from rdd.embed import uvd_embed
import numpy as np

# Embed frames
frame_paths = [f"demo/frame_{i:04d}.png" for i in range(200)]
embeds = uvd_embed(frame_paths, preprocessor="liv", device="cuda")
# embeds.shape: (200, 1024)

# Load ANN searcher
searcher = RLBenchAnnoySearcher(
    searcher_path="data/vec_databases/franka/train/index.ann",
    vec_database_path="data/vec_databases/franka/train",
    include_views=["front_rgb"],
)

# Decompose
score, segments = max_sum_partition(
    u=list(range(len(embeds))),
    score_func=rdd_score,
    min_len=2,
    max_len=100,
    searcher=searcher,
    embeds=embeds,
    mode="ood",
    alpha=0.0,
    beta=0.1,
)

# Print decomposition
for i, seg in enumerate(segments):
    print(f"Sub-task {i}: frames {seg[0]}-{seg[-1]} ({len(seg)} frames)")
```

## 3. Multi-View Decomposition

```python
from rdd.embed import uvd_embed
import numpy as np

# Embed each view separately
front_embeds = uvd_embed(front_frame_paths, preprocessor="liv", device="cuda")
wrist_embeds = uvd_embed(wrist_frame_paths, preprocessor="liv", device="cuda")

# Concatenate views (as done in the server pipeline)
embeds = np.concatenate([front_embeds, wrist_embeds], axis=-1)
# embeds.shape: (T, 2048) for 2 views with LIV (1024 each)

# Build/load searcher with matching views
searcher = RLBenchAnnoySearcher(
    searcher_path="data/vec_databases/franka/train/index.ann",
    vec_database_path="data/vec_databases/franka/train",
    include_views=["front_rgb", "wrist_rgb"],
)

# Decompose as usual
score, segments = max_sum_partition(
    u=list(range(len(embeds))),
    score_func=rdd_score,
    min_len=2, max_len=100,
    searcher=searcher, embeds=embeds,
    mode="ood", alpha=0.0, beta=0.1,
)
```

## 4. Compare RDD vs UVD Decomposition

```python
from rdd.algorithms import max_sum_partition, rdd_score
from rdd.uvd_wrapper import uvd_decompose
from rdd.embed import uvd_embed

# Embed
embeds = uvd_embed(frame_paths, preprocessor="liv", device="cuda")

# UVD decomposition (heuristic baseline)
uvd_segments = uvd_decompose(embeds)
print(f"UVD found {len(uvd_segments)} sub-tasks")

# RDD decomposition (retrieval + DP)
score, rdd_segments = max_sum_partition(
    u=list(range(len(embeds))),
    score_func=rdd_score,
    min_len=2, max_len=100,
    searcher=searcher, embeds=embeds,
    mode="ood", alpha=0.0, beta=0.1,
)
print(f"RDD found {len(rdd_segments)} sub-tasks")
```

## 5. Evaluate Decomposition Quality (IoU)

```python
from eval_rdd import calculate_iou, find_nearest_neighbors, get_accuracy

# Ground truth segments (from info.txt)
gt_segments = [[0, 29], [30, 74], [75, 119], [120, 179]]

# Predicted segments (from RDD)
pred_segments = [[s[0], s[-1]] for s in segments]

# Compute accuracy (mean IoU with NN matching)
accuracy = get_accuracy(pred_segments, gt_segments)
print(f"Mean IoU: {accuracy:.3f}")
```

## 6. Client-Server Integration (with a Planner)

```python
import requests

# Send decomposition request to RDD server
response = requests.post(
    "http://localhost:8001/decompose",
    json={
        "paths": [[f"demo/frame_{i:04d}.png"] for i in range(200)],
        # paths shape: (T, num_views) — list of lists
        "preprocessor": "liv",
        "method": "rdd",    # or "uvd" for baseline
    },
)
result = response.json()
segments = result["segments"]
nearest_neighbors = result["nearest_neighbors"]
```

## 7. Prepare Custom Dataset (Video to RLBench Format)

```bash
# Convert video to frames
python scripts/dataset/video_to_frames.py \
    --input path/to/video.mp4 \
    --output data/custom/frames/

# Convert frames + annotations to RLBench format
python scripts/dataset/frames_dataset_proc.py \
    --input data/custom/frames/ \
    --output data/custom/rlbench_format/
```

Sub-task annotation format (`info.txt`):
```
30
75
120
158
180
```
Each line = ending frame index of a sub-task.

## 8. Build Database with Different Encoders

```bash
# LIV (1024-dim, recommended)
python build_vec_database.py 0 liv 1 data/rlbench/splits/train \
    --name-suffix liv --views front_rgb --embed-mode ood

# CLIP (1024-dim)
python build_vec_database.py 0 clip 1 data/rlbench/splits/train \
    --name-suffix clip --views front_rgb --embed-mode ood

# R3M (2048-dim)
python build_vec_database.py 0 r3m 1 data/rlbench/splits/train \
    --name-suffix r3m --views front_rgb --embed-mode ood
```

## 9. Tuning alpha and beta

```yaml
# configs/rdd_server.yaml

# In-distribution (training tasks):
mode: "default"     # uses start+end frame features
alpha: 1.0          # length penalty ON
beta: 0.25          # moderate UVD alignment

# Out-of-distribution (novel tasks):
mode: "ood"         # uses end frame only
alpha: 0.0          # length penalty OFF (auto-forced)
beta: 0.1           # light UVD alignment
```

| Scenario | mode | alpha | beta | Notes |
|----------|------|-------|------|-------|
| In-distribution tasks | `default` | `1.0` | `0.25` | Full feature + penalties |
| Novel / OOD tasks | `ood` | `0.0` | `0.1` | End-frame only, less reliance on priors |
| UVD works well for your domain | either | any | `0.25+` | Lean on UVD boundaries |
| UVD fails for your domain | either | any | `0.0` | Disable UVD penalty entirely |

## 10. SLURM: Build Database on HPC

```bash
#!/bin/bash
#SBATCH --job-name=rdd_vecdb
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=4:00:00

conda activate rdd
cd /path/to/Retrieval-Demonstration-Decomposer

python build_vec_database.py $CUDA_VISIBLE_DEVICES liv 1 \
    data/rlbench/splits/train \
    --name-suffix franka_liv \
    --views front_rgb \
    --embed-mode ood
```
