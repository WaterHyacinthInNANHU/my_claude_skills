# Mode: Auto

Automated graph search over the idea refinement tree. Orchestrates evaluate -> propose -> iterate cycles until convergence or budget exhaustion.

## Trigger

User says: "auto-explore this idea", "auto mode", "automatically refine this".

## Composability

- **Orchestrates**: evaluate, propose (and transitively, survey)
- **Standalone**: runs the full loop autonomously, pausing only at key decision points

## Concept

Treats idea refinement as **tree search**:
- **State** = idea version + validation scores
- **Goal** = all dimensions >= convergence_threshold
- **Heuristic** = weighted average of scores (weights from config.md)
- **Start node** = current idea version (detected from git branch)

## Parameters (from config.md, all overridable per invocation)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `strategy` | best-first | best-first / BFS / DFS |
| `max_iterations` | 5 | Max evaluate-propose cycles |
| `beam_width` | 3 | Directions to evaluate per iteration |
| `convergence_threshold` | 4.0 | Min score for all dimensions |
| `max_depth` | 3 | Max refinement depth from start node |

## Algorithm

### 1. Initialize

```bash
# Detect start node
BRANCH=$(git branch --show-current)
python3 scripts/status.py --json    # machine-readable state
cat config.md                       # load search parameters
```

Parse auto-mode parameters from config.md. User can override inline:
- `/idea_refinery auto --beam_width 2 --max_iterations 3`

Initialize:
- `frontier = [current_node]`
- `best_score = current weighted average (or 0 if unscored)`
- `stagnation_counter = 0`
- `iteration = 0`

### 2. Main Loop

```
WHILE iteration < max_iterations:
    iteration += 1

    # EVALUATE current node (if not already scored)
    Run evaluate mode on current node
    current_scores = parse validation scores

    # GOAL CHECK
    IF all dimensions >= convergence_threshold:
        CONVERGE: merge back to parent, stop
        BREAK

    # PROPOSE directions
    Run propose mode (beam_width directions)
    # propose mode handles: generate, survey, evaluate each direction

    # COLLECT results
    candidates = [evaluated directions from propose]

    # UPDATE frontier
    FOR each candidate:
        IF candidate.weighted_avg > current_scores.weighted_avg - 0.5:
            ADD to frontier (skip obviously worse candidates)
        ELSE:
            MARK as dead end

    # SELECT next node (strategy-dependent)
    SWITCH strategy:
        best-first: pick highest weighted_avg from entire frontier
        BFS: pick highest weighted_avg at shallowest depth
        DFS: pick highest weighted_avg at deepest depth

    # Check depth limit
    IF selected.depth > max_depth:
        SKIP, pick next from frontier

    # STAGNATION check
    IF best_score improved by <= 0.1:
        stagnation_counter += 1
    ELSE:
        stagnation_counter = 0
        best_score = new best

    IF stagnation_counter >= 2:
        STOP: "No improvement in 2 iterations. Best version: X"
        BREAK

    # SWITCH to selected node
    git checkout <selected_branch>
    current_node = selected

    # CHECKPOINT
    Update sketch.md with iteration summary
    git commit -m "auto(iter N): exploring <node> -- avg=X.X"
```

### 3. Convergence Actions

When the loop exits (convergence, stagnation, or budget):

```bash
# Report final state
python3 scripts/status.py

# If converged: merge best back to parent
git checkout ideate/<tag>
git merge <best_branch>
git commit -m "auto: converged on <best_version> after N iterations"
```

### 4. Present Results to User

**ASK USER:**

```markdown
## Auto Mode Complete

**Result:** <converged / stagnated / budget exhausted>
**Iterations:** N
**Best version:** <version> (avg=X.X)
**Convergence:** <which dimensions met / which still below threshold>

### Exploration Summary
| Iter | Node | Avg Score | Action |
|------|------|-----------|--------|
| 1 | v0 | 3.2 | proposed A, B, C |
| 2 | A | 3.8 | proposed A.1, A.2 |
| 3 | A.1 | 4.1 | converged |

### Dimensions Still Below Threshold
| Dimension | Score | Threshold | Suggestion |
|-----------|-------|-----------|-----------|
| Risk | 3/5 | 4.0 | Add fallback plan for X |
```

- "Want me to continue iterating?"
- "Want to write the final proposal? (`/idea_refinery converge`)"
- "Want to manually explore a specific direction?"

## Guardrails

- **Never auto-merge without convergence** -- only merge when all dims >= threshold
- **Always checkpoint** between iterations so user can review git log
- **Respect hard constraints** from config.md -- auto-reject violating directions
- **Pause on major pivots** -- if best candidate is in a completely different direction than current, ask user before switching
