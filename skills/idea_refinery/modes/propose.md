# Mode: Propose

Generate refinement directions based on current validation results. Each direction addresses a weakness or amplifies a strength.

## Trigger

User says: "propose new directions", "how can I improve this?", "what directions should I explore?".

## Composability

- **Standalone**: user requests directions after manual evaluation
- **May call**: survey (when a proposed direction enters unfamiliar territory)
- **Called by**: auto (as the expansion step in graph search)

## Procedure

### 1. Load Context

```bash
python3 scripts/status.py          # current tree, scores, convergence status
cat config.md                      # hard constraints, soft preferences
```

Read the current idea card and its validation report.

### 2. Identify Improvement Targets

From the validation scores, identify:
- **Must fix**: dimensions below convergence threshold (from config.md)
- **Should improve**: dimensions with lowest weighted score
- **Hard constraint violations**: auto-reject any direction that violates these

### 3. Generate 3-5 Directions

Each direction should address a weakness or amplify a strength:

```markdown
### Direction <X>: <name>
**Addresses:** <which validation weakness>
**Core change:** <what's different from current version>
**Expected impact:** <which dimensions improve, which might regress>
**New risk:** <what new risk this introduces>
**Effort delta:** <more/less/same vs. current>
**Hard constraint check:** <passes all / violates X -- REJECTED>
```

Direction types to consider:

| Type | When to Propose |
|------|----------------|
| **Sharpen novelty** | Similar work exists; find a unique angle |
| **Simplify** | Overscoped; find minimum viable version |
| **Strengthen theory** | Weak theoretical grounding |
| **Change scope** | Contribution too small |
| **Alternative method** | Core approach is risky |
| **Merge ideas** | Two sub-ideas could combine well |

**Auto-reject** any direction that violates a hard constraint from config.md. Note the rejection and reason.

### 4. If Needed: Quick Survey

If a proposed direction enters unfamiliar territory, call **survey mode** (targeted) to check:
- Has this direction been tried before?
- What papers support or contradict it?

### 5. Present to User

**ASK USER:**
- "Here are N directions. Which should I explore?"
- "You can pick multiple -- I'll evaluate them in parallel."
- "Should I merge aspects of any directions?"
- "Any new constraints after seeing these?"

### 6. Branch & Commit

For each selected direction:

```bash
# Create branch
git checkout -b ideate/<tag>/<dir_id>

# Write direction description
# Save to doc/agent/directions/dir_<name>.md

git add doc/agent/ && git commit -m "direction(<dir_id>): <1-line description>"
```

### 7. Evaluate Selected Directions

Launch parallel evaluation of selected directions:

```
Per direction (parallel agents):
1. Targeted survey (reuse refs.db + new searches)
2. Validate (full checklist, focused on delta from parent)
3. Score all dimensions
4. Write direction report with validation delta table
```

Each agent receives: parent idea card, refs.db, parent validation, config.md.

#### Direction Report Format

```markdown
## Direction <X>: <name>

### Refined Idea
<1-2 paragraph description>

### Key Papers Found
| Paper | Year | Relevance | Code |
|-------|------|-----------|------|
| [Title](link) | 2025 | <why> | [repo](url) |

### Validation Delta
| Dimension | Parent | This Direction | Delta |
|-----------|--------|---------------|-------|
| Novelty | X/5 | Y/5 | +/-Z |
...

### Verdict
<Promising / Marginal / Dead end>
```

### 8. Rank & Select

After all directions evaluated:

```markdown
| Rank | Direction | Weighted Avg | Key Tradeoff |
|------|-----------|-------------|-------------|
| 1 | Dir A | 4.2 | ... |
| 2 | Dir C | 3.8 | ... |
```

**ASK USER** which to pursue. Merge winning direction:

```bash
git checkout ideate/<tag> && git merge ideate/<tag>/<dir_id>
# Create new idea version card
git add doc/agent/ && git commit -m "decide: pursue <dir_id> (<reason>)"
```
