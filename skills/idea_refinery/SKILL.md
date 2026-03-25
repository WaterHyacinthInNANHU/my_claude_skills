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

## Mode Dispatch

Identify the user's intent, then read the corresponding mode file from `modes/`.

| Command | Mode | File |
|---------|------|------|
| `/idea_refinery setup` | **setup** | `modes/setup.md` |
| `/idea_refinery survey [topic]` | **survey** | `modes/survey.md` |
| `/idea_refinery evaluate` | **evaluate** | `modes/evaluate.md` |
| `/idea_refinery propose` | **propose** | `modes/propose.md` |
| `/idea_refinery auto` | **auto** | `modes/auto.md` |
| `/idea_refinery draft` | **draft** | `modes/draft.md` |
| `/idea_refinery converge` | **converge** | `modes/converge.md` |
| `/idea_refinery merge <dir>` | merge direction into main | (inline, see below) |
| `/idea_refinery switch <dir>` | switch to a direction branch | (inline, see below) |
| `/idea_refinery kill` | mark current direction as dead end | (inline, see below) |
| `/idea_refinery status` | show compact tree + scores | (inline, see below) |
| `/idea_refinery next` | suggest and run the logical next mode | (inline, see below) |

Also matches natural language (e.g., "evaluate this idea" -> evaluate mode).

**If the user gives a raw idea with no existing workspace**, start with **setup** then proceed to **survey** or **auto**.

**If ambiguous**, ask: "Which mode? setup / survey / evaluate / propose / auto / draft / converge"

### Inline Commands

These don't need a mode file — execute directly:

**`/idea_refinery merge <dir>`** — Merge a direction into the main branch:
```bash
git checkout ideate/<tag> && git merge ideate/<tag>/<dir>
# Create new idea version card from the merged direction
# Update sketch.md
git add doc/agent/ && git commit -m "decide: merge <dir> into main"
```

**`/idea_refinery switch <dir>`** — Switch to a direction branch:
```bash
git checkout ideate/<tag>/<dir>
python3 scripts/status.py
# Report current state on that branch
```

**`/idea_refinery kill`** — Mark current direction as dead end:
```bash
# Commit any uncommitted work
git add doc/agent/ && git commit -m "dead-end(<dir>): <reason>"
git checkout ideate/<tag>
# Update sketch.md to mark direction as dead
```

**`/idea_refinery status`** — Show current state:
```bash
python3 scripts/status.py
```

**`/idea_refinery next`** — Suggest the logical next step based on current state:
1. Run `python3 scripts/status.py --json`
2. If no scores yet -> suggest **evaluate**
3. If scores exist but below threshold -> suggest **propose** (or **survey** if knowledge gaps)
4. If all scores meet threshold -> suggest **converge**
5. If multiple directions unscored -> suggest **auto**
6. Tell the user what and why, then proceed if they agree

## Agent Reading Order

```
1. This file (SKILL.md)     <- Shared definitions + mode dispatch
2. modes/<mode>.md           <- The selected mode's full instructions
3. CLAUDE.md (in workspace)  <- Session protocol, git workflow (at runtime)
```

## Shared Definitions

### Validation Rating Scale

5-point scale used throughout all validation and scoring:

| Rating | Meaning | Guidance |
|--------|---------|----------|
| 1/5 | Critical weakness | Likely fatal -- must pivot or abandon |
| 2/5 | Significant concern | Needs major rework to proceed |
| 3/5 | Adequate | Workable but room for improvement |
| 4/5 | Strong | Minor issues only, ready to proceed |
| 5/5 | Excellent | No concerns in this dimension |

### Validation Dimensions

| Dimension | What It Measures |
|-----------|-----------------|
| Novelty | Does this exist already? What's the delta? |
| Theory | Sound from first principles? Assumptions valid? |
| Contribution | Significant enough for the target venue/goal? |
| Feasibility | Within resource budget (from config.md)? |
| Risk | Technical, resource, novelty, evaluation, scope risks |

### Convergence Target

All dimensions >= convergence_threshold (default 4/5, configurable in config.md).

### Git Branch Strategy

Branches form a tree. The user switches branches; modes operate on the current branch.

```
ideate/<tag>                      <- main branch (best version)
+-- ideate/<tag>/A                <- direction A
|   +-- ideate/<tag>/A.1          <- sub-refinement
|   +-- ideate/<tag>/A.2
+-- ideate/<tag>/B
+-- ideate/<tag>/C
```

### Navigating the Idea Tree

The user controls which node the agent works on via commands or natural language:

| User Says | Command Equivalent |
|-----------|-------------------|
| "this direction looks good, merge it" | `/idea_refinery merge <dir>` |
| "explore direction A" / "switch to A" | `/idea_refinery switch A` |
| "this is a dead end" / "kill this" | `/idea_refinery kill` |
| "go deeper on this" / "sub-refine" | `git checkout -b ideate/<tag>/<dir>.<N>`, then propose or evaluate |
| "what should we do next?" | `/idea_refinery next` |
| "write it up" / "let me see it" | `/idea_refinery draft` |
| "finalize" / "we're done" | `/idea_refinery converge` |

**Key principle:** The user drives tree navigation; modes operate on the current branch. If the user's intent implies a branch switch, do it and confirm before proceeding.

### Git Commit Conventions

Format: `<type>(<scope>): <what and why>`

| Type | When |
|------|------|
| `seed` | Initial idea capture |
| `survey` | Papers found/read |
| `validate` | Validation complete |
| `direction` | New direction proposed |
| `decide` | User chose a direction |
| `refine` | Idea updated |
| `dead-end` | Direction abandoned |
| `draft` | Proposal snapshot |
| `converge` | Final proposal |
| `refs` | Reference DB updated |
| `checkpoint` | Safety save |
| `auto` | Auto mode iteration |

### Workspace Structure

```
<workspace>/
+-- refs.db                       <- Paper reference database (SQLite + FTS5)
+-- config.md                     <- Global constraints & search params
+-- scripts/
|   +-- refs.py                   <- Reference DB CLI
|   +-- status.py                 <- Compact status generator
+-- doc/
|   +-- agent/
|   |   +-- sketch.md             <- Current state & next steps
|   |   +-- findings.md           <- Accumulated insights
|   |   +-- decisions.md          <- Direction decisions
|   |   +-- idea_versions/        <- One idea card per version
|   |   +-- directions/           <- Direction evaluation reports
|   |   +-- validations/          <- Detailed validation reports
|   +-- proposals/                <- User-facing output documents
|   |   +-- evaluation.md        <- Accumulated evaluation history
|   |   +-- draft.md             <- Current proposal snapshot
+-- CLAUDE.md                     <- Session protocol
+-- .claude/hooks/                <- SessionStart context restoration
```

### Quick Status

```bash
python3 scripts/status.py           # full status with tree + scores
python3 scripts/status.py --tree-only  # just the idea tree
python3 scripts/status.py --json    # machine-readable (for auto mode)
```

### Paper Operations

All papers stored in `refs.db`. Use `scripts/refs.py` for all operations:

```bash
python3 scripts/refs.py add --title "..." --direction seed --relevance high --notes "..."
python3 scripts/refs.py search "query"
python3 scripts/refs.py get <paper_id>
python3 scripts/refs.py update <paper_id> --read --append-notes "..."
python3 scripts/refs.py link <version> <paper_id> <role>
python3 scripts/refs.py list --direction A.1 --relevance high
python3 scripts/refs.py stats
python3 scripts/refs.py export-bib > refs.bib
```

Paper discovery and reading methods are detailed in `modes/survey.md`.
