# Reference: Python Project Layout

## Directory Placement Cheatsheet

| File/Directory | Location | Required? | Notes |
|----------------|----------|-----------|-------|
| `pyproject.toml` | repo root | Yes | Replaces setup.py, setup.cfg |
| `README.md` | repo root | Yes | Project overview |
| `LICENSE` | repo root | Yes | Use MIT, Apache-2.0, BSD, etc. |
| `CHANGELOG.md` | repo root | No | Track notable changes |
| `src/package_name/` | `src/` | Yes | All importable Python code |
| `__init__.py` | each package dir | Yes | Makes directory a package |
| `__main__.py` | package root | No | Enables `python -m package_name` |
| `tests/` | repo root | Yes | All test code (outside src/) |
| `conftest.py` | `tests/` | No | Shared pytest fixtures |
| `docs/` | repo root | No | Sphinx/MkDocs documentation |
| `scripts/` | repo root | No | Standalone utility scripts |
| `.github/workflows/` | repo root | No | CI/CD pipelines |

## Layout Comparison

| Aspect | src Layout | Flat Layout |
|--------|-----------|-------------|
| Structure | `src/pkg/` | `pkg/` at root |
| Accidental imports | Prevented | Possible |
| Requires install | Yes (`pip install -e .`) | No |
| Test reliability | Tests use installed pkg | Tests may use local files |
| Recommended for | Libraries, new projects | Small scripts, legacy |

## pyproject.toml Sections

| Section | Purpose |
|---------|---------|
| `[build-system]` | Build backend (setuptools, hatchling, flit) |
| `[project]` | Name, version, description, dependencies |
| `[project.optional-dependencies]` | Dev/test/docs extras |
| `[project.scripts]` | CLI entry points |
| `[project.urls]` | Homepage, repo, issue tracker |
| `[tool.setuptools.packages.find]` | Package discovery (`where = ["src"]`) |
| `[tool.pytest.ini_options]` | Pytest configuration |
| `[tool.ruff]` | Linter/formatter config |
| `[tool.mypy]` | Type checker config |

## Build Backends

| Backend | Install | Best For |
|---------|---------|----------|
| setuptools | `requires = ["setuptools>=75.0"]` | Most projects, C extensions |
| hatchling | `requires = ["hatchling"]` | Pure Python, fast builds |
| flit-core | `requires = ["flit_core>=3.4"]` | Simple pure Python |
| pdm-backend | `requires = ["pdm-backend"]` | pdm users |

## Common Module Names

| Module | Purpose |
|--------|---------|
| `core.py` | Primary business logic |
| `cli.py` | CLI (argparse/click/typer) |
| `api.py` | Web API endpoints |
| `models.py` | Data classes, ORM models |
| `schemas.py` | Validation schemas (pydantic) |
| `config.py` | Settings, environment vars |
| `exceptions.py` | Custom exceptions |
| `constants.py` | Project-wide constants |
| `types.py` | Type aliases, protocols |
| `utils.py` | Shared small helpers |
| `io.py` | File I/O, data loading |

## Refactoring Commands

```bash
# Assess current structure
find . -name '*.py' -not -path './.venv/*' | head -40

# Create src layout skeleton
mkdir -p src/package_name tests
touch src/package_name/__init__.py tests/conftest.py

# Move files into src
mv module.py src/package_name/

# Find all imports that need updating
grep -rn "^from \|^import " src/ tests/ --include='*.py'

# Install in editable mode
pip install -e ".[dev]"

# Run tests to verify
pytest -v

# Check for broken imports
python -c "import package_name"
```

## Files to Delete After Migration

| Old File | Replaced By |
|----------|-------------|
| `setup.py` | `pyproject.toml` |
| `setup.cfg` | `pyproject.toml` |
| `MANIFEST.in` | `pyproject.toml` (usually) |
| `requirements.txt` | `[project].dependencies` in pyproject.toml |
| `requirements-dev.txt` | `[project.optional-dependencies].dev` |
| `tox.ini` (tool config) | `[tool.*]` sections in pyproject.toml |
| `pytest.ini` | `[tool.pytest.ini_options]` |
| `.flake8` | `[tool.ruff]` (migrate to ruff) |
| `mypy.ini` | `[tool.mypy]` |
