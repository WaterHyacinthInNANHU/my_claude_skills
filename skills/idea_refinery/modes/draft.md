# Mode: Draft

Generate or update a readable proposal snapshot from the current idea version. Follows the same structure as the final proposal template but acknowledges gaps. Meant for the user to review progress at any point during exploration.

## Trigger

User says: "show me the current proposal", "draft what we have", "write up the current idea", "update the draft", "what does the idea look like now?".

## Composability

- **Standalone**: user wants to read current state as a coherent document
- **Does not call** other modes — works purely from existing data
- **Repeatable**: regenerate after each refinement cycle to track how the proposal evolves

## Output

Saved to `doc/proposals/draft.md`. Overwritten on each invocation (git tracks history).

## Procedure

### 1. Gather Current State

```bash
python3 scripts/status.py                    # tree, scores, convergence
cat config.md                                # constraints, goal
```

Read the current idea card from `doc/agent/idea_versions/`.
Read `doc/agent/findings.md` for accumulated insights.
Read `doc/agent/decisions.md` for design choices made.

### 2. Gather References

```bash
python3 scripts/refs.py list --relevance high   # key papers
python3 scripts/refs.py links <current_version>  # papers linked to this version
```

### 3. Write Draft Proposal

Write `doc/proposals/draft.md` following the **same structure as `proposal.md.template`**, but marking incomplete sections. Use `[TBD]` for sections without enough data yet.

```markdown
# <Idea Title> (Draft)

> **Version:** <current version>
> **Branch:** <current branch>
> **Last updated:** <date>
> **Status:** Draft — <N> dimensions below threshold
> **Refined through:** <N> iterations, <M> papers reviewed

---

## Brief

> **One-liner:** <single sentence describing the core idea>
> **Key insight:** <what makes this different from existing work>
> **Scores:** N:X T:X C:X F:X R:X (avg=X.X, threshold=X.X)
> **Gaps:** <dimensions below threshold and what's needed to close them>
> **Next action:** <what should happen next — e.g., "evaluate after adding risk mitigation">

---

## Abstract

<3-5 sentences: problem, approach, expected contribution. Best-effort from current state.>

---

## 1. Problem Statement

### 1.1 Background
<From idea card + findings: what area, why it matters>

### 1.2 Current Limitations
<From refs.db + validation: what existing methods fail at>

| Current Approach | Limitation | Evidence |
|-----------------|-----------|---------|
| [Method](link) | ... | ... |

### 1.3 Research Gap
<The specific gap — may be tentative if novelty not fully validated>

---

## 2. Related Work

Organize by sub-topic from refs.db.

### 2.1 <Sub-topic A>

| Paper | Year | Key Contribution | Relation to Ours |
|-------|------|-----------------|-----------------|
| [Title](link) | ... | ... | ... |

### 2.2 Positioning
<How our work fits — from validation novelty check>

---

## 3. Proposed Method

### 3.1 Overview
<From idea card: current method description>

### 3.2 Architecture / Pipeline
<ASCII diagram if concrete enough, otherwise [TBD]>

### 3.3 Key Components
<From idea card, broken into components>

### 3.4 Design Choices

| Choice | Alternatives Considered | Why This One | Evidence |
|--------|----------------------|-------------|---------|
| <from decisions.md> | ... | ... | ... |

---

## 4. Novelty & Contribution

### 4.1 What's New
<From validation novelty check>

### 4.2 Differentiation from Closest Work

| Aspect | [Closest Paper](link) | Ours | Why Different |
|--------|---------------------|------|--------------|
| ... | ... | ... | ... |

### 4.3 Expected Contributions
<From idea card strengths + validation contribution assessment>

---

## 5. Theoretical Justification

<From validation theory check. [TBD] if not yet evaluated.>

---

## 6. Experiment Plan

### 6.1 Baselines

| # | Baseline | Paper | Code | Why Compare | Expected Gap |
|---|----------|-------|------|-------------|-------------|
| B1 | ... | [link](link) | [repo](link) / none | ... | ... |

**Baseline resource requirements:**

| Baseline | GPUs | Training Time | Data | Notes |
|----------|------|--------------|------|-------|
| B1 | ... | ... | ... | <from paper or repo inspection> |

### 6.2 Minimum Viable Experiment (Phase 1)

| Experiment | Purpose | Benchmark | Baselines | Metric | Estimated Cost |
|-----------|---------|-----------|-----------|--------|---------------|
| ... | ... | ... | B1, B2 | ... | ... |

**Resource requirements (Phase 1):**

| Item | Ours | Baselines (total) | Combined |
|------|------|-------------------|----------|
| GPU-hours | ... | ... | ... |

**Success criteria:** ...
**Failure plan:** ...

### 6.3 Full Evaluation (Phase 2)

| Experiment | Benchmark | Baselines | Metric | Estimated Cost |
|-----------|-----------|-----------|--------|---------------|
| ... | ... | ... | ... | ... |

[TBD if not enough info yet]

### 6.4 Ablation Studies

| Ablation | What It Tests | Expected Outcome | Cost |
|---------|--------------|-----------------|------|
| ... | ... | ... | ... |

[TBD if method not concrete enough]

---

## 7. Resource Plan (Total)

| Resource | Required | Available (config.md) | Gap | Mitigation |
|----------|---------|----------------------|-----|-----------|
| Compute (ours) | ... | ... | ... | ... |
| Compute (baselines) | ... | ... | ... | ... |
| Data | ... | ... | ... | ... |
| Time | ... | ... | ... | ... |

---

## 8. Risk & Mitigation

| # | Risk | Likelihood | Impact | Mitigation | Fallback |
|---|------|-----------|--------|-----------|---------|
| <from validation risk assessment> | ... | ... | ... | ... |

---

## 9. Timeline

| Phase | Duration | Deliverable | Dependencies |
|-------|---------|------------|-------------|
| ... | ... | ... | ... |

[TBD if not enough info for scheduling]

---

## 10. References

<All papers cited in this draft, with links. Pull from refs.db.>

---

## Current Assessment

| Dimension | Score | Threshold | Notes |
|-----------|-------|-----------|-------|
| Novelty | X/5 | from config.md | ... |
| Theory | X/5 | ... | ... |
| Contribution | X/5 | ... | ... |
| Feasibility | X/5 | ... | ... |
| Risk | X/5 | ... | ... |
| **Weighted Avg** | **X.X** | | |

**Gaps to close:** <dimensions below threshold and what's needed>

## Exploration History

<From status.py tree>

v0 seed [scores] -> v1 ... -> current
Dead ends: <list>
```

### 4. Commit

```bash
git add doc/proposals/draft.md && git commit -m "draft: proposal snapshot — v<N>, avg=X.X"
```

### 5. Present to User

Print a short summary:
- Current weighted average and gap to convergence
- Which proposal sections are complete vs. `[TBD]`
- Suggest next mode: "Run `/idea_refinery evaluate` to strengthen weak dimensions" or "Run `/idea_refinery converge` when ready to finalize"

## Key Differences from Converge

| | Draft | Converge |
|--|-------|----------|
| **When** | Any time during exploration | When all dims meet threshold or user is done |
| **Output** | `doc/proposals/draft.md` (overwritten) | `doc/proposals/<date>_<slug>.md` (permanent) |
| **Depth** | Same structure, `[TBD]` for gaps | Polished, all sections complete |
| **Extras** | Current assessment + gaps section | Exploration summary, BibTeX export, appendices |
| **Finality** | Iterative — update as idea evolves | One-time — marks the end of exploration |
