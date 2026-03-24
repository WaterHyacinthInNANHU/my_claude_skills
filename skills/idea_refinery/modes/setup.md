# Mode: Setup

Create a git-managed idea refinery workspace.

## Trigger

User says: "set up a new idea workspace", "start refining an idea", or begins with a seed idea and no workspace exists.

## Procedure

### 1. Gather Inputs

**ASK USER** for:

1. **Workspace path** — where to create the workspace
2. **Tag** — short slug (e.g., `3d-vla-robust`)
3. **Seed idea** — even one sentence is fine

### 2. Run Setup Script

```bash
bash <skill_path>/templates/scripts/setup.sh \
  --workspace <path> \
  --tag <idea_slug> \
  --idea "<seed idea text>"
```

This creates the full workspace structure:

```
<workspace>/
├── refs.db                       <- Paper reference database (SQLite + FTS5)
├── config.md                     <- Global constraints & search params
├── scripts/
│   ├── refs.py                   <- Reference DB CLI
│   └── status.py                 <- Compact status generator
├── doc/
│   ├── agent/
│   │   ├── sketch.md             <- Current state & next steps
│   │   ├── findings.md           <- Accumulated insights
│   │   ├── decisions.md          <- Direction decisions
│   │   ├── idea_versions/
│   │   │   └── v0_seed.md
│   │   ├── directions/
│   │   └── validations/
│   └── proposals/
├── CLAUDE.md
└── .claude/hooks/
```

### 3. Configure Constraints

**ASK USER** to fill `config.md`:

| Resource | Ask About |
|----------|-----------|
| Compute | # GPUs, type (A100/H100/etc.), hours available |
| Time | Deadline or time budget |
| Data | What datasets are accessible |
| Team | Solo or collaborators, expertise areas |
| Codebase | Starting from scratch or building on existing code |

Update `config.md` with their answers. Set hard constraints (auto-reject violations) vs. soft preferences (break ties).

### 4. Capture Seed Idea

Record in `doc/agent/idea_versions/v0_seed.md` (idea card template) and update `sketch.md`.

```bash
git add -A && git commit -m "seed: <1-line idea summary>"
```

### 5. Suggest Next Step

Tell the user:
- "Workspace ready. Run `/idea_refinery survey` to survey literature around this idea."
- "Or run `/idea_refinery evaluate` to validate the seed directly."
- "Or run `/idea_refinery auto` for automated exploration."
