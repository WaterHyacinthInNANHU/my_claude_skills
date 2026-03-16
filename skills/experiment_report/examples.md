# Examples

## Example: DP3 Point Cloud Augmentation Ablation

# Experiment Report: DP3 Point Cloud Augmentation on Adroit Hammer

**Date:** 2026-03-10
**Author:** MY
**Project:** dp3-robomanip
**Experiment ID:** exp-042
**Status:** success

---

## 1. Motivation

**Hypothesis:** Adding random SE(3) jitter (+-5deg rotation, +-1cm translation) to the input point cloud during DP3 training will improve sim-to-sim generalization on Adroit Hammer by reducing overfitting to fixed camera poses.

**Context:** exp-039 showed DP3 success rate drops from 82% to 61% when we randomize camera position at eval time. This suggests the policy memorizes viewpoint-specific point cloud structure.

---

## 2. Experiment Setup

| Item | Details |
|------|---------|
| Task / Env | Adroit Hammer-v1 (DexPoint variant) |
| Dataset | 200 expert demos from exp-030 |
| Repo / Branch | dp3-fork, branch `pc-augment` |
| Commit | `a3f7c12` |
| Hardware | 1x A100-80GB, HPCC `gpu01` |
| SLURM Job ID | 9482731 |
| Seeds | 0, 1, 2 |
| Training steps | 300k |
| Batch size | 256 |
| Learning rate | 1e-4 (cosine decay to 1e-6) |
| Point cloud size | 1024 points |

**Baseline:** exp-039 (same config, no augmentation), success rate 82% (fixed cam) / 61% (random cam)

<details>
<summary>Config snippet</summary>

```yaml
augmentation:
  enabled: true
  rotation_deg: 5.0
  translation_cm: 1.0
  apply_prob: 0.8
```

</details>

---

## 3. Method

**Changes:**
1. Added SE(3) jitter to point cloud input during training (rotation sampled uniformly +-5 deg per axis, translation +-1cm, applied with p=0.8)
2. No changes to architecture or loss

---

## 4. Results

### Key Metrics

| Method | Success Rate (fixed cam) | Success Rate (random cam) | Training Time |
|--------|------------------------|--------------------------|---------------|
| Baseline (exp-039) | 82 +/- 3% | 61 +/- 5% | 4.2h |
| + PC augment (exp-042) | 80 +/- 2% | 74 +/- 3% | 4.3h |

### Training Curves

**W&B:** https://wandb.ai/mylab/dp3-robomanip/groups/exp-042

Loss converged similarly to baseline. No training instability from augmentation.

### Qualitative Observations

- Under random camera, baseline frequently misaligns the hammer grasp by ~1cm. Augmented policy corrects this.
- Two failure modes remain: (1) dropping hammer during swing, (2) nail not seated properly (env reset issue).

---

## 5. Analysis & Next Steps

### What Worked
PC augmentation recovered 13 percentage points of success rate under camera randomization with negligible cost to fixed-camera performance (-2%, within noise).

### What Didn't Work
Still a 6-point gap between fixed and random camera, suggesting augmentation alone doesn't fully solve viewpoint invariance.

### Surprising Observations
Augmentation didn't slow convergence at all -- expected at least mild slowdown.

### Next Experiment Proposal

**Proposed:** exp-043 -- combine PC augmentation with PointNet++ backbone (replace current PointNet)
- Change: swap encoder to PointNet++ with multi-scale grouping
- Expected outcome: further close the fixed/random camera gap by learning hierarchical local features
- Priority: high
