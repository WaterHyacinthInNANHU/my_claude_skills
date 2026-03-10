# my_claude_skills

Custom Claude Code skills for common workflows.

## Repo Structure

```
skills/
├── create_skill/                    # Core skills (always installed)
├── create_skill_with_paper/
├── python_project_layout/
├── ucr_hpcc_cluster/
├── rlinf/
└── papers/                          # Skill group (install on-demand)
    ├── paper_3d__dp3/
    └── paper_3d__utonia/
```

## Installation

```bash
git clone https://github.com/WaterHyacinthInNANHU/my_claude_skills.git
cd my_claude_skills

./install.sh                                          # Core skills only
./install.sh --papers --all                           # Core + all paper skills
./install.sh --papers paper_3d__dp3 paper_3d__utonia  # Core + specific papers
```

## Update

```bash
cd my_claude_skills
git pull
./install.sh --update       # Updates core + already-installed group skills
```

## Uninstall

```bash
./install.sh --uninstall                      # Remove all skills from this repo
./install.sh --uninstall --papers             # Remove all paper skills
./install.sh --uninstall paper_3d__dp3        # Remove a specific skill
```

## Info

```bash
./install.sh --list                           # List all available skills
./install.sh --list papers                    # List skills in a group
./install.sh --help                           # Full usage info
```

## Available Skills

### Core Skills

| Skill | Description |
|-------|-------------|
| `create_skill` | Guide for creating well-structured Claude Code skills |
| `create_skill_with_paper` | Turn academic papers into reusable skills |
| `python_project_layout` | Modern Python project structure (src layout + pyproject.toml) |
| `ucr_hpcc_cluster` | UCR HPCC cluster commands — Slurm jobs, modules, storage |
| `rlinf` | RLinf RL training framework troubleshooting on HPCC |

### Paper Skills (on-demand)

| Skill | Description |
|-------|-------------|
| `paper_3d__dp3` | 3D Diffusion Policy — imitation learning with point clouds |
| `paper_3d__utonia` | Cross-domain pre-trained Point Transformer V3 encoder |

> Paper skills use the naming convention `paper_<domain>__<method>`.
> See `create_skill_with_paper` for domain prefixes and how to add new papers.

## Usage

Once installed, invoke a skill with `/skill_name` in Claude Code.
