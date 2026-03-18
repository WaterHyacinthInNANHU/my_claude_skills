---
name: experiment_report
description: Write structured experiment reports for robot learning and AI research.
---

# experiment_report

Generate structured experiment reports for robot learning / AI research. Reports are designed to be **scannable** — a reader should get the key takeaway from the TL;DR and summary table without reading the full report.

## When to Use

- After completing an experiment run
- When documenting ablations or comparisons
- When proposing next experiments based on findings
- When writing to Notion, markdown, or any structured doc

## Report Structure

### 0. Header & TL;DR

Every report starts with metadata and a 1-2 sentence conclusion.

Required fields:
- **Title** — descriptive, includes the main result (e.g., "DAgger Flow PC 1024+1024: 94% Success")
- **Date** — YYYY-MM-DD
- **Project** — project name
- **Status** — success | partial | failed | in-progress
- **TL;DR** — Lead with the conclusion. State the best result and the key insight in 1-2 sentences. This is the most important part — a busy reader may only see this.

### 1. Results Summary (FIRST, before setup)

Put the results table **at the top**, not buried after methodology. Readers want to see numbers immediately.

**Comparison table** — always include, even for single experiments (compare against baseline):

| Experiment | Key Metric 1 | Key Metric 2 | Training Time | W&B | Status |
|------------|-------------|-------------|---------------|-----|--------|

Rules for the results table:
- **Bold the best result** in each metric column
- **Include W&B link** for every run (as inline link in experiment name or separate column)
- Include SLURM Job ID if on cluster
- Mark status: Completed / Running / Failed / Timed out
- Use consistent units and precision across rows

If there are multiple experiment groups, use separate tables with clear headers.

After the table, add a **Key Findings** section — 3-5 numbered bullet points distilling the most important insights. Each finding should be a standalone statement that doesn't require reading the rest of the report.

### 2. Motivation

Answer **why** this experiment exists in 2-4 sentences:
- What hypothesis are we testing?
- What gap in prior results does this address?
- What decision depends on the outcome?

Link to prior experiment reports if this is a follow-up.

### 3. Experiment Setup

Provide enough detail to **reproduce** the experiment:

| Item | What to include |
|------|----------------|
| **Task / Environment** | Env name, version, task variant, obs/action space |
| **Dataset** | Name, size, collection method |
| **Codebase** | Repo, branch/commit hash |
| **Hardware** | GPU type, count, SLURM partition, job IDs |
| **Hyperparameters** | Learning rate, batch size, epochs, seed(s) |
| **Baseline** | What you compare against — prior run ID or config name |
| **Config file** | Path or inline snippet |

### 4. Method

Describe **what changed** relative to the baseline:
- Algorithmic changes (new loss, architecture tweak, reward shaping)
- Data changes (filtering, augmentation, new demonstrations)
- Training recipe changes (schedule, optimizer, curriculum)

Be precise: "replaced MLP policy head with 2-layer transformer (d=256, 4 heads)" not "changed the policy network".

### 5. Detailed Results

Expand on the summary table with:
- **Training curves** — link to W&B / TensorBoard dashboard
- **Per-step metrics** — table of eval metrics at key checkpoints (e.g., every 500 steps) if training dynamics matter (collapse, recovery, convergence)
- **Qualitative observations** — rollout videos, failure mode descriptions
- **Timing** — wall-clock time per step, total training time, any timeouts or restarts

### 6. Analysis & Next Steps

Interpret results and propose actions:

- **Key findings** — numbered insights (can expand on the summary findings)
- **What went wrong** — root-cause analysis with evidence, not just "it's worse". Include the fix if found.
- **Surprising observations** — unexpected behaviors, training instabilities
- **Next experiment proposal** — concrete description with expected outcome and priority

### 7. Artifacts

Always include a reference section with paths and links:

| Artifact | Path / Link |
|----------|------------|
| Config file | `path/to/config.yaml` |
| Checkpoint (best) | `path/to/checkpoint/` |
| Training logs | `path/to/logs/` |
| W&B run | `https://wandb.ai/...` |
| SLURM output | `path/to/slurm_output.out` |

## Writing Guidelines

- **Lead with results, not setup** — the summary table comes before methodology
- Use **past tense** for what was done, **present tense** for analysis
- Lead with the conclusion: "X improved success rate by 12% over baseline"
- Attach raw numbers; don't only show plots
- **Every experiment must have a W&B link** — no exceptions
- One report per experiment batch; group related runs under a single report with sub-sections
- Date every report (YYYY-MM-DD)
- When writing to Notion: use Notion table syntax, bold the best results, include inline links
