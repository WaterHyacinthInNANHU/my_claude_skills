# Auto Experiment Skill

Automated iterative experiment workflow for ML/AI research.

## Usage

```
/auto_experiment
```

## Inputs

| Input | Description |
|-------|-------------|
| `code` | Path to code repository |
| `data` | Path to dataset |
| `workspace` | Path for experiment workspace |
| `instruction` | What experiment to run |

## Workflow

1. **Confirm Inputs** — Verify paths, clarify instructions
2. **Setup Workspace** — Branch, symlink data, install hooks/scripts
3. **Plan** — Explore codebase, define baselines, create plan in sketch.md
4. **Experiment Loop** — Setup round → Run → Monitor/Early stop → Analyze → Propose → Loop
5. **Final Report** — Use `/experiment_report`

## Key Features

- **Iterative loop** with per-round git branching (`autoresearch/<tag>-r1`, `-r2`, ...)
- **Early stopping** heuristics comparing against baselines
- **Context preservation** via SessionStart hook + incremental sketch.md updates
- **Two-level logging**: doc/agent/ for high-level, git notes for implementation details
- **Data safety**: Symlinks only, never modify source

## File Organization

| File | Role |
|------|------|
| `SKILL.md` | Full workflow (Steps 1-5) — read first |
| `CLAUDE.md.template` | Workspace agent instructions — single source of truth |
| `templates/*.template` | Context file templates (sketch, architecture, findings, etc.) |
| `templates/scripts/` | setup.sh, monitor.sh, cleanup.sh, archive-experiment.sh |
| `templates/hooks/` | SessionStart context restoration hook |
| `templates/experiment_loop.md` | Analysis guide and diagnosis checklist |
| `templates/monitoring_guide.md` | Smoke test and execution reference |

## Integration

- **Reporting**: `/experiment_report`
- **Cluster**: `/ucr_hpcc_cluster` (for SLURM jobs)
