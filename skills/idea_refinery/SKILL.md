---
name: idea_refinery
description: Iteratively refine a research idea through literature survey, validation, and branching exploration until convergence.
---

# idea_refinery

Iteratively refine a coarse research idea into a validated, concrete proposal through cycles of literature survey, critical validation, and branching exploration.

## When to Use

- User has a rough research idea and wants to develop it
- User wants to validate novelty/feasibility before committing
- User wants to explore multiple directions from a seed idea

## Inputs

| Input | Required | Example |
|-------|----------|---------|
| **Idea** | Yes | "Use 3D point clouds to improve VLA robustness" |
| **Domain** | Optional | robotics, 3D vision, RL, etc. |
| **Resources** | Optional | GPUs, time budget, data access, team size |
| **Constraints** | Optional | "Must work with existing VLA checkpoint", "Conference deadline in 3 months" |

## Agent Reading Order

```
1. This file (SKILL.md)            — Full workflow, Phases 0-3
2. CLAUDE.md.template               — Installed to workspace; session protocol, git workflow
3. Templates (sketch.md, etc.)      — Used during setup, not read at runtime
```

## Validation Rating Scale

Used throughout all validation steps. 5-point scale:

| Rating | Meaning | Guidance |
|--------|---------|----------|
| ⬤○○○○ (1/5) | Critical weakness | Likely fatal — must pivot or abandon |
| ⬤⬤○○○ (2/5) | Significant concern | Needs major rework to proceed |
| ⬤⬤⬤○○ (3/5) | Adequate | Workable but room for improvement |
| ⬤⬤⬤⬤○ (4/5) | Strong | Minor issues only, ready to proceed |
| ⬤⬤⬤⬤⬤ (5/5) | Excellent | No concerns in this dimension |

**Convergence target:** all dimensions ≥ 4/5.

## Workflow Overview

```
Phase 0: WORKSPACE SETUP
  Create git-managed workspace with context files and hooks

Phase 1: SEED
  Step 1: Capture idea + constraints
  Step 2: Initial topic survey (reuse /topic_survey)
  Step 3: Validate seed idea
  Step 4: Propose N refinement directions
                    │
Phase 2: BRANCH & REFINE (parallel across directions)
  ┌─────────────────┼─────────────────┐
  Dir A             Dir B             Dir C
  │                 │                 │
  ├─ Targeted search├─ Targeted search├─ Targeted search
  ├─ Validate       ├─ Validate       ├─ Validate
  ├─ Score          ├─ Score          ├─ Score
  └─────────────────┴─────────────────┘
                    │
  Rank → ASK USER to pick / merge / combine
                    │
  Iterate on top picks until convergence
                    │
Phase 3: CONVERGE
  Exploration summary + Final proposal document
```

---

## Phase 0: WORKSPACE SETUP

### Create Workspace

```bash
# Automated setup
bash <skill_path>/templates/scripts/setup.sh \
  --workspace <path> \
  --tag <idea_slug> \
  --idea "<seed idea text>"
```

### Workspace Structure

```
<workspace>/
├── doc/
│   ├── agent/                    ← Agent working memory
│   │   ├── sketch.md             ← Current state & next steps (updated frequently)
│   │   ├── survey_cache.md       ← All papers found, shared across directions
│   │   ├── findings.md           ← Accumulated insights & dead ends
│   │   ├── decisions.md          ← Direction and pivot decisions
│   │   ├── idea_versions/        ← One idea card per version
│   │   │   └── v0_seed.md
│   │   ├── directions/           ← One report per direction evaluated
│   │   └── validations/          ← Detailed validation reports
│   └── proposals/                ← Final output documents
├── CLAUDE.md                     ← Agent session protocol (from template)
└── .claude/hooks/                ← SessionStart context restoration
```

### Git Branch Strategy

```
ideate/<tag>                      ← main branch (best idea version)
├── ideate/<tag>-dir-<name>       ← direction exploration branches
└── ideate/<tag>-v<N>             ← version refinement branches
```

| Action | Git Command |
|--------|------------|
| Explore a direction | `git checkout -b ideate/<tag>-dir-<name>` |
| Direction is promising | `git checkout ideate/<tag> && git merge ideate/<tag>-dir-<name>` |
| Direction is dead end | `git checkout ideate/<tag>` (leave branch as record) |
| New idea version | `git checkout -b ideate/<tag>-v<N>`, refine, merge back |
| Checkpoint before pivot | `git commit -m "checkpoint: before <decision>"` |

### Session Recovery

The SessionStart hook auto-restores context: sketch.md, branches, latest idea card, survey cache size. If a session is interrupted, the next session picks up exactly where it left off.

---

## Phase 1: SEED

### Step 1: Capture Idea & Constraints

**ASK USER** to provide:

1. **The idea** — even a single sentence is fine
2. **Goal** — paper publication? class project? prototype? internal tool?
3. **Resources** (critical for feasibility):

| Resource | Ask About |
|----------|-----------|
| Compute | # GPUs, type (A100/H100/etc.), hours available |
| Time | Deadline or time budget |
| Data | What datasets are accessible |
| Team | Solo or collaborators, expertise areas |
| Codebase | Starting from scratch or building on existing code |

4. **Constraints** — any hard requirements or non-negotiables

Record in `doc/agent/idea_versions/v0_seed.md` (idea card template) and update `sketch.md`.

```bash
git add doc/agent/ && git commit -m "v0: seed idea captured"
```

### Step 2: Initial Topic Survey

Run `/topic_survey` logic on the idea's domain. This builds the shared knowledge base that all subsequent steps reuse.

**Scope the survey around the idea:**
- Core topic keywords from the idea
- Adjacent areas that might intersect
- Recent work (last 2-3 years)

#### Paper Discovery & Reading

Use the methods from `/paper_related_works` and `/topic_survey` for all paper operations.

**Discover papers:**

| Method | When to Use | How |
|--------|------------|-----|
| Semantic Scholar API | Keyword search, citation graph | `curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=<KEYWORDS>&limit=20&fields=title,year,authors,citationCount,externalIds,abstract&sort=citationCount:desc"` |
| Semantic Scholar (recent) | Find cutting-edge work | Same but add `&year=2024-2026` |
| Semantic Scholar (citations) | Find successors of a paper | `.../paper/ArXiv:{ID}?fields=citations.title,citations.year,citations.authors,citations.externalIds,citations.citationCount` |
| Web search | Broad sweep, surveys | `WebSearch: "<topic>" site:arxiv.org` |
| Papers With Code | Find benchmarks, code | `WebSearch: "<topic>" site:paperswithcode.com` |
| Citation chain | Trace research lineage | From papers already in cache, follow references + citing papers (see `/paper_related_works` Steps 3-4) |

**Read papers** via AlphaXiv (always try first for any arXiv paper):

```
WebFetch: https://alphaxiv.org/overview/{PAPER_ID}.md    # structured overview (fast)
WebFetch: https://alphaxiv.org/abs/{PAPER_ID}.md         # full text (if overview lacks detail)
```

If AlphaXiv returns 404, fall back to reading the PDF directly.

**For key papers** (foundations the idea builds on, main competitors): use `/paper_related_works` logic to map their predecessors and successors — this surfaces papers that keyword search misses.

**Write results to `doc/agent/survey_cache.md`:**

```markdown
| # | Paper | Year | Citations | Sub-topic | Relevance | Direction | Read? |
|---|-------|------|-----------|-----------|-----------|-----------|-------|
| 1 | [Title](https://arxiv.org/abs/...) | 2025 | 42 | <topic> | high | seed | [x] |
```

- `Direction` column: `seed` = initial survey, `dir-A` = found during direction A, etc.
- Never remove entries — mark relevance down instead.

```bash
git add doc/agent/survey_cache.md && git commit -m "survey: initial topic survey complete"
```

### Step 3: Validate Seed Idea

Run the **validation checklist** against the seed idea. This framework is reused in every refinement cycle.

#### 3a. Novelty Check

- Does this exact idea already exist? (search survey cache + targeted search)
- If similar work exists, what's the delta?

| Level | Description | Action |
|-------|-------------|--------|
| **Novel** | No prior work does this | Proceed |
| **Incremental** | Similar exists, but meaningful delta | Sharpen the delta |
| **Exists** | Already done, similar results expected | Pivot or abandon |

For each similar paper found:

```markdown
| Similar Paper | What They Do | What's Different in Our Idea | Gap |
|--------------|-------------|----------------------------|-----|
| [Paper](https://arxiv.org/abs/...) | ... | ... | ... |
```

#### 3b. Theoretical Sanity

- Does the idea make sense from first principles?
- Are the assumptions valid?
- Are there known theoretical results that support or contradict it?
- Could this fail for fundamental reasons? (e.g., information-theoretic limits, computational complexity)

Rate: **Sound** / **Plausible but unproven** / **Questionable** / **Flawed**

#### 3c. Contribution Assessment

- What would this contribute to the field?
- Is the contribution significant enough for the target venue/goal?

| Type | Description | Example |
|------|-------------|---------|
| **New method** | Novel algorithm or architecture | "A new loss function for X" |
| **New insight** | Surprising finding or analysis | "X actually hurts because..." |
| **New benchmark** | Evaluation framework or dataset | "First benchmark for X" |
| **Engineering** | Making something practical/scalable | "Real-time version of X" |
| **Combination** | Novel integration of existing ideas | "X + Y for Z" |

#### 3d. Feasibility & Resource Analysis

**Estimate required resources by examining related papers and code.**

Read training details from closest related papers via AlphaXiv. For core papers, **clone and inspect code repos:**

```bash
git clone <repo_url> /tmp/idea_refinery_<method>
cd /tmp/idea_refinery_<method>

# Resource requirements
grep -r "batch_size\|num_gpu\|n_gpu\|world_size" configs/ scripts/ --include="*.py" --include="*.yaml"
cat README.md | grep -iA5 "training\|hardware\|gpu\|resource"

# Model size
grep -r "num_params\|n_parameters\|model_size" --include="*.py" | head -10

# Data pipeline
ls data/ datasets/ 2>/dev/null
grep -r "dataset\|dataloader" --include="*.py" -l | head -5

rm -rf /tmp/idea_refinery_<method>
```

**When to clone repos:**
- Estimating compute/time for feasibility
- Understanding implementation details not in the paper
- Checking if code can be adapted for our idea
- Verifying reproducibility (check GitHub issues too)

Build a resource comparison:

```markdown
| Aspect | Related Work (Paper X) | Our Idea (Estimate) | User Has | Feasible? |
|--------|----------------------|--------------------|---------| ---------|
| GPUs | 8x A100, 48h | ~4x A100, 24h | 2x A100 | Tight |
| Data | ImageNet + custom 50K | ImageNet only | ImageNet | Yes |
| Training time | 3 days | ~2 days | 1 week budget | Yes |
| Engineering effort | 2 months, team of 3 | ~1 month solo | Solo, 3 months | Yes |
```

Flag: **Feasible** / **Feasible with cuts** / **Infeasible without more resources**

If infeasible, identify what to scale down.

#### 3e. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| **Technical** — core method may not work | H/M/L | <fallback plan> |
| **Resource** — may exceed budget | H/M/L | <what to cut> |
| **Novelty** — someone publishes first | H/M/L | <speed plan, differentiation> |
| **Evaluation** — hard to demonstrate gains | H/M/L | <alternative metrics/tasks> |
| **Scope** — too ambitious for timeline | H/M/L | <minimum viable version> |

#### 3f. Validation Summary

```markdown
| Dimension | Rating | Notes |
|-----------|--------|-------|
| Novelty | ⬤⬤⬤○○ | Similar to X but differs in Y |
| Theory | ⬤⬤⬤⬤○ | Sound, supported by Z |
| Contribution | ⬤⬤⬤○○ | Incremental but useful |
| Feasibility | ⬤⬤⬤⬤⬤ | Within resource budget |
| Risk | ⬤⬤○○○ | High technical risk |
| **Overall** | **Promising / Needs work / Weak / Abandon** |
```

**Present to user. ASK USER** if they want to proceed, pivot, or add constraints.

```bash
# Save to doc/agent/validations/val_v0.md
# Update idea card with validation scores
git add doc/agent/ && git commit -m "validate: seed idea v0 assessed"
git notes add -m "v0 validation: <overall rating>, key issues: <list>" HEAD
```

### Step 4: Propose Refinement Directions

Based on the survey and validation, propose **3-5 improvement directions**.

Each direction should address a weakness found in validation OR amplify a strength:

```markdown
### Direction A: <name>
**Addresses:** <which validation weakness>
**Core change:** <what's different from seed idea>
**Expected impact:** <which dimensions improve>
**New risk:** <what new risk this introduces>
**Effort delta:** <more/less/same vs. seed>
```

Direction types to consider:

| Type | When to Propose |
|------|----------------|
| **Sharpen novelty** | Similar work exists; find a unique angle |
| **Simplify** | Idea is overscoped; find minimum viable version |
| **Strengthen theory** | Weak theoretical grounding; add formal justification |
| **Change scope** | Contribution too small; expand to stronger result |
| **Alternative method** | Core approach is risky; propose safer path to same goal |
| **Merge ideas** | Two sub-ideas from survey could combine well |

**ASK USER:** "Here are N directions. Which ones should I explore? You can pick multiple — I'll evaluate them in parallel."

---

## Phase 2: BRANCH & REFINE

### Parallel Evaluation of Directions

**Launch parallel agents** — one per selected direction:

```
Agent per direction:
1. Targeted search (reuse survey cache + new searches)
2. Validate (same checklist as Phase 1 Step 3, focused on delta)
3. Score all dimensions
4. Write direction report
```

#### Agent Instructions (per direction)

Each agent receives: seed idea card, survey cache, seed validation summary, user resource constraints.

**2'. Targeted Search (agent-driven depth):**
- Start from the survey cache (don't re-search papers already found)
- Search for work specific to this direction using all discovery methods (see Phase 1 Step 2):
  - Semantic Scholar API (keyword search + citation graph)
  - Web search (arxiv.org, paperswithcode.com)
  - Citation chains from cached papers
  - For key papers, run `/paper_related_works` logic to find predecessors/successors
- Read all discovered papers via AlphaXiv first (`https://alphaxiv.org/overview/{ID}.md`)
- **The agent decides how deep to search:**

| Situation | Search Depth |
|-----------|-------------|
| Direction well-covered by cache | Minimal — 1-2 new papers, reuse cached |
| Introduces new technique/domain | Moderate — 3-5 new papers |
| Pivots to unfamiliar subfield | Deep — run a mini `/topic_survey` on the new subfield |
| Finds paper citing unknown work | Follow the chain — read references and successors |
| Suspects direction already done | Aggressive novelty search — look for exact prior work |
| Feasibility unclear | Clone repos to check training configs and resource needs |

**Proactively expand search** when validation reveals knowledge gaps or novelty is inconclusive. **Stop searching** when enough evidence exists for a confident judgment or the direction is clearly a dead end.

**3'. Validate Direction:**
- Run the full validation checklist (3a-3f) on the refined idea
- Compare against the seed idea's validation: what improved, what got worse?
- Estimate resource delta from seed
- If validation reveals unknowns, **go back to 2' and search more** before finalizing

**Output per direction:**

```markdown
## Direction <X>: <name>

### Refined Idea
<1-2 paragraph description of the refined idea>

### Key Papers Found
| Paper | Year | Relevance | Code |
|-------|------|-----------|------|
| [Title](https://arxiv.org/abs/...) | 2025 | <why it matters> | [repo](url) |

### Validation Delta
| Dimension | Seed v0 | This Direction | Delta |
|-----------|---------|---------------|-------|
| Novelty | ⬤⬤⬤○○ | ⬤⬤⬤⬤○ | +1 |
| Theory | ⬤⬤⬤⬤○ | ⬤⬤⬤⬤○ | = |
| Contribution | ⬤⬤⬤○○ | ⬤⬤⬤⬤○ | +1 |
| Feasibility | ⬤⬤⬤⬤⬤ | ⬤⬤⬤○○ | -2 |
| Risk | ⬤⬤○○○ | ⬤⬤⬤○○ | +1 |

### Verdict
<Promising / Marginal / Dead end>
<1-2 sentences on why>
```

### Rank & Select

As each parallel agent returns, save its report and merge new papers into the survey cache:

```bash
git checkout ideate/<tag>-dir-<name>
# Write to doc/agent/directions/dir_<name>.md
# Append new papers to doc/agent/survey_cache.md
git add doc/agent/ && git commit -m "dir-<name>: <verdict>"
git notes add -m "Direction <name>: <verdict>, key finding: <summary>" HEAD
```

After all agents return, compile a ranking:

```markdown
## Direction Ranking (Iteration N)

| Rank | Direction | Overall | Novelty | Feasibility | Key Tradeoff |
|------|-----------|---------|---------|-------------|-------------|
| 1 | Dir A | ⬤⬤⬤⬤○ | High | High | ... |
| 2 | Dir C | ⬤⬤⬤○○ | High | Medium | ... |
| 3 | Dir B | ⬤⬤○○○ | Medium | High | ... |
```

**ASK USER:**
- "Direction A looks strongest because X. Direction C is interesting but Y. Which should I refine further?"
- "Should I merge aspects of A and C?"
- "Any new constraints or thoughts after seeing these?"

#### Merging Two Directions

If user wants to combine aspects of multiple directions:

1. Create a new direction branch from main: `git checkout -b ideate/<tag>-dir-<merged_name>`
2. Write a merged idea description combining the selected aspects
3. Run validation on the merged idea (may need new targeted search for the combination)
4. The merged direction is treated as a new version candidate

#### Record Decision

```bash
# Append to doc/agent/decisions.md
# Merge winning direction branch back to main
git checkout ideate/<tag> && git merge ideate/<tag>-dir-<name>
# Create new idea version card: doc/agent/idea_versions/v<N>_<slug>.md
git add doc/agent/ && git commit -m "v<N>: <what changed from v<N-1>>"
```

### Iterate

For each selected direction, repeat Phase 2:
- Propose 2-3 sub-refinements within the direction
- Run parallel validation
- Rank and present

**Convergence criteria (stop iterating when):**

| Condition | Action |
|-----------|--------|
| All dimensions ≥ ⬤⬤⬤⬤○ | **Converge** — idea is strong |
| No direction improves over parent | **Converge** — best version found |
| User says "good enough" | **Converge** |
| All directions hit dead ends | **Converge** — report what was learned |
| 3+ iterations with no improvement | **Converge** — diminishing returns |
| Fundamental blocker found | **Stop** — explain why, suggest pivots |

Typical convergence: **2-3 iterations** (seed → directions → sub-refinements → final).

---

## Phase 3: CONVERGE

### Step 1: Summarize Exploration

Write `doc/agent/exploration_summary.md`:

```markdown
# Exploration Summary: <Idea>

## Journey

v0 (seed) → v1 (<direction>) → v2 (<refinement>) → ... → vN (final)

### Iteration 1: Seed → Directions
- **Seed idea:** <1 sentence>
- **Seed validation:** <overall rating, key weaknesses>
- **Directions explored:**

| Direction | Verdict | Key Finding | Kept? |
|-----------|---------|-------------|-------|
| A: <name> | Promising | <what we learned> | Yes → became v1 |
| B: <name> | Dead end | <why it failed> | No |

### Iteration 2: v1 → Sub-refinements
...

### Convergence
- **Reason:** <all dimensions strong / no further improvement / user satisfied>
- **Total iterations:** N
- **Total papers reviewed:** M
- **Dead ends encountered:** K

## Key Insights Discovered

1. <insight that shaped the final idea>
2. <surprising finding from literature>

## Ideas Not Pursued (Future Work)

| Direction | Why Dropped | Potential If Revisited |
|-----------|------------|----------------------|
| ... | ... | ... |
```

### Step 2: Write Final Proposal

Use the template at `templates/proposal.md.template`. Compile the best idea version into a polished, self-contained document — **readable by someone who hasn't seen the exploration**.

**Key rules for the proposal:**
- Every paper reference must have a clickable link (arXiv or Semantic Scholar)
- Organize related work by sub-topic, not chronologically
- Design choices table must include alternatives considered and evidence
- Experiment plan must have success criteria and failure plans
- Include idea evolution and dead ends as appendices

Save to `doc/proposals/<YYYY-MM-DD>_<idea_slug>.md`.

### Step 3: Save & Commit

```bash
# Final commit
git add -A && git commit -m "ideate/<tag>: final proposal — <1-line summary>"
git notes add -m "Final: <idea title>, <N> iterations, <M> papers, <overall score>" HEAD

# Update sketch.md phase → done
```

### Step 4: Offer Next Steps

**ASK USER:**
- "Want me to start implementing? I can set up an experiment workspace with `/auto_experiment`."
- "Want me to create skills for key papers? (`/create_skill_with_paper`)"
- "Want me to refine any section of the proposal further?"
- "Want me to find additional baselines or related work for a specific section?"

---

## Quick Reference

| Action | How |
|--------|-----|
| Start refinement | User gives idea → Phase 0 + Phase 1 |
| Check current state | `cat doc/agent/sketch.md` |
| Check latest idea version | `ls -t doc/agent/idea_versions/ \| head -1` |
| See all branches explored | `git branch -a \| grep ideate/` |
| Count papers in cache | `grep -c "^\| [0-9]" doc/agent/survey_cache.md` |
| Add constraint mid-process | User injects at any ASK USER checkpoint |
| Skip to proposal | User says "good enough" at any checkpoint → Phase 3 |
| Restart from different seed | New idea → back to Phase 1 Step 1 |
| Reuse survey for new idea | Keep survey cache, re-run from Step 3 with new idea |
