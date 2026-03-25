# Mode: Draft

Generate or update a readable proposal snapshot from the current idea version. Lighter than converge — meant for the user to review progress at any point during exploration.

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

Write `doc/proposals/draft.md` with this structure:

```markdown
# <Idea Title> (Draft)

> **Version:** <current version>
> **Branch:** <current branch>
> **Last updated:** <date>
> **Status:** Draft — not converged, <N> dimensions below threshold

---

## Problem & Motivation

<From idea card + findings: what gap this addresses, why it matters>

## Proposed Approach

<From idea card: the current method, key components>
<Include ASCII diagram if the idea is concrete enough>

## What Makes This Different

<From validation novelty check + refs.db:
 comparison table vs. closest existing work>

| Aspect | Closest Work | Ours | Delta |
|--------|-------------|------|-------|
| ... | ... | ... | ... |

## Current Assessment

| Dimension | Score | Notes |
|-----------|-------|-------|
| Novelty | X/5 | ... |
| Theory | X/5 | ... |
| Contribution | X/5 | ... |
| Feasibility | X/5 | ... |
| Risk | X/5 | ... |
| **Weighted Avg** | **X.X** | |

**Gaps to close:** <dimensions below threshold and what's needed>

## Key Supporting Evidence

<Top 5-8 papers from refs.db that support or inform the idea, with 1-line relevance notes>

1. [Author et al. "Title." Venue, Year.](link) — <relevance>
2. ...

## Design Choices So Far

<From decisions.md: key choices made and why>

| Choice | Alternatives Considered | Why This One |
|--------|----------------------|-------------|
| ... | ... | ... |

## Open Questions & Risks

<From findings.md + idea card weaknesses + sketch.md open questions>

- ...

## Exploration History

<Compact version — from status.py tree>

```
v0 seed [scores] → v1 <direction> [scores] → ...
Dead ends: <list>
```

## What's Next

<From sketch.md next steps: what needs to happen before convergence>
```

### 4. Commit

```bash
git add doc/proposals/draft.md && git commit -m "draft: updated proposal snapshot — v<N>, avg=X.X"
```

### 5. Present to User

Print a short summary:
- Current weighted average and gap to convergence
- Which sections are well-supported vs. still thin
- Suggest next mode: "Run `/idea_refinery evaluate` to strengthen weak dimensions" or "Run `/idea_refinery converge` if you're satisfied"

## Key Differences from Converge

| | Draft | Converge |
|--|-------|----------|
| **When** | Any time during exploration | When all dims meet threshold or user is done |
| **Output** | `doc/proposals/draft.md` (overwritten) | `doc/proposals/<date>_<slug>.md` (permanent) |
| **Depth** | Readable snapshot, gaps acknowledged | Polished, self-contained, publication-ready |
| **Extras** | None | Exploration summary, BibTeX export, appendices |
| **Finality** | Iterative — update as idea evolves | One-time — marks the end of exploration |
