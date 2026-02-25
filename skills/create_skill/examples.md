# Examples: Creating Claude Code Skills

## Example 1: Simple Command Reference Skill

**Goal:** Create a skill for Docker commands

### Directory Structure

```
skills/
└── docker/
    ├── SKILL.md
    ├── examples.md
    └── reference.md
```

### SKILL.md

```markdown
# docker

Docker container management commands.

## Container Lifecycle

| Command | Description |
|---------|-------------|
| `docker run IMAGE` | Create and start container |
| `docker start ID` | Start stopped container |
| `docker stop ID` | Stop running container |
| `docker rm ID` | Remove container |

## Images

| Command | Description |
|---------|-------------|
| `docker images` | List images |
| `docker pull IMAGE` | Download image |
| `docker build -t NAME .` | Build from Dockerfile |
| `docker rmi IMAGE` | Remove image |

## Inspection

| Command | Description |
|---------|-------------|
| `docker ps` | List running containers |
| `docker ps -a` | List all containers |
| `docker logs ID` | View container logs |
| `docker exec -it ID bash` | Shell into container |
```

---

## Example 2: Workflow-Based Skill

**Goal:** Create a skill for Git workflows

### SKILL.md

```markdown
# git_workflow

Git workflows for feature development.

## Feature Branch Workflow

1. Create branch from main:
   ```bash
   git checkout main
   git pull
   git checkout -b feature/name
   ```

2. Make changes and commit:
   ```bash
   git add .
   git commit -m "Add feature"
   ```

3. Push and create PR:
   ```bash
   git push -u origin feature/name
   gh pr create
   ```

## Hotfix Workflow

1. Branch from main:
   ```bash
   git checkout -b hotfix/issue main
   ```

2. Fix, commit, and merge:
   ```bash
   git commit -am "Fix issue"
   git checkout main
   git merge hotfix/issue
   git push
   ```
```

---

## Example 3: Skill with Templates

**Goal:** Create a skill for Python project setup

### Directory Structure

```
skills/
└── python_project/
    ├── SKILL.md
    ├── reference.md
    └── templates/
        ├── pyproject.toml
        ├── setup.cfg
        └── .gitignore
```

### SKILL.md

```markdown
# python_project

Python project setup and best practices.

## Quick Start

1. Create project structure:
   ```bash
   mkdir my_project && cd my_project
   mkdir src tests
   touch src/__init__.py
   ```

2. Initialize git and virtual env:
   ```bash
   git init
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Copy templates:
   ```bash
   cp ~/.claude/skills/python_project/templates/* .
   ```

## Project Structure

```
my_project/
├── src/
│   └── __init__.py
├── tests/
├── pyproject.toml
├── setup.cfg
└── .gitignore
```
```

### templates/pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my_project"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "black", "mypy"]
```

---

## Example 4: Domain-Specific Skill

**Goal:** Create a skill for AWS S3 operations

### SKILL.md

```markdown
# aws_s3

AWS S3 storage operations using AWS CLI.

## Bucket Operations

| Command | Description |
|---------|-------------|
| `aws s3 ls` | List buckets |
| `aws s3 mb s3://bucket` | Create bucket |
| `aws s3 rb s3://bucket` | Delete bucket |

## Object Operations

| Command | Description |
|---------|-------------|
| `aws s3 cp file s3://bucket/` | Upload file |
| `aws s3 cp s3://bucket/file .` | Download file |
| `aws s3 sync dir s3://bucket/` | Sync directory |
| `aws s3 rm s3://bucket/file` | Delete object |

## Common Flags

| Flag | Description |
|------|-------------|
| `--recursive` | Apply to all objects |
| `--exclude "*.log"` | Exclude pattern |
| `--include "*.txt"` | Include pattern |
| `--dryrun` | Preview changes |
```

---

## Anti-Patterns to Avoid

### Too Much Prose

**Bad:**
```markdown
## Introduction

Docker is a platform for developing, shipping, and running applications
in containers. Containers are lightweight, standalone packages that
include everything needed to run software...
```

**Good:**
```markdown
## Containers

| Command | Description |
|---------|-------------|
| `docker run` | Create and start |
| `docker stop` | Stop running |
```

### Missing Code Examples

**Bad:**
```markdown
To list files, use the ls command with appropriate flags.
```

**Good:**
```markdown
```bash
ls -la          # List all with details
ls -lh          # Human-readable sizes
```
```

### Inconsistent Formatting

**Bad:**
```markdown
Run `docker ps` to see containers
Run docker stop ID to stop them
Use the **docker rm** command to remove
```

**Good:**
```markdown
| Command | Description |
|---------|-------------|
| `docker ps` | List containers |
| `docker stop ID` | Stop container |
| `docker rm ID` | Remove container |
```
