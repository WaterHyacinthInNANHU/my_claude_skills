---
name: experiment_report
description: Write structured experiment reports for robot learning and AI research.
---

# experiment_report

Generate structured experiment reports for robot learning / AI research. Reports follow a 5-section format: Motivation, Setup, Method, Results, Analysis.

## When to Use

- After completing an experiment run
- When documenting ablations or comparisons
- When proposing next experiments based on findings

## Report Sections

### 1. Motivation

Answer **why** this experiment exists:
- What hypothesis are we testing?
- What gap in prior results does this address?
- What decision depends on the outcome?

Keep it to 2-4 sentences. Link to prior experiment reports if this is a follow-up.

### 2. Experiment Setup

Provide enough detail to **reproduce** the experiment:

| Item | What to include |
|------|----------------|
| **Task / Environment** | Env name, version, task variant, observation/action space |
| **Dataset** | Name, size, collection method, train/val/test split |
| **Codebase** | Repo, branch/commit hash, any patches applied |
| **Hardware** | GPU type, count, node name, SLURM job ID if on cluster |
| **Hyperparameters** | Learning rate, batch size, epochs, seed(s), any sweep ranges |
| **Baseline** | What you compare against — prior run ID, published number, or config name |
| **Config file** | Path or inline snippet of the config used |

### 3. Method

Describe **what changed** relative to the baseline:
- Algorithmic changes (new loss, architecture tweak, reward shaping)
- Data changes (filtering, augmentation, new demonstrations)
- Training recipe changes (schedule, optimizer, curriculum)

Be precise: "replaced MLP policy head with 2-layer transformer (d=256, 4 heads)" not "changed the policy network".

### 4. Results

Present outcomes with **numbers and evidence**:

| What | Format |
|------|--------|
| **Key metrics** | Table with baseline vs. experiment (mean +/- std over N seeds) |
| **Training curves** | Screenshot or link to W&B / TensorBoard |
| **Qualitative** | Rollout videos, failure mode descriptions |
| **W&B link** | Direct link to the run or group |
| **Artifacts** | Checkpoint path, evaluation logs |

Always include:
- Success rate or return (with confidence intervals when possible)
- Wall-clock training time
- Whether the result is statistically significant or just a single seed

### 5. Analysis & Next Steps

Interpret results and propose actions:

- **What worked / didn't work** — root-cause analysis, not just "it's worse"
- **Surprising observations** — unexpected behaviors, training instabilities
- **Ablation ideas** — which component to isolate next
- **Next experiment proposal** — concrete description with expected outcome
- **Decision** — keep, discard, or iterate on this direction

## Writing Guidelines

- Use **past tense** for what was done, **present tense** for analysis
- Lead with the conclusion: "X improved success rate by 12% over baseline"
- Attach raw numbers; don't only show plots
- One experiment per report; group related runs under a single report with sub-sections
- Date every report (YYYY-MM-DD)
- Tag with project name and experiment ID for searchability
