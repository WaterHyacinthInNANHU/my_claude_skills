# my_claude_skill

Custom Claude Code skills for common workflows.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/my_claude_skill.git
   ```

2. Add to your Claude Code settings (`~/.claude/settings.json`):
   ```json
   {
     "skills": [
       "/path/to/my_claude_skill"
     ]
   }
   ```

   Or for project-specific setup, add to `.claude/settings.json` in your project:
   ```json
   {
     "skills": [
       "/path/to/my_claude_skill"
     ]
   }
   ```

## Available Skills

| Skill | Description |
|-------|-------------|
| `hpc_cluster` | UCR HPCC cluster commands - Slurm jobs, modules, storage |

## Usage

Once installed, invoke a skill with `/skill_name` in Claude Code.
