# Mode: Converge

Generate the final proposal document from the best idea version.

## Trigger

User says: "write the final proposal", "converge", "good enough, let's write it up".

## Composability

- **Standalone**: called when user is satisfied with the idea

## Procedure

### 1. Load Context

```bash
python3 scripts/status.py          # full tree with scores
python3 scripts/refs.py stats      # reference DB overview
```

Verify the current branch has the best idea version merged.

### 2. Summarize Exploration

Write `doc/agent/exploration_summary.md`:

```markdown
# Exploration Summary: <Idea>

## Journey

v0 (seed) -> v1 (<direction>) -> ... -> vN (final)

### Iteration 1: Seed -> Directions
- **Seed idea:** <1 sentence>
- **Seed validation:** <overall rating, key weaknesses>
- **Directions explored:**

| Direction | Verdict | Key Finding | Kept? |
|-----------|---------|-------------|-------|
| A: <name> | Promising | <what we learned> | Yes -> became v1 |
| B: <name> | Dead end | <why it failed> | No |

### Convergence
- **Reason:** <all dimensions strong / no further improvement / user satisfied>
- **Total iterations:** N
- **Total papers reviewed:** M (from `refs.py stats`)
- **Dead ends encountered:** K

## Key Insights Discovered

1. <insight that shaped the final idea>
2. <surprising finding from literature>

## Ideas Not Pursued (Future Work)

| Direction | Why Dropped | Potential If Revisited |
|-----------|------------|----------------------|
| ... | ... | ... |
```

### 3. Write Final Proposal

Use the template at `templates/proposal.md.template`. Compile the best idea version into a polished document readable by someone who hasn't seen the exploration.

**Key rules:**
- Every paper reference must have a clickable link (arXiv or Semantic Scholar)
- Organize related work by sub-topic, not chronologically
- Design choices table must include alternatives considered and evidence
- Experiment plan must have success criteria and failure plans
- Include idea evolution and dead ends as appendices

Pull references from refs.db:
```bash
python3 scripts/refs.py list --relevance high
python3 scripts/refs.py links <final_version>
```

Save to `doc/proposals/<YYYY-MM-DD>_<idea_slug>.md`.

### 4. Export & Commit

```bash
# Export references
python3 scripts/refs.py export-bib > doc/proposals/references.bib
python3 scripts/refs.py export-md > doc/proposals/references.md

# Final commit
git add -A && git commit -m "converge: <final idea title> -- N iterations, M papers reviewed"
git notes add -m "Final scores: N:X T:X C:X F:X R:X avg=X.X" HEAD

# Update sketch.md phase -> done
```

### 5. Offer Next Steps

**ASK USER:**
- "Want me to start implementing? I can set up an experiment workspace."
- "Want me to create skills for key papers? (`/create_skill_with_paper`)"
- "Want me to refine any section of the proposal further?"
- "Want me to find additional baselines or related work?"
