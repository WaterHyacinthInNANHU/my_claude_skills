# Unified Context Structure for Experiments

## Replaces planning-with-files

This structure is optimized for ML experiments while covering planning-with-files functionality.

```
doc/agent/
├── sketch.md          # = task_plan.md + progress.md combined
├── architecture.md    # = findings.md (technical decisions part)
├── findings.md        # Experiment-specific insights
└── exp_*.md          # Individual experiment reports
```

## Mapping from planning-with-files

| planning-with-files | This Structure | Why |
|---------------------|----------------|-----|
| task_plan.md (phases, status) | sketch.md | Combined with progress tracking |
| progress.md (session log) | sketch.md | Session log at bottom of sketch |
| findings.md (technical decisions) | architecture.md | More explicit naming |
| findings.md (research findings) | findings.md | Experiment insights |
| - | exp_*.md | New: detailed experiment reports |

## Key Difference: Enforcement

planning-with-files: Agent may or may not update
**This approach: CLAUDE.md mandates update at session boundaries**

## The Enforcement Mechanism

In CLAUDE.md, we add explicit procedures that agents MUST follow:

```markdown
## SESSION PROTOCOL (MANDATORY)

### On Session Start
YOU MUST do this BEFORE any other work:
1. Read doc/agent/sketch.md
2. State your understanding of current phase and next step
3. If unclear, ask user

### On Session End
YOU MUST do this BEFORE ending:
1. Update doc/agent/sketch.md with:
   - Current phase
   - Last action completed
   - Next steps
2. Add git notes for implementation details
3. Update results.tsv if applicable
```

## Active Update Triggers

The agent should update context files:

| Trigger | Update What |
|---------|-------------|
| Session start | Read sketch.md (verify understanding) |
| Session end | Write sketch.md (current state) |
| Design decision | architecture.md |
| Experiment complete | results.tsv + exp_N.md |
| Insight gained | findings.md |
| Any commit | git notes |
| Milestone reached | sketch.md |
| Before risky change | git commit + sketch.md |
