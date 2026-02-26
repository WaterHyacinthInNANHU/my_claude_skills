---
name: python_project_layout
description: Refactor Python projects to follow modern best-practice directory structure using src layout and pyproject.toml.
---

# python_project_layout

Refactor Python projects to follow modern best-practice directory structure using src layout, pyproject.toml, and proper package organization.

## When to Use This Skill

Use when the user asks to:
- Restructure or refactor a Python project layout
- Convert a flat layout to src layout
- Set up a new Python project/package
- Add or fix pyproject.toml configuration
- Organize tests, docs, or scripts properly

## Refactoring Workflow

1. **Assess** the current project structure (run `find . -type f -name '*.py'` or use Glob)
2. **Identify** the layout type (flat, src, or unstructured)
3. **Plan** the migration — map every file to its new location
4. **Confirm** the plan with the user before moving files
5. **Execute** — create directories, move files, update imports
6. **Configure** — write/update pyproject.toml
7. **Verify** — run tests and check imports still work

## Target Structure: src Layout

The **src layout** is the recommended structure for Python projects. It prevents accidental imports of the local package over the installed version and ensures tests run against the installed package.

```
project-name/
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── __main__.py          # optional: python -m package_name
│       ├── core.py              # core domain logic
│       ├── cli.py               # CLI entry points
│       ├── models.py            # data models
│       ├── utils.py             # shared utilities
│       └── subpackage/
│           ├── __init__.py
│           └── module.py
├── tests/
│   ├── __init__.py              # optional (needed for relative imports)
│   ├── conftest.py              # pytest fixtures
│   ├── test_core.py
│   ├── test_cli.py
│   └── test_models.py
├── docs/                        # optional
├── scripts/                     # optional: standalone scripts
├── pyproject.toml               # REQUIRED: metadata + build + tool config
├── README.md
├── LICENSE
└── CHANGELOG.md                 # optional
```

### When to Use Flat Layout Instead

Flat layout (package at repo root) is acceptable for:
- Single-file scripts or very small projects
- Existing large projects where migration cost is too high (NumPy, pandas)
- Internal tools that will never be distributed

```
project-name/
├── package_name/
│   ├── __init__.py
│   └── module.py
├── tests/
├── pyproject.toml
└── README.md
```

## Package Organization Principles

### Module Naming

| Pattern | Use For |
|---------|---------|
| `core.py` or `main.py` | Primary business logic |
| `cli.py` | Command-line interface |
| `api.py` | Web API / external interface |
| `models.py` | Data classes, schemas, ORM models |
| `utils.py` | Small shared helpers (keep it small) |
| `config.py` | Configuration loading and defaults |
| `exceptions.py` | Custom exception classes |
| `constants.py` | Project-wide constants |
| `types.py` | Type aliases and protocols |

### Subpackage Strategy

Split into subpackages when a single package exceeds ~10 modules or when there are clear domain boundaries:

```python
src/package_name/
├── __init__.py
├── core/          # domain logic
├── api/           # HTTP/gRPC layer
├── db/            # database layer
├── auth/          # authentication
└── utils/         # cross-cutting helpers
```

### Anti-Patterns to Avoid

- Scattering `.py` files at the repo root without a package directory
- Mixing tests with source code inside the package
- "Grab bag" modules where unrelated code accumulates (e.g. a 2000-line `utils.py`)
- Multiple top-level packages with no clear relationship
- Putting data files or large assets inside the Python package

## pyproject.toml Configuration

### Minimal (src layout with setuptools)

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"

[project]
name = "package-name"
version = "0.1.0"
description = "Short description."
requires-python = ">=3.10"
dependencies = []

[tool.setuptools.packages.find]
where = ["src"]
```

### Minimal (src layout with hatchling)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "package-name"
version = "0.1.0"
description = "Short description."
requires-python = ">=3.10"
dependencies = []
```

### Full Example

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"

[project]
name = "package-name"
version = "0.1.0"
description = "Short description of the project."
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [{name = "Author Name", email = "author@example.com"}]
keywords = ["keyword1", "keyword2"]
dependencies = [
    "requests>=2.28",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.4", "mypy>=1.0"]
docs = ["sphinx>=7.0", "sphinx-rtd-theme"]

[project.scripts]
my-cli = "package_name.cli:main"

[project.urls]
Homepage = "https://github.com/user/project"
Issues = "https://github.com/user/project/issues"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.10"
strict = true
```

### Dynamic Version (read from __init__.py)

```toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "package_name.__version__"}
```

## Test Organization

Tests mirror the package structure and live in a top-level `tests/` directory:

```
tests/
├── conftest.py         # shared fixtures
├── test_core.py        # tests for src/package_name/core.py
├── test_cli.py
└── subpackage/
    └── test_module.py  # tests for src/package_name/subpackage/module.py
```

### Key Rules

- **Never include test data in the package** — use fixtures, factories, or external downloads
- **Tests stay outside `src/`** — they are not shipped in the wheel
- **Use `conftest.py`** for shared pytest fixtures
- Run tests with: `pip install -e ".[dev]" && pytest`

## Import Update Checklist

After moving files, update all affected imports:

1. **Relative imports within the package** — should still work if the internal structure is preserved
2. **Absolute imports** — update to reflect new `package_name.module` paths
3. **Test imports** — must use the installed package name (not relative paths to `src/`)
4. **Entry points / scripts** — update `[project.scripts]` paths in pyproject.toml
5. **CI/CD configs** — update paths in Makefile, GitHub Actions, tox.ini, etc.
6. **`__init__.py` re-exports** — ensure public API is still exposed

## Development Installation

After restructuring, install in editable mode:

```bash
# With pip
pip install -e ".[dev]"

# With uv
uv pip install -e ".[dev]"
```

This creates a link so code changes are reflected immediately without reinstalling.
