# Reference: Skill Creation

## Directory Structure

```
skills/
└── skill_name/
    ├── SKILL.md        # Required: Main documentation
    ├── examples.md     # Optional: Usage examples
    ├── reference.md    # Optional: Quick reference
    └── templates/      # Optional: Reusable files
```

## File Purposes

| File | Purpose | When to Include |
|------|---------|-----------------|
| `SKILL.md` | Core commands and concepts | Always (required) |
| `examples.md` | Step-by-step workflows | Complex multi-step tasks |
| `reference.md` | Quick lookup tables | Many commands/options |
| `templates/` | Boilerplate files | Repetitive configurations |

## SKILL.md Template

```markdown
# skill_name

One-line description of what this skill does.

## Section 1

| Command | Description |
|---------|-------------|
| `cmd1` | Does X |
| `cmd2` | Does Y |

## Section 2

```bash
# Example usage
command --flag value
```
```

## Markdown Best Practices

| Element | Use For |
|---------|---------|
| `# H1` | Skill title only |
| `## H2` | Major sections |
| `### H3` | Subsections |
| Tables | Command references |
| Code blocks | Examples |
| Lists | Steps, options |

## Code Block Languages

| Language | Use For |
|----------|---------|
| `bash` | Shell commands |
| `python` | Python code |
| `javascript` | JS/Node code |
| `json` | Config files |
| `yaml` | YAML configs |
| `markdown` | Documentation |
| (none) | Plain text output |

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Directory | `snake_case` | `aws_lambda` |
| Main file | `SKILL.md` | `SKILL.md` |
| Other docs | `lowercase.md` | `examples.md` |
| Templates | Original extension | `config.yaml` |

## Installation

```bash
# Copy single skill
cp -r skills/my_skill ~/.claude/skills/

# Copy all skills
cp -r skills/* ~/.claude/skills/
```

## Content Guidelines

### Do

- Use tables for command references
- Include runnable code examples
- Organize by task/topic
- Keep descriptions brief
- Use consistent formatting

### Don't

- Write long explanatory paragraphs
- Include obvious information
- Duplicate content across files
- Use inconsistent code formatting
- Add unnecessary sections

## Section Ideas

Common sections to include in skills:

| Section | Content |
|---------|---------|
| Quick Start | Most common commands |
| Commands | Full command reference |
| Examples | Real-world usage |
| Configuration | Config file options |
| Troubleshooting | Common errors/fixes |
| Tips | Pro tips, shortcuts |

## Template Files

For `templates/` directory:

| File Type | Examples |
|-----------|----------|
| Scripts | `job.sh`, `run.py` |
| Configs | `config.yaml`, `.env.example` |
| Boilerplate | `Dockerfile`, `Makefile` |
