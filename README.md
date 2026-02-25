# my_claude_skill

Custom Claude Code skills for common workflows.

## Installation

### Linux / macOS

```bash
git clone https://github.com/WaterHyacinthInNANHU/my_claude_skills.git
cp -r my_claude_skills/skills/* ~/.claude/skills/
```

### Windows (PowerShell)

```powershell
git clone https://github.com/WaterHyacinthInNANHU/my_claude_skills.git
Copy-Item -Recurse -Force my_claude_skills\skills\* $env:USERPROFILE\.claude\skills\
```

### Windows (Command Prompt)

```cmd
git clone https://github.com/WaterHyacinthInNANHU/my_claude_skills.git
xcopy /E /I /Y my_claude_skills\skills %USERPROFILE%\.claude\skills
```

## Update

### Linux / macOS

```bash
cd my_claude_skills
git pull
cp -r skills/* ~/.claude/skills/
```

### Windows (PowerShell)

```powershell
cd my_claude_skills
git pull
Copy-Item -Recurse -Force skills\* $env:USERPROFILE\.claude\skills\
```

### Windows (Command Prompt)

```cmd
cd my_claude_skills
git pull
xcopy /E /I /Y skills %USERPROFILE%\.claude\skills
```

## Available Skills

| Skill | Description |
|-------|-------------|
| `ucr_hpcc_cluster` | UCR HPCC cluster commands - Slurm jobs, modules, storage |
| `create_skill` | Guide for creating well-structured Claude Code skills |

## Usage

Once installed, invoke a skill with `/skill_name` in Claude Code.
