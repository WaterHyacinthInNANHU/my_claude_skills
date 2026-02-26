---
name: create_skill
description: Guide for creating well-structured Claude Code skills following best practices.
---

# create_skill

Guide for creating well-structured Claude Code skills following best practices.

## Skill Structure

A skill should be organized as a directory with multiple files:

```
skills/
└── skill_name/
    ├── SKILL.md        # Main documentation (required)
    ├── examples.md     # Usage examples
    ├── reference.md    # Quick reference / cheatsheet
    └── templates/      # Reusable templates
        └── *.sh, *.py, etc.
```

## SKILL.md Structure

The main skill file **must** start with YAML frontmatter for discoverability:

```yaml
---
name: skill_name
description: One-line summary of what the skill does.
---
```

Then include:

1. **Title** - Skill name as H1 header (must match directory name)
2. **Description** - One-line summary of what the skill does
3. **Core Content** - The main instructions, commands, or guidance
4. **Sections** - Organized by topic with H2 headers

## Best Practices

### 1. Design for Context Efficiency

Skills are loaded into Claude's context window. Keep them:
- **Concise** - Include only essential information
- **Scannable** - Use tables, lists, and code blocks
- **Actionable** - Focus on commands and procedures, not explanations

### 2. Use the 3-File Pattern

| File | Purpose | Content |
|------|---------|---------|
| `SKILL.md` | Core knowledge | Essential commands and concepts |
| `examples.md` | Learning | Step-by-step workflows |
| `reference.md` | Quick lookup | Tables, cheatsheets |

### 3. Include Templates

For repetitive tasks, provide templates in `templates/` directory:
- Job scripts
- Config files
- Boilerplate code

### 4. Write for Search

Use clear, searchable headings:
- "## Job Submission" not "## How to Submit"
- "## GPU Jobs" not "## Using Graphics Cards"

### 5. Prefer Tables Over Prose

Tables are scannable and dense:

```markdown
| Command | Description |
|---------|-------------|
| `cmd1` | Does X |
| `cmd2` | Does Y |
```

### 6. Use Consistent Code Blocks

Always specify the language:

```bash
# Shell commands
command --flag value
```

```python
# Python code
def example():
    pass
```

## Creating a New Skill

1. Create the directory structure:
   ```bash
   mkdir -p skills/my_skill/templates
   ```

2. Create `SKILL.md` with:
   - H1 title matching directory name
   - Brief description
   - Core commands/concepts

3. Add `examples.md` with real-world workflows

4. Add `reference.md` with quick-lookup tables

5. Add templates for common tasks

## Installation Location

Skills are installed to `~/.claude/skills/`:

```bash
cp -r skills/my_skill ~/.claude/skills/
```

## Skill Naming

- Use `snake_case` for directory and file names
- Keep names short but descriptive
- Prefix with domain if needed (e.g., `aws_lambda`, `docker_compose`)
