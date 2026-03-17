# Auto Experiment Skill

Automated experiment workflow for ML/AI research with structured planning, execution monitoring, and result analysis.

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

1. **Confirm Inputs** - Verify paths, clarify instructions with user
2. **Setup Workspace** - Create branch (`autoresearch/<tag>`), symlink data, init tracking
3. **Plan Experiment** - Use `/planning-with-files:plan` for structured planning
4. **Execute & Monitor** - Smoke test first, then full training with monitoring
5. **Analyze & Report** - Use `/experiment_report` for final documentation

## Key Features

- **Branch naming convention** from [Karpathy's autoresearch](https://github.com/karpathy/autoresearch)
- **Two-level logging**: High-level to `doc/agent/`, details to git notes
- **Data safety**: Symlinks only, never modify source data
- **Version control**: Commit before changes, easy rollback

## Templates

| File | Purpose |
|------|---------|
| `CLAUDE.md.template` | Workspace instructions for agent |
| `setup_checklist.md.template` | Initial setup verification |
| `exp_log.md.template` | Per-experiment documentation |
| `monitoring_guide.md` | Training monitoring reference |
| `results.tsv.template` | Results tracking header |

## Integration

- **Planning**: `/planning-with-files:plan`
- **Reporting**: `/experiment_report`
