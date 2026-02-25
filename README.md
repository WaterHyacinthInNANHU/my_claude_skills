# my_claude_skill

Custom Claude Code skills for common workflows.

## Installation

```bash
git clone https://github.com/WaterHyacinthInNANHU/my_claude_skills.git
cp -r my_claude_skills/skills/* ~/.claude/skills/
```

## Update

Pull the latest skills:

```bash
cd my_claude_skills
git pull
cp -r skills/* ~/.claude/skills/
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `ucr_hpcc_cluster` | UCR HPCC cluster commands - Slurm jobs, modules, storage |
| `create_skill` | Guide for creating well-structured Claude Code skills |

## Usage

Once installed, invoke a skill with `/skill_name` in Claude Code.
