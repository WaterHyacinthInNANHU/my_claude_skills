# Mode: Evaluate

Validate the current idea version against all dimensions. Reads config.md for weights and hard constraints.

## Trigger

User says: "evaluate this idea", "validate the current idea", "how strong is this?".

## Composability

- **Standalone**: user requests explicit validation
- **May call**: survey (when knowledge gaps block a confident rating)
- **Called by**: auto (as the scoring step in graph search)

## Procedure

### 1. Load Context

```bash
python3 scripts/status.py          # full status including current version + scores
cat config.md                      # constraints, weights, hard limits
```

Read the current idea card from `doc/agent/idea_versions/`.

### 2. Run Validation Checklist

Evaluate each dimension. If the knowledge base is insufficient for a confident rating, call **survey mode** to fill gaps before continuing.

#### 2a. Novelty Check

- Does this exact idea already exist? (search refs.db + targeted search)
- If similar work exists, what's the delta?

| Level | Description | Action |
|-------|-------------|--------|
| **Novel** | No prior work does this | Proceed |
| **Incremental** | Similar exists, meaningful delta | Sharpen the delta |
| **Exists** | Already done | Pivot or abandon |

For each similar paper:

```markdown
| Similar Paper | What They Do | Our Delta | Gap Size |
|--------------|-------------|-----------|----------|
| [Paper](link) | ... | ... | ... |
```

#### 2b. Theoretical Sanity

- Does the idea make sense from first principles?
- Are the assumptions valid?
- Known theoretical results that support or contradict it?
- Could this fail for fundamental reasons?

Rate: **Sound** / **Plausible but unproven** / **Questionable** / **Flawed**

#### 2c. Contribution Assessment

| Type | Description |
|------|-------------|
| **New method** | Novel algorithm or architecture |
| **New insight** | Surprising finding or analysis |
| **New benchmark** | Evaluation framework or dataset |
| **Engineering** | Making something practical/scalable |
| **Combination** | Novel integration of existing ideas |

Is the contribution significant enough for the target venue/goal (from config.md)?

#### 2d. Feasibility & Resource Analysis

Read training details from closest related papers. For core papers, clone and inspect repos.

Build a resource comparison:

```markdown
| Aspect | Related Work | Our Estimate | User Has (config.md) | Feasible? |
|--------|-------------|-------------|---------------------|-----------|
| GPUs | 8x A100, 48h | ~4x A100, 24h | from config.md | Tight |
| Data | ImageNet+50K | ImageNet only | from config.md | Yes |
| Time | 3 days | ~2 days | from config.md | Yes |
```

**Check against config.md hard constraints.** If a hard constraint is violated, flag immediately.

Flag: **Feasible** / **Feasible with cuts** / **Infeasible without more resources**

#### 2e. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| **Technical** -- core method may not work | H/M/L | fallback plan |
| **Resource** -- may exceed budget | H/M/L | what to cut |
| **Novelty** -- someone publishes first | H/M/L | speed plan |
| **Evaluation** -- hard to demonstrate gains | H/M/L | alternative metrics |
| **Scope** -- too ambitious for timeline | H/M/L | minimum viable version |

### 3. Score & Summarize

Use the 5-point rating scale (from SKILL.md shared definitions).

```markdown
| Dimension | Rating | Weight | Notes |
|-----------|--------|--------|-------|
| Novelty | X/5 | from config.md | ... |
| Theory | X/5 | from config.md | ... |
| Contribution | X/5 | from config.md | ... |
| Feasibility | X/5 | from config.md | ... |
| Risk | X/5 | from config.md | ... |
| **Weighted Avg** | **X.X** | | |
| **Overall** | **Promising / Needs work / Weak / Abandon** |
```

If any dimension's rating is below the convergence threshold (from config.md, default 4.0), note it as requiring improvement.

### 4. Save & Commit

Save **two outputs**:

**Agent working file** — `doc/agent/validations/val_<version>.md` (detailed internal record)

**User-facing evaluation** — `doc/proposals/evaluation.md` (accumulated, readable)

Update `doc/proposals/evaluation.md` — this file is **append-based**: each evaluation adds a section, building a history the user can read. Structure:

```markdown
# Evaluation Report: <tag>

> Last updated: <date>
> Convergence threshold: <from config.md>

## Summary

| Version | Branch | Scores | Avg | Verdict | Date |
|---------|--------|--------|-----|---------|------|
| v0 | ideate/<tag> | N:3 T:4 C:3 F:5 R:2 | 3.4 | Needs work | 2026-03-24 |
| A | ideate/<tag>/A | N:4 T:4 C:4 F:3 R:3 | 3.6 | Promising | 2026-03-24 |
| A.1 | ideate/<tag>/A.1 | N:4 T:4 C:4 F:4 R:3 | 3.8 | Promising | 2026-03-25 |

## <version>: <1-line idea summary> (<date>)

### Scores
| Dimension | Rating | Weight | Notes |
|-----------|--------|--------|-------|
| Novelty | X/5 | ... | ... |
| ... | ... | ... | ... |
| **Weighted Avg** | **X.X** | | |

### Novelty Assessment
<novelty level> — <comparison table vs. similar work>

### Theoretical Sanity
<rating> — <key reasoning>

### Contribution
<type> — <significance assessment>

### Feasibility
<flag> — <resource comparison table>

### Risks
<risk table with mitigations>

### Verdict
**<Promising / Needs work / Weak / Abandon>**
- Strengths: ...
- Gaps to close: <dimensions below threshold>
- Suggested next: <propose / survey / specific action>

---
(next evaluation appended below)
```

**On first evaluation:** create the file with header + summary table + first entry.
**On subsequent evaluations:** update the summary table (add/update row) and append a new section.

```bash
# Update idea card with scores
# Update doc/proposals/evaluation.md
# Link key papers
python3 scripts/refs.py link <version> <paper_id> <role> --note "..."
git add doc/agent/ doc/proposals/evaluation.md refs.db && git commit -m "validate(<version>): <overall> -- <key_issues>"
git notes add -m "Scores: N:X T:X C:X F:X R:X avg=X.X" HEAD
```

### 5. Present to User

**ASK USER:**
- Show the validation summary
- Highlight dimensions below convergence threshold
- "The full evaluation history is in `doc/proposals/evaluation.md`"
- "Want to proceed, pivot, or add constraints?"
- Suggest: `/idea_refinery propose` to generate improvement directions
