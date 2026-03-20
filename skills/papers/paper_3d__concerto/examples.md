# Concerto — Usage Examples

## 1. Feature Extraction (Minimal)

```python
import concerto
import torch

# Load model
model = concerto.model.load("concerto_base").cuda().eval()

# Prepare point cloud
point = {
    "coord": coords,    # (N, 3) np.float32
    "color": colors,    # (N, 3) np.uint8, RGB
}
transform = concerto.transform.default()
point = transform(point)
for k in point:
    if isinstance(point[k], torch.Tensor):
        point[k] = point[k].cuda()

# Extract features
with torch.inference_mode():
    output = model(point)
feat = output.feat  # (N_grid, 512) at coarsest scale
```

## 2. Full-Resolution Feature Recovery

```python
# After model forward pass, recover features at original point resolution
def recover_features(output):
    """Upsample hierarchical features to original resolution."""
    # Concat features from 2 levels
    for _ in range(2):
        parent = output.pop("pooling_parent")
        inverse = output.pop("pooling_inverse")
        parent.feat = torch.cat([parent.feat, output.feat[inverse]], dim=-1)
        output = parent
    # Copy features for remaining levels
    while "pooling_parent" in output.keys():
        parent = output.pop("pooling_parent")
        inverse = output.pop("pooling_inverse")
        parent.feat = output.feat[inverse]
        output = parent
    # Grid-sampled → original resolution
    return output.feat[output.inverse]

original_feat = recover_features(output)  # (N_original, C)
```

## 3. Batched Inference

```python
import copy
import concerto

model = concerto.model.load("concerto_large").cuda().eval()
transform = concerto.transform.default()

# Prepare batch
points = []
for pc in point_clouds:  # list of dicts with coord, color
    points.append(transform(pc))
batch = concerto.data.collate_fn(points)

for k in batch:
    if isinstance(batch[k], torch.Tensor):
        batch[k] = batch[k].cuda()

with torch.inference_mode():
    output = model(batch)
# output.batch: (N_total,) indices identifying which cloud each point belongs to
# output.offset: (B,) cumulative point counts
```

## 4. PCA Visualization (from demo)

```python
import concerto
import torch
import numpy as np
from sklearn.decomposition import PCA

model = concerto.model.load("concerto_large").cuda().eval()
point = concerto.data.load("sample1")
transform = concerto.transform.default()
point = transform(point)
for k in point:
    if isinstance(point[k], torch.Tensor):
        point[k] = point[k].cuda()

with torch.inference_mode():
    output = model(point)

feat = recover_features(output)  # see above
feat_np = feat.cpu().numpy()

pca = PCA(n_components=3)
pca_color = pca.fit_transform(feat_np)
pca_color = (pca_color - pca_color.min(0)) / (pca_color.max(0) - pca_color.min(0))
# pca_color is (N, 3) RGB for visualization
```

## 5. Integration with DP3 / Robotic Manipulation

When using Concerto as a point cloud encoder in a diffusion policy pipeline:

```python
import concerto
import torch

class ConcertoEncoder(torch.nn.Module):
    """Wrapper for using Concerto as a point cloud encoder in DP3-style policies."""

    def __init__(self, model_name="concerto_small", out_dim=256):
        super().__init__()
        self.model = concerto.model.load(model_name)
        self.model.eval()
        # Project from encoder output dim to policy embedding dim
        # concerto_small/base/large all output 512-dim at coarsest level
        self.proj = torch.nn.Linear(512, out_dim)
        self.transform = concerto.transform.default()

    def forward(self, coords, colors=None):
        """
        Args:
            coords: (B, N, 3) point coordinates
            colors: (B, N, 3) RGB colors [0, 255], optional
        Returns:
            features: (B, out_dim) global features
        """
        B, N, _ = coords.shape
        all_points = []
        for i in range(B):
            pt = {"coord": coords[i].cpu().numpy()}
            if colors is not None:
                pt["color"] = colors[i].cpu().numpy()
            all_points.append(self.transform(pt))

        batch = concerto.data.collate_fn(all_points)
        for k in batch:
            if isinstance(batch[k], torch.Tensor):
                batch[k] = batch[k].to(coords.device)

        with torch.no_grad():
            output = self.model(batch)

        # Global average pooling per sample
        feat = output.feat  # (N_total, 512)
        batch_idx = output.batch
        global_feat = torch.zeros(B, 512, device=feat.device)
        for i in range(B):
            mask = batch_idx == i
            global_feat[i] = feat[mask].mean(dim=0)

        return self.proj(global_feat)
```

**Practical notes for robotics use:**
- Use `concerto_small` (39M, ~17 FPS @ 1024 pts) for real-time control
- `concerto_base` (108M, ~14 FPS @ 1024 pts) if you can tolerate slightly higher latency
- Memory is not a bottleneck — even large model uses < 2 GB for 4096 points
- The encoder is PTv3 (same as Sonata) — Concerto's advantage is better pre-trained weights from joint 2D-3D training

## 6. Running the Speed Benchmark

Benchmark script location: `/rhome/myan035/workspace/dp3-policy-design/point-cloud-encoder-test/workspace/scripts/benchmark_inference.py`

```bash
# On HPCC with GPU
sbatch /rhome/myan035/workspace/dp3-policy-design/point-cloud-encoder-test/workspace/scripts/run_benchmark.sh
```

The benchmark tests all PTv3-family encoders (sonata, concerto, utonia) across point counts (1024, 2048, 4096) measuring latency, throughput, and GPU memory.

## 7. Without FlashAttention

If you can't install flash-attn (e.g., older GPU):

```python
model = concerto.model.load("concerto_base", custom_config={
    "enable_flash": False,
    "enc_patch_size": [1024, 1024, 1024, 1024, 1024],
}).cuda()
```

This falls back to standard PyTorch attention — slower but functional.
