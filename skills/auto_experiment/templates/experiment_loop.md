# Iterative Experiment Loop

## Loop Overview

```
                    ┌──────────────────────────────────────────────┐
                    │                                              │
                    ▼                                              │
┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────┐  ┌─────┴────┐
│  SETUP   │→ │   RUN    │→ │   MONITOR    │→ │ ANALYZE │→ │ PROPOSE  │
│ (branch) │  │ (launch) │  │ (eval/stop)  │  │ (why?)  │  │ (next?)  │
└──────────┘  └──────────┘  └──────────────┘  └─────────┘  └──────────┘
     │                           │
     │                      Early stop?
     │                       Yes → Analyze
     │                       No  → Keep monitoring
     │
     └── New sub-branch per round: autoresearch/<tag>-r1, r2, ...
```

## Branch Strategy Per Round

```bash
# Workspace branch (base)
autoresearch/<tag>            # e.g., autoresearch/mar22

# Per-round sub-branches
autoresearch/<tag>-r1         # Round 1: baseline
autoresearch/<tag>-r2         # Round 2: adjusted LR
autoresearch/<tag>-r3         # Round 3: added augmentation
```

Each round:
1. Branch from workspace branch (or previous successful round)
2. Make changes, commit with descriptive message
3. Add git notes with full experiment rationale
4. Run experiment
5. Merge back if successful, or leave as dead branch

```bash
# Start new round
git checkout autoresearch/<tag>
git checkout -b autoresearch/<tag>-r<N>

# Record setup in git notes
git notes add -m "Round <N>: <hypothesis>
Changes: <what changed from previous round>
Motivation: <why we think this will work>
Based on: r<N-1> findings" HEAD

# After experiment
git checkout autoresearch/<tag>
git merge autoresearch/<tag>-r<N>   # if successful
```

## Evaluation Heuristics

### How to Evaluate Training Progress

**Step 1: Establish baselines**

Before judging any experiment, you need reference points:
- Published results from the paper/method
- Previous successful rounds
- Known good configurations

Record baselines in `doc/agent/findings.md`:
```markdown
## Baselines
| Source | Metric | Value | Notes |
|--------|--------|-------|-------|
| Paper  | val_acc | 0.85 | Table 2, default config |
| r1     | val_acc | 0.72 | Our baseline reproduction |
```

**Step 2: Define early indicators**

Different metrics tell you different things at different stages:

| Stage | What to Check | Healthy Sign | Bad Sign |
|-------|---------------|--------------|----------|
| First 100 steps | Loss decreasing | Steady decrease | Flat, NaN, increasing |
| ~5% of training | Loss magnitude | Within 2x of baseline at same point | >5x baseline |
| ~10% of training | Val metric trending | Improving, even slowly | Flat or worse than random |
| ~25% of training | Learning curve shape | Comparable to baseline curve | Significantly below baseline |
| ~50% of training | Convergence rate | On track to match/beat baseline | Plateaued well below baseline |

**Step 3: Compare against successful runs**

```bash
# Extract metric progression from current run
grep -E "epoch|val_" logs/train.log | tail -10

# Compare with previous successful run (from git notes)
git notes show autoresearch/<tag>-r<prev_successful>
```

### Early Stopping Decision Matrix

| Condition | Action | Confidence |
|-----------|--------|------------|
| Loss is NaN/Inf | **STOP immediately** | Certain failure |
| OOM error | **STOP**, reduce batch/model size | Certain failure |
| Loss not decreasing after 10% of training | **STOP**, investigate | High confidence |
| Val metric >30% worse than baseline at 25% mark | **STOP**, likely won't recover | High confidence |
| Val metric 10-30% worse than baseline at 50% mark | **STOP**, diminishing returns | Medium confidence |
| Val metric within 10% of baseline, different trend | **Continue**, may catch up | Low confidence |
| Val metric improving but slowly | **Continue**, be patient | Let it run |

### What to Record When Early Stopping

```bash
# 1. Record the decision
echo -e "$(git rev-parse --short HEAD)\t<metric_at_stop>\t<mem>\tearly_stop\t<reason>" >> results.tsv

# 2. Save the training curve up to stop point
grep -E "(loss|val_)" logs/train.log > doc/agent/r<N>_curve.txt

# 3. Git notes with analysis
git notes add -m "EARLY STOPPED at epoch <X>/<total>
Reason: <specific reason>
Metric at stop: <value> (baseline was <value> at same point)
Hypothesis: <why it failed>" HEAD
```

## Post-Experiment Analysis

### Structured Analysis Template

After each round (early stopped or completed), fill this out:

```markdown
## Round <N> Analysis

### Result
- Status: [completed | early_stopped at epoch X/Y]
- Final metric: <value>
- vs Baseline: [+/-]<delta> (<percentage>%)
- vs Previous round: [+/-]<delta>

### What Changed (from previous round)
- <change 1>
- <change 2>

### Diagnosis
**If failed/worse:**
- Root cause hypothesis: <what went wrong>
- Evidence: <what in the logs/metrics supports this>
- Contributing factors: <secondary issues>

**If improved:**
- What helped: <what change drove the improvement>
- Evidence: <metric comparison>
- Remaining gap: <how far from target>

### Patterns Observed
- <pattern 1: e.g., "LR > 1e-3 always diverges on this dataset">
- <pattern 2>

### Proposed Next Steps
1. <specific change with rationale>
2. <alternative if #1 fails>
3. <longer-term investigation>
```

### Analysis Thinking Process

**For failures, systematically check:**

1. **Optimization issues**
   - Learning rate too high/low?
   - Gradient exploding/vanishing?
   - Wrong optimizer settings?

2. **Data issues**
   - Correct preprocessing?
   - Data loading order/shuffling?
   - Augmentation too aggressive?

3. **Architecture issues**
   - Model too small/large for data?
   - Wrong activation/normalization?
   - Initialization problem?

4. **Implementation bugs**
   - Compare with reference implementation
   - Check shapes, dtypes
   - Verify loss computation

**For improvements, identify:**
- Which specific change drove it?
- Is the improvement consistent or noisy?
- Is there further room to push this direction?

## Loop Protocol in CLAUDE.md

```markdown
## EXPERIMENT LOOP PROTOCOL

### Before Each Round

1. Review findings.md - what patterns have we seen?
2. Review results.tsv - what's worked, what hasn't?
3. Check git notes from relevant previous rounds
4. Formulate specific hypothesis for this round
5. Create sub-branch: autoresearch/<tag>-r<N>
6. Record hypothesis in git notes

### During Each Round

1. Launch experiment
2. Monitor with early stopping heuristics
3. Compare against baselines at checkpoints (10%, 25%, 50%)
4. Early stop if clearly failing (see decision matrix)

### After Each Round

1. Record result in results.tsv
2. Fill out analysis template in doc/agent/exp_r<N>.md
3. Update findings.md with new patterns
4. Propose next round changes
5. Update sketch.md with current state

### Loop Termination Conditions

- Target metric achieved
- All reasonable hypotheses exhausted
- User requests stop
- Resource budget exceeded
```
