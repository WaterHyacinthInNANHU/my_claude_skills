# Context Management Guide

## Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: doc/agent/                                        │
│  ├── sketch.md          <- Current state & next steps       │
│  ├── architecture.md    <- Design decisions & rationale     │
│  ├── exp_*.md           <- Individual experiment reports    │
│  └── findings.md        <- Accumulated insights             │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: git notes                                         │
│  └── Per-commit implementation details                      │
│      - What was tried                                       │
│      - Why it worked/failed                                 │
│      - Debug steps taken                                    │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: results.tsv                                       │
│  └── Structured experiment outcomes                         │
└─────────────────────────────────────────────────────────────┘
```

## What Goes Where

### doc/agent/sketch.md (Primary Context File)

**Updated at:** End of every session and after major milestones

```markdown
# Experiment Sketch

## Current State
- Phase: [setup/planning/running/analyzing]
- Last action: <what was done>
- Blocking issues: <if any>

## Goal
<What we're trying to achieve>

## Approach
<High-level strategy, not implementation details>

## Key Decisions Made
1. <decision>: <rationale>
2. ...

## Next Steps
1. [ ] <immediate next action>
2. [ ] <following action>
3. ...

## Open Questions
- <unresolved question>

## Session Log
| Date | Summary |
|------|---------|
| ... | ... |
```

### doc/agent/architecture.md

**Updated at:** When design decisions are made

- Model architecture choices
- Data pipeline design
- Training strategy
- Evaluation approach
- Why alternatives were rejected

### doc/agent/findings.md

**Updated at:** After each experiment analysis

- What hypotheses were tested
- What worked / didn't work
- Patterns observed
- Insights for future experiments

### git notes (Implementation Details)

**Updated at:** Each commit

```bash
git notes add -m "
## Changes
- Modified learning rate schedule

## Why
- Previous schedule caused loss spikes at epoch 50

## Tried but didn't work
- Warmup for 1000 steps (too slow)
- Cosine decay (unstable)

## Debug notes
- Loss spike correlated with batch size change
" HEAD
```

## Context Restoration Procedure

**Agent must follow this at session start:**

### Step 1: Read Sketch (30 seconds)
```bash
cat doc/agent/sketch.md
```
Understand: current phase, last action, next steps, blocking issues.

### Step 2: Check Recent History (30 seconds)
```bash
# Recent commits with notes
git log --oneline -10 --show-notes

# Recent results
tail -10 results.tsv
```
Understand: what experiments were run, outcomes.

### Step 3: Read Relevant Details (if needed)
```bash
# If continuing specific experiment
git notes show <commit>

# If blocked on architecture question
cat doc/agent/architecture.md

# If analyzing patterns
cat doc/agent/findings.md
```

### Step 4: Confirm Understanding
Before proceeding, state:
- Current phase
- What was last done
- What needs to happen next
- Any blockers

**If unclear:** Ask user for clarification rather than guessing.

## Context Save Procedure

**Agent must follow this at session end or milestones:**

### Step 1: Update Sketch
```markdown
## Current State
- Phase: <current>
- Last action: <what you just did>
- Blocking issues: <any>

## Next Steps
1. [ ] <immediate next>
2. [ ] ...
```

### Step 2: Commit Implementation Details
```bash
git notes add -m "<implementation details>" HEAD
```

### Step 3: Update Results (if experiment completed)
```bash
echo -e "<commit>\t<metric>\t<status>\t<description>" >> results.tsv
```

### Step 4: Update Findings (if insights gained)
Append to `doc/agent/findings.md`

## Quick Reference

| When | Update What |
|------|-------------|
| Session start | Read sketch.md → git log → notes |
| Made design decision | architecture.md |
| Completed experiment | results.tsv, exp_N.md |
| Gained insight | findings.md |
| Any commit | git notes |
| Session end / milestone | sketch.md |

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| Put implementation details in sketch.md | Use git notes |
| Leave sketch.md stale | Update at session end |
| Skip context restoration | Always follow the procedure |
| Assume you remember | Read the docs |
| Put everything in one file | Use appropriate layer |
