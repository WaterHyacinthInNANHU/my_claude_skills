# Experiment Report: [TITLE]

**Date:** YYYY-MM-DD
**Author:** [name]
**Project:** [project name]
**Experiment ID:** [exp-XXX]
**Status:** success | partial | failed

---

## 1. Motivation

<!-- Why are we running this experiment? What hypothesis are we testing? -->

**Hypothesis:** [If we do X, then Y should improve because Z.]

**Context:** [Link to prior experiment or discussion that motivated this.]

---

## 2. Experiment Setup

| Item | Details |
|------|---------|
| Task / Env | |
| Dataset | |
| Repo / Branch | |
| Commit | |
| Hardware | |
| SLURM Job ID | |
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

## 3. Method

<!-- What changed compared to the baseline? Be specific. -->

**Changes:**
1.
2.
3.

---

## 4. Results

### Key Metrics

| Method | Success Rate | Return | Training Time |
|--------|-------------|--------|---------------|
| Baseline | | | |
| Ours | | | |

### Training Curves

<!-- Paste screenshot or link -->

**W&B:** [link]

### Qualitative Observations

<!-- Rollout videos, failure modes, etc. -->

---

## 5. Analysis & Next Steps

### What Worked


### What Didn't Work


### Surprising Observations


### Next Experiment Proposal

**Proposed:** [exp-XXX+1] — [one-line description]
- Change:
- Expected outcome:
- Priority: high | medium | low
