# Experiment Report: [TITLE — include main result]

**Date:** YYYY-MM-DD
**Author:** [name]
**Project:** [project name]
**Status:** success | partial | failed | in-progress

**TL;DR:** [1-2 sentence conclusion. Lead with the best result and key insight.]

---

## 1. Results Summary

<!-- PUT RESULTS FIRST. Readers want numbers immediately. -->

| Experiment | Key Metric 1 | Key Metric 2 | Training Time | W&B | Status |
|------------|-------------|-------------|---------------|-----|--------|
| **Best variant** | **XX%** | **YY%** | Xh | [wandb](link) | Completed |
| Baseline | XX% | YY% | Xh | [wandb](link) | Completed |
| Variant B | XX% | YY% | Xh | [wandb](link) | Failed |

### Key Findings

1. **[Finding 1]** — standalone insight that doesn't require reading the full report
2. **[Finding 2]** — e.g., "Flow matching outperforms MSE by 60pp despite higher loss"
3. **[Finding 3]** — e.g., "Fewer points (1024) beat more points (4096) and train 3x faster"

---

## 2. Motivation

**Hypothesis:** [If we do X, then Y should improve because Z.]

**Context:** [Link to prior experiment or discussion that motivated this.]

---

## 3. Experiment Setup

| Item | Details |
|------|---------|
| Task / Env | |
| Repo / Branch | |
| Commit | |
| Hardware | |
| SLURM Job IDs | |
| Seeds | |
| Training steps | |
| Batch size | |
| Learning rate | |
| Other key HPs | |

**Baseline:** [config name / run ID / published number]

<details>
<summary>Config snippet</summary>

```yaml
# paste relevant config here
```

</details>

---

## 4. Method

**Changes relative to baseline:**
1.
2.
3.

---

## 5. Detailed Results

### Per-Checkpoint Metrics

<!-- Include if training dynamics matter (collapse, recovery, etc.) -->

| Step | Success Once | Success at End | Loss | Notes |
|------|-------------|---------------|------|-------|
| 500 | | | | |
| 1000 | | | | |
| ... | | | | |

### Training Curves

**W&B Dashboard:** [link to group/workspace view]

### Qualitative Observations

<!-- Rollout videos, failure modes, behavioral descriptions -->

### Timing & Infrastructure

<!-- Wall-clock time, per-step speed, any timeouts/restarts/resubmits -->

---

## 6. Analysis & Next Steps

### What Worked
<!-- Root-cause analysis with evidence -->

### What Went Wrong
<!-- Include the fix if found -->

### Surprising Observations

### Next Experiment Proposal

**Proposed:** [one-line description]
- Change:
- Expected outcome:
- Priority: high | medium | low

---

## 7. Artifacts

| Artifact | Path / Link |
|----------|------------|
| Config | `path/to/config.yaml` |
| Best checkpoint | `path/to/checkpoint/` |
| Training logs | `path/to/logs/` |
| W&B run(s) | [link](https://wandb.ai/...) |
| SLURM output | `path/to/slurm.out` |
