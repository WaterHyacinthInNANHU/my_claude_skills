---
name: auto_experiment
description: Automated experiment workflow for code + data experiments with structured planning, execution, and reporting.
---

# auto_experiment

Automated experiment workflow: workspace setup, iterative experiment loop, and result analysis.

## Agent Reading Order

```
1. This file (SKILL.md)       — Full workflow, steps 1-5
2. CLAUDE.md.template          — Installed to workspace; session protocol, context rules
3. Templates (sketch.md, etc.) — Used during setup, not read at runtime
```

## Inputs

| Input | Description | Required |
|-------|-------------|----------|
| **code** | Path to code repository or URL | Yes |
| **data** | Path to dataset | Yes |
| **workspace** | Path for experiment workspace | Yes |
| **instruction** | What experiment to run | Yes |

## Workflow Overview

```
Step 1: Confirm Inputs → Step 2: Setup Workspace → Step 3: Plan
                                                       ↓
Step 5: Final Report  ←──── Step 4: Experiment Loop
                              ┌→ Setup Round (branch)
                              │→ Run (launch)
                              │→ Monitor (early stop?)
                              │→ Analyze (diagnose)
                              │→ Propose (next hypothesis)
                              └── Loop until done
```

---

## Step 1: Confirm Inputs & Understand Instructions

1. Verify all paths exist and are accessible
2. Understand the experiment instruction
3. **ASK USER** for clarification on:
   - Unclear requirements
   - Missing parameters (seeds, epochs, GPUs, etc.)
   - Success metric to track
   - Expected outcomes

**Validation checklist:**
- [ ] Code path exists and is a valid git repo (or clonable URL)
- [ ] Data path exists and contains expected files
- [ ] Workspace path parent directory exists
- [ ] Experiment instruction is clear and actionable
- [ ] Success metric defined (e.g., val_loss, accuracy, reward)

---

## Step 2: Create Workspace

### Run Setup Script

```bash
# Automated setup
./scripts/setup.sh \
  --code <code_path> \
  --data <data_path> \
  --workspace <workspace_path> \
  --tag <experiment_tag>
```

Or manually:

```bash
mkdir -p <workspace>/{outputs,logs,doc/agent,.claude/hooks,scripts}

# Code: clone on new branch
cd <workspace>
git clone <code_path> code
cd code && git checkout -b autoresearch/<tag>

# Data: symlink only (NEVER copy or modify)
ln -s <data_path> <workspace>/data

# Initialize tracking
echo -e "commit\tmetric\tmemory_gb\tstatus\tdescription" > results.tsv

# Initialize context files
touch doc/agent/{sketch.md,architecture.md,findings.md}

# Install scripts and hooks
cp <skill_path>/templates/scripts/*.sh scripts/ && chmod +x scripts/*.sh
cp <skill_path>/templates/hooks/restore-context.sh .claude/hooks/ && chmod +x .claude/hooks/restore-context.sh
cp <skill_path>/templates/hooks/settings.json .claude/settings.json
```

### Branch Naming

Pattern: `autoresearch/<tag>` (from [Karpathy's autoresearch](https://github.com/karpathy/autoresearch))

```bash
autoresearch/mar22            # workspace branch
autoresearch/mar22-r1         # round 1
autoresearch/mar22-r2         # round 2
```

### Workspace Structure

```
<workspace>/
├── code/                    # Git repo on experiment branch
├── data -> /path/to/data    # SYMLINK only
├── outputs/                 # Training outputs, checkpoints
├── logs/                    # Training logs (per-round: train_r1.log, etc.)
├── doc/agent/               # High-level context (see CLAUDE.md)
│   ├── sketch.md            # Current state & next steps
│   ├── architecture.md      # Design decisions
│   ├── findings.md          # Accumulated insights & baselines
│   └── exp_r*.md            # Per-round analysis reports
├── scripts/                 # Utility scripts (monitor, cleanup, archive)
├── results.tsv              # Experiment results tracking
├── CLAUDE.md                # Agent instructions (from template)
└── .claude/hooks/           # SessionStart context restoration
```

### Write CLAUDE.md

Copy from `templates/CLAUDE.md.template`, fill in `{{placeholders}}`.

CLAUDE.md is the **single source of truth** for:
- Session start/end protocol
- Context update triggers
- Early stopping heuristics
- Experiment loop protocol
- Data and logging rules

### Experiment ID Convention

Rounds use sequential integers: `r1`, `r2`, `r3`, ...

| ID | Branch | Log | Report |
|----|--------|-----|--------|
| r1 | `autoresearch/<tag>-r1` | `logs/train_r1.log` | `doc/agent/exp_r1.md` |
| r2 | `autoresearch/<tag>-r2` | `logs/train_r2.log` | `doc/agent/exp_r2.md` |

---

## Step 3: Plan Experiment

### 3.1 Initialize sketch.md

```markdown
# Experiment Sketch

## Current State
- Phase: planning
- Last action: workspace setup complete
- Blocking issues: none

## Goal
<instruction from user>

## Baselines
| Source | Metric | Value | Notes |
|--------|--------|-------|-------|
| Paper  |        |       |       |

## Approach
<to be determined after codebase exploration>

## Next Steps
1. [ ] Understand codebase
2. [ ] Identify files to modify
3. [ ] Define plan
```

### 3.2 Explore Codebase

Read and document in `doc/agent/architecture.md`:
- Entry point / training script
- Config files and key hyperparameters
- Model architecture
- Data loading pipeline
- Evaluation code and metrics

### 3.3 Create Plan in sketch.md

Update with:
- Phases and steps
- Success metric and target value
- Baseline numbers (from paper, prior work)
- Key decisions made

**ASK USER** about unclear implementation choices before proceeding.

---

## Step 4: Iterative Experiment Loop

```
┌→ 4.1 Setup Round → 4.2 Run → 4.3 Monitor → 4.4 Analyze → 4.5 Propose →┐
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.0 Smoke Test (First Round Only)

```bash
python train.py --epochs 1 --debug 2>&1 | tee logs/smoke_test.log
```

Verify: imports resolve, data loads, forward/backward pass works, metrics compute, no OOM. Fix before entering loop.

### 4.1 Setup Round

```bash
git checkout autoresearch/<tag>
git checkout -b autoresearch/<tag>-r<N>

# Make changes, commit
git add -A && git commit -m "r<N>: <hypothesis>"

# Record rationale
git notes add -m "Round <N>: <hypothesis>
Changes from r<N-1>: <what changed>
Motivation: <why>
Expected: <what we hope to see>" HEAD
```

### 4.2 Run

```bash
nohup python train.py <args> > logs/train_r<N>.log 2>&1 &
echo $! > logs/train.pid
```

### 4.3 Monitor with Early Stopping

**Context-efficient monitoring (DO NOT use `tail -f`):**

```bash
# Preferred: background monitor (only outputs on metric changes)
./scripts/monitor.sh --log logs/train_r<N>.log --pid $(cat logs/train.pid) --interval 120

# Or sparse polling
grep -E "(loss|epoch|val_)" logs/train_r<N>.log | tail -3
```

**Early stopping — compare against baselines (from findings.md):**

| Training % | STOP if | CONTINUE if |
|------------|---------|-------------|
| First 100 steps | Loss NaN/Inf/increasing | Steady decrease |
| ~5% | Loss >5x baseline at same point | Within 2x baseline |
| ~10% | Val metric flat or random-level | Trending up |
| ~25% | Significantly below baseline curve | Comparable |
| ~50% | Plateaued well below baseline | On track |

### 4.4 Analyze

**After completion OR early stop — THINK before next round:**

```bash
# Record result
echo -e "$(git rev-parse --short HEAD)\t<metric>\t<memory_gb>\t<status>\t<description>" >> results.tsv
```

Write `doc/agent/exp_r<N>.md` (use `templates/exp_log.md.template`):

```markdown
## Round <N> Analysis

### Result
- Status: [completed | early_stopped at epoch X/Y]
- Metric: <value> (baseline: <value>, prev round: <value>)

### Diagnosis
If worse → root cause? (optimization / data / architecture / bug?)
If better → which change drove it?

### Patterns
- <new observations across rounds>

### Proposed Next
- Hypothesis: ...
- Changes: ...
```

Update `doc/agent/findings.md` with new patterns and baselines.

**Systematic failure diagnosis:**
1. **Optimization** — LR too high/low? Gradient issues? Wrong optimizer?
2. **Data** — Preprocessing correct? Shuffling? Augmentation too aggressive?
3. **Architecture** — Model capacity? Activation/normalization? Init?
4. **Bug** — Shape mismatch? Wrong loss? Compare with reference impl

### 4.5 Propose & Loop

| Outcome | Action |
|---------|--------|
| Target metric achieved | **Exit loop** → Step 5 |
| Promising, push further | **New round** in same direction |
| Failed, new hypothesis | **New round** with different approach |
| All hypotheses exhausted | **Exit loop** → Step 5 (report findings) |
| User requests stop | **Exit loop** |

```bash
# If successful round, merge back
git checkout autoresearch/<tag> && git merge autoresearch/<tag>-r<N>

# If failed, leave branch and go back
git checkout autoresearch/<tag>

# Update sketch.md → Go to 4.1
```

### Error Recovery

| Error | Recovery |
|-------|----------|
| Training crashes mid-run | Check logs, fix bug, re-run same round |
| OOM | Reduce batch size, enable gradient checkpointing |
| Disk full | Run `./scripts/cleanup.sh`, clear old checkpoints |
| Git state corrupted | `git reflog` to find last good state |
| Stale sketch.md | Check `git log --show-notes` for ground truth |
| Job killed (SLURM timeout) | Adjust time limit, resume from checkpoint if available |

### Cross-Session Long-Running Jobs

If training runs longer than a session:
1. Update sketch.md with: phase=training, job ID, expected completion
2. End session
3. Next session: hook restores context, agent checks job status
4. `squeue -j <id>` or `kill -0 $(cat logs/train.pid)` to verify

---

## Step 5: Analyze Results & Report

Use the experiment report skill:
```
/experiment_report
```

Save to `doc/agent/final_report.md`. Include:
1. **Motivation** — Hypothesis and context
2. **Setup** — Full reproducibility details
3. **Results** — All rounds summarized, best result highlighted
4. **Analysis** — What worked, patterns, recommendations

```bash
# Final commit
git add -A && git commit -m "experiment complete: <summary>"
git notes add -m "Final: <best metric>, <N> rounds, <key finding>" HEAD
```

---

## Context Management

**CLAUDE.md is the single source of truth for all context rules.**

Summary of the architecture:

```
doc/agent/sketch.md       ← Current state (updated frequently)
doc/agent/architecture.md ← Design decisions (append as needed)
doc/agent/findings.md     ← Patterns & baselines (append as needed)
doc/agent/exp_r*.md       ← Per-round reports (one per round)
git notes                 ← Implementation details (per commit)
results.tsv               ← Metrics (append per round)
```

**Restoration:** SessionStart hook auto-injects sketch.md + recent history.
**Updates:** Incremental triggers defined in CLAUDE.md.

### Sketch.md Size Management

If sketch.md grows beyond ~100 lines:
1. Move completed session log entries to `doc/agent/findings.md`
2. Summarize old "Key Decisions" into architecture.md
3. Keep sketch.md focused on: current state, next steps, open questions

---

## Workspace Cleanup

```bash
# Preview
./scripts/cleanup.sh --dry-run

# Execute
./scripts/cleanup.sh

# Archive first
./scripts/archive-experiment.sh <round_id>
```

| Item | Default | Protected |
|------|---------|-----------|
| Checkpoints | Keep last 3 | No |
| Logs | Keep 30 days | No |
| Git branches | Delete merged | No |
| Context files | — | **Yes** |
| Data symlink | — | **Yes** |
| results.tsv | — | **Yes** |

---

## Results Schema

**Authoritative column definition** (all files must use these exact names):

| Column | Type | Description |
|--------|------|-------------|
| `commit` | string | Short git hash |
| `metric` | float | Primary success metric value |
| `memory_gb` | float | Peak GPU memory in GB |
| `status` | enum | `success`, `early_stop`, `failed`, `baseline` |
| `description` | string | What was tried |

```bash
echo -e "$(git rev-parse --short HEAD)\t<metric>\t<memory_gb>\t<status>\t<description>" >> results.tsv
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `cat doc/agent/sketch.md` | Check current state |
| `git log --oneline -5 --show-notes` | Recent history |
| `column -t -s $'\t' results.tsv` | View all results |
| `git notes add -m "..." HEAD` | Add implementation details |
| `./scripts/monitor.sh --log <f> --pid <p>` | Monitor training |
| `./scripts/cleanup.sh --dry-run` | Preview cleanup |
| `./scripts/archive-experiment.sh <id>` | Archive experiment |
