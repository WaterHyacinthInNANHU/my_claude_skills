---
name: auto_experiment
description: Automated experiment workflow for code + data experiments with structured planning, execution, and reporting.
---

# auto_experiment

Automated experiment workflow that handles workspace setup, planning, execution monitoring, and result analysis. Designed for ML/AI research experiments with proper version control and logging.

## Inputs

| Input | Description | Required |
|-------|-------------|----------|
| **code** | Path to code repository or URL | Yes |
| **data** | Path to dataset | Yes |
| **workspace** | Path for experiment workspace | Yes |
| **instruction** | What experiment to run | Yes |

## Workflow Overview

```
Step 1: Confirm Inputs → Step 2: Setup Workspace → Step 3: Plan Experiment
    ↓
Step 5: Analyze & Report ← Step 4: Execute & Monitor
```

## Step 1: Confirm Inputs & Understand Instructions

**Actions:**
1. Verify all paths exist and are accessible
2. Understand the experiment instruction
3. **ASK USER** for clarification on:
   - Unclear requirements
   - Missing parameters (seeds, epochs, etc.)
   - Expected outcomes/metrics

**Validation Checklist:**
- [ ] Code path exists and is a valid git repo (or clonable URL)
- [ ] Data path exists and contains expected files
- [ ] Workspace path parent directory exists
- [ ] Experiment instruction is clear and actionable

## Step 2: Create Workspace

### Branch Naming Convention

Use the `autoresearch/<tag>` pattern from [Karpathy's autoresearch](https://github.com/karpathy/autoresearch):

```bash
# Format: autoresearch/<date>[-<variant>]
# Examples:
autoresearch/mar17
autoresearch/mar17-ablation
autoresearch/mar17-gpu0

# Check branch doesn't exist, then create
git checkout -b autoresearch/<tag>
```

### Workspace Structure

```
<workspace>/
├── code/                    # Git worktree or clone (on experiment branch)
├── data -> /path/to/data    # SYMLINK only - never modify source data
├── outputs/                 # Training outputs, checkpoints
├── logs/                    # Training logs
├── doc/
│   └── agent/              # High-level logs (architecture, params, reports)
│       ├── sketch.md       # CRITICAL: Current state & next steps
│       ├── architecture.md # Design decisions & rationale
│       ├── findings.md     # Accumulated insights
│       └── exp_*.md        # Individual experiment reports
├── CLAUDE.md               # Agent instructions for this workspace
└── results.tsv             # Experiment results tracking
```

### Setup Commands

```bash
# Create workspace
mkdir -p <workspace>/{outputs,logs,doc/agent,.claude/hooks}

# Clone/worktree code on new branch
cd <workspace>
git clone <code_path> code  # or git worktree add
cd code
git checkout -b autoresearch/<tag>

# Symlink data (NEVER copy or modify)
ln -s <data_path> <workspace>/data

# Initialize results tracking
echo -e "commit\tmetric\tmemory_gb\tstatus\tdescription" > results.tsv

# Initialize context files
touch doc/agent/sketch.md doc/agent/architecture.md doc/agent/findings.md

# Install context restoration hook
cp <skill_path>/templates/hooks/restore-context.sh .claude/hooks/
chmod +x .claude/hooks/restore-context.sh

# Install utility scripts
mkdir -p scripts
cp <skill_path>/templates/scripts/*.sh scripts/
chmod +x scripts/*.sh

# Configure hook in .claude/settings.json
cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/restore-context.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
EOF
```

### Create CLAUDE.md

Write workspace-specific instructions to `<workspace>/CLAUDE.md`:

```markdown
# Experiment Workspace: <tag>

## Data Policy
- Data is symlinked from: <original_data_path>
- **NEVER modify the data directory**
- Local data changes go to: outputs/processed_data/

## Logging Policy
### High-level logs (doc/agent/)
- Architecture decisions
- Important hyperparameter changes
- Experiment reports
- Key findings

### Implementation details (git notes)
- Check previous implementation notes: `git notes show <commit>`
- Add implementation notes: `git notes add -m "details..." <commit>`

## Code Version Control
- Commit before any significant changes
- Create sub-branches for risky experiments: `git checkout -b <tag>-<variant>`
- Use `git reset --hard HEAD~1` to revert failed experiments

## Key Files
- Config: <path>
- Main training script: <path>
- Evaluation: <path>
```

## Step 3: Plan Experiment

**Initialize context files and create plan:**

### 3.1 Initialize Context Files

```bash
# Create initial sketch.md
cat > doc/agent/sketch.md << 'EOF'
# Experiment Sketch

## Current State
- Phase: planning
- Last action: workspace setup complete
- Blocking issues: none

## Goal
<instruction from user>

## Approach
<to be determined>

## Next Steps
1. [ ] Understand codebase structure
2. [ ] Identify files to modify
3. [ ] Define success metrics
4. [ ] Create experiment plan

## Session Log
| Date | Summary |
|------|---------|
| <today> | Initial setup |
EOF

# Create empty architecture.md
touch doc/agent/architecture.md

# Create empty findings.md
touch doc/agent/findings.md
```

### 3.2 Explore Codebase

Read and understand:
- Entry point / training script
- Config files
- Model architecture
- Data loading
- Evaluation code

Document findings in `doc/agent/architecture.md`.

### 3.3 Create Plan in sketch.md

Update `doc/agent/sketch.md` with:
- Phases and steps
- Success metrics
- Key decisions

**Planning Checklist:**
- [ ] Understand codebase structure
- [ ] Identify files to modify
- [ ] Define success metrics
- [ ] Plan ablations if needed
- [ ] **ASK USER** about unclear implementation choices
- [ ] Update sketch.md with complete plan

## Step 4: Execute & Monitor

### Stage 1: Smoke Test

Run a quick sanity check before full training:

```bash
# Short run to catch bugs
python train.py --epochs 1 --debug 2>&1 | tee logs/smoke_test.log

# Check for:
# - Import errors
# - Shape mismatches
# - CUDA/memory errors
# - Data loading issues
```

**If smoke test fails:** Fix issues before proceeding.

### Stage 2: Full Training

```bash
# Launch training with logging
nohup python train.py <args> > logs/train.log 2>&1 &

# Or with SLURM
sbatch job.sh
```

### Monitoring

```bash
# Tail logs
tail -f logs/train.log

# Check GPU usage
nvidia-smi -l 5

# Monitor SLURM job
squeue -u $USER
sacct -j <job_id> --format=JobID,State,Elapsed,MaxRSS
```

**Wait for completion** - Do not proceed until training finishes.

### Record Results

Append to `results.tsv`:

```bash
echo -e "<commit>\t<metric>\t<status>\t<description>" >> results.tsv
```

### Git Version Control During Execution

```bash
# Before changes
git add -A && git commit -m "checkpoint: <description>"

# Add implementation notes
git notes add -m "Implementation detail: ..." HEAD

# If experiment fails
git reset --hard HEAD~1

# If experiment succeeds, tag it
git tag exp-<id>-success
```

## Step 5: Analyze Results & Report

### Generate Report

Use the experiment_report skill:

```
/experiment_report
```

Save report to `doc/agent/exp_<id>_report.md`

### Report Contents

1. **Motivation** - Hypothesis and context
2. **Setup** - Full reproducibility details
3. **Method** - What changed
4. **Results** - Metrics, curves, qualitative observations
5. **Analysis** - What worked, what didn't, next steps

### Archive Artifacts

```bash
# Copy key outputs to doc/agent/
cp outputs/best_checkpoint.pt doc/agent/
cp logs/train.log doc/agent/

# Commit final state
git add -A && git commit -m "exp-<id>: <summary>"
git notes add -m "Final metrics: <...>" HEAD
```

## Context Management (Memory Preservation)

### Option A: Automatic via Hook (Recommended)

Install the SessionStart hook for automatic context restoration:

```bash
# Copy hook to workspace
mkdir -p <workspace>/.claude/hooks
cp templates/hooks/restore-context.sh <workspace>/.claude/hooks/

# Add to workspace settings (.claude/settings.json)
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/restore-context.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**What the hook does:**
- Fires on every session start (startup, resume, compact, clear)
- Reads `doc/agent/sketch.md` and injects into context
- Shows recent git history with notes
- Shows recent results from `results.tsv`
- Tells agent what triggered the restore

**Matchers available:**
| Matcher | When |
|---------|------|
| `startup` | New session |
| `resume` | Resuming session |
| `compact` | After context compaction |
| `clear` | After /clear command |
| `""` (empty) | All of the above |

### Option B: Manual via CLAUDE.md

If hooks aren't available, the CLAUDE.md template includes mandatory session protocols.

### Memory Architecture

```
Layer 1: doc/agent/sketch.md      <- Current state, next steps (UPDATE EVERY SESSION)
Layer 2: doc/agent/*.md           <- Architecture, findings, reports (APPEND AS NEEDED)
Layer 3: git notes                <- Implementation details per commit
Layer 4: results.tsv              <- Structured experiment outcomes
```

### Session Start Procedure (MANDATORY)

**Before doing any work, restore context:**

```bash
# 1. Read current state
cat doc/agent/sketch.md

# 2. Recent history
git log --oneline -5 --show-notes
tail -5 results.tsv

# 3. Confirm understanding
# - Current phase: ___
# - Last action: ___
# - Next step: ___
```

**If anything is unclear, ASK USER before proceeding.**

### Incremental Update Triggers

**Update context files as you work, not just at session end:**

| Trigger | Action |
|---------|--------|
| After significant action | Update sketch.md briefly |
| After experiment completes | results.tsv + git notes |
| After design decision | architecture.md |
| After insight | findings.md |
| Before risky change | git commit + sketch.md |
| At session end | Full sketch.md update + commit |

**Rule: If session crashes now, would the next session know what happened?**
- If no → update context files now
- If yes → continue working

### What Goes Where

| Content | Location | When Updated |
|---------|----------|--------------|
| Current state, next steps | `sketch.md` | Every session |
| Design decisions | `architecture.md` | When decisions made |
| Experiment reports | `exp_*.md` | After each experiment |
| Accumulated insights | `findings.md` | After analysis |
| Implementation details | `git notes` | Each commit |
| Experiment metrics | `results.tsv` | After each run |

## Critical Rules

| Rule | Reason |
|------|--------|
| **Never modify source data** | Use symlinks, keep changes local |
| **Two-level logging** | Core info in doc/, details in git notes |
| **Version control before changes** | Easy rollback of failed experiments |
| **Ask when unclear** | Better to clarify than waste compute |
| **Wait for completion** | Results analysis needs final outputs |
| **Update sketch.md every session** | Context preservation for multi-session work |

## Workspace Cleanup

### Cleanup Workflow

```
1. ARCHIVE successful experiments
   └── ./scripts/archive-experiment.sh <exp_id>

2. PRUNE by retention policy
   └── ./scripts/cleanup.sh --dry-run  (preview)
   └── ./scripts/cleanup.sh            (execute)

3. VERIFY before delete
   └── Script shows sizes and asks confirmation
```

### Install Scripts

```bash
cp <skill_path>/templates/scripts/*.sh <workspace>/scripts/
chmod +x <workspace>/scripts/*.sh
```

### Archive an Experiment

```bash
# Archive with best checkpoint only
./scripts/archive-experiment.sh exp_001

# Archive with all checkpoints
./scripts/archive-experiment.sh exp_001 --include-all-checkpoints
```

Creates `archives/exp_001_20260317.tar.gz` containing:
- Best/final checkpoint
- Training log
- Experiment report
- Git commit info and notes
- Config file
- Results excerpt

### Cleanup Workspace

```bash
# Preview what would be deleted
./scripts/cleanup.sh --dry-run

# Run cleanup with prompts
./scripts/cleanup.sh

# Force cleanup (no prompts)
./scripts/cleanup.sh --force

# Custom retention
./scripts/cleanup.sh --keep-checkpoints 5 --keep-logs-days 60
```

### Cleanup Policies

| Item | Default Policy | Flag |
|------|----------------|------|
| Checkpoints | Keep last 3 | `--keep-checkpoints N` |
| Logs | Keep 30 days | `--keep-logs-days N` |
| Git branches | Delete merged | automatic |
| Python cache | Delete all | automatic |
| Processed data | Ask user | prompted |
| Context files | **Never delete** | protected |
| Data symlink | **Never touch** | protected |

### What's Protected

- `doc/agent/*` - All context files
- `data` symlink - Source data reference
- `results.tsv` - Experiment tracking
- `CLAUDE.md` - Workspace instructions
- Current git branch

## Quick Reference

| Command | Purpose |
|---------|---------|
| `git checkout -b autoresearch/<tag>` | Create experiment branch |
| `ln -s <path> data` | Symlink data (never copy) |
| `cat doc/agent/sketch.md` | Restore context (session start) |
| `git log --oneline -5 --show-notes` | Check recent history |
| `git notes add -m "..." HEAD` | Add implementation details |
| `git notes show HEAD` | View implementation details |
| `./scripts/cleanup.sh --dry-run` | Preview cleanup |
| `./scripts/archive-experiment.sh <id>` | Archive experiment |
| `/experiment_report` | Generate experiment report |
