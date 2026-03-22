# Experiment Analysis Guide

> Reference material for Step 4.4 (Analyze) of the experiment loop.
> The loop workflow itself is defined in SKILL.md Step 4.

## Post-Round Analysis Template

Copy this to `doc/agent/exp_r<N>.md` after each round:

```markdown
## Round <N> Analysis

### Result
- Status: [completed | early_stopped at epoch X/Y]
- Metric: <value>
- vs Baseline: [+/-]<delta> (<percentage>%)
- vs Previous round: [+/-]<delta>

### What Changed (from previous round)
- <change 1>
- <change 2>

### Diagnosis
**If failed/worse:**
- Root cause: <what went wrong>
- Evidence: <what in the logs/metrics supports this>
- Contributing factors: <secondary issues>

**If improved:**
- What helped: <which change drove the improvement>
- Evidence: <metric comparison>
- Remaining gap: <how far from target>

### Patterns Observed
- <e.g., "LR > 1e-3 always diverges on this dataset">

### Proposed Next Round
1. <specific change with rationale>
2. <alternative if #1 fails>
```

## Failure Diagnosis Checklist

Work through systematically — don't guess:

### 1. Optimization
- [ ] Learning rate too high? (loss exploding, NaN)
- [ ] Learning rate too low? (loss barely moving)
- [ ] Gradient issues? (vanishing or exploding)
- [ ] Wrong optimizer or wrong beta/momentum?
- [ ] Missing warmup or wrong schedule?

### 2. Data
- [ ] Preprocessing correct? (normalization, tokenization)
- [ ] Data loading order? (shuffling, sampling)
- [ ] Augmentation too aggressive? (losing signal)
- [ ] Train/val split leaking?
- [ ] Wrong data path? (loading cached/stale data)

### 3. Architecture
- [ ] Model too small for task complexity?
- [ ] Model too large for data amount? (overfitting)
- [ ] Wrong activation or normalization?
- [ ] Initialization problem?
- [ ] Missing dropout or regularization?

### 4. Implementation Bugs
- [ ] Shape mismatch (silent broadcasting)?
- [ ] Wrong loss function or reduction?
- [ ] Metric computed incorrectly?
- [ ] Compare with reference implementation line-by-line
- [ ] Check dtypes (fp16 overflow?)

## How to Establish Baselines

Record in `doc/agent/findings.md` before first experiment round:

```markdown
## Baselines
| Source | Metric | Value | Config | Notes |
|--------|--------|-------|--------|-------|
| Paper Table X | val_acc | 0.85 | default | Reported result |
| Their repo | val_acc | 0.83 | default | Our reproduction |
| r1 (ours) | val_acc | 0.72 | default | First attempt |
```

Where to find baseline numbers:
1. Paper's results tables
2. Reference repo README or logs
3. Run the default config unchanged (r1 = baseline)

## Pattern Tracking

After 3+ rounds, look for patterns in `findings.md`:

```markdown
## Patterns
1. LR > 1e-3 diverges on this dataset (r1, r3)
2. Batch size 64 gives best memory/performance tradeoff (r2, r4)
3. Augmentation hurts when data < 10k samples (r5)
```

Use patterns to avoid repeating failed approaches.
