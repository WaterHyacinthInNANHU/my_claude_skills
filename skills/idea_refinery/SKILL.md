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

| User Intent | Mode | File |
|-------------|------|------|
| "set up a new idea workspace" | **setup** | `modes/setup.md` |
| "survey literature on X" | **survey** | `modes/survey.md` |
| "evaluate/validate the current idea" | **evaluate** | `modes/evaluate.md` |
| "propose new directions" | **propose** | `modes/propose.md` |
| "auto-explore the idea tree" | **auto** | `modes/auto.md` |
| "show me the current proposal" | **draft** | `modes/draft.md` |
| "write the final proposal" | **converge** | `modes/converge.md` |

**If the user gives a raw idea with no existing workspace**, start with **setup** then proceed to **survey** or **auto**.

**If ambiguous**, ask: "Which mode? setup / survey / evaluate / propose / auto / draft / converge"

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
|   +-- proposals/                <- Final output documents
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
