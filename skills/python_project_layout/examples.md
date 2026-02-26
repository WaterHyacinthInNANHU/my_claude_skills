# Examples: Python Project Layout Refactoring

## Example 1: Unstructured Scripts → src Layout

### Before (messy)

```
my_project/
├── main.py
├── helpers.py
├── database.py
├── config.py
├── test_main.py
├── test_database.py
├── requirements.txt
└── README.md
```

### Step 1: Create directory structure

```bash
mkdir -p src/my_project tests
```

### Step 2: Move source files

```bash
mv main.py src/my_project/
mv helpers.py src/my_project/utils.py
mv database.py src/my_project/
mv config.py src/my_project/
touch src/my_project/__init__.py
```

### Step 3: Move tests

```bash
mv test_main.py tests/
mv test_database.py tests/
touch tests/conftest.py
```

### Step 4: Convert requirements.txt → pyproject.toml

Read `requirements.txt` and create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "sqlalchemy>=2.0",
    "requests>=2.28",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Step 5: Update imports

In `src/my_project/main.py`:
```python
# Before
from helpers import some_func
from database import get_connection

# After
from my_project.utils import some_func
from my_project.database import get_connection
```

In `tests/test_main.py`:
```python
# Before
from main import app

# After
from my_project.main import app
```

### Step 6: Install and verify

```bash
pip install -e ".[dev]"
pytest
```

### After (clean)

```
my_project/
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── main.py
│       ├── database.py
│       ├── config.py
│       └── utils.py
├── tests/
│   ├── conftest.py
│   ├── test_main.py
│   └── test_database.py
├── pyproject.toml
└── README.md
```

---

## Example 2: Flat Layout → src Layout

### Before

```
mypackage/
├── mypackage/
│   ├── __init__.py
│   ├── core.py
│   └── cli.py
├── tests/
│   └── test_core.py
├── setup.py
├── setup.cfg
└── README.md
```

### Migration

```bash
# Create src directory and move package into it
mkdir src
mv mypackage src/

# Remove old setup files (replaced by pyproject.toml)
rm setup.py setup.cfg
```

Create `pyproject.toml` with the same metadata from `setup.py`/`setup.cfg`.

No import changes needed if internal imports already use the package name (`from mypackage.core import ...`).

### After

```
mypackage/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── core.py
│       └── cli.py
├── tests/
│   └── test_core.py
├── pyproject.toml
└── README.md
```

---

## Example 3: Single Script → Proper Package

### Before

```
project/
└── analysis.py    # 800-line script doing everything
```

### Step 1: Identify logical domains in the script

Read through `analysis.py` and identify sections:
- Data loading and parsing
- Data processing / transformation
- Visualization / plotting
- CLI argument handling
- Configuration constants

### Step 2: Split into modules

```bash
mkdir -p src/analysis tests
touch src/analysis/__init__.py
```

Extract code into focused modules:

```
src/analysis/
├── __init__.py
├── __main__.py      # entry point: python -m analysis
├── cli.py           # argparse / click CLI
├── config.py        # constants, defaults
├── io.py            # data loading and saving
├── processing.py    # transformation logic
└── plotting.py      # visualization
```

### Step 3: Wire up entry point

`src/analysis/__main__.py`:
```python
from analysis.cli import main

if __name__ == "__main__":
    main()
```

`pyproject.toml`:
```toml
[project.scripts]
analysis = "analysis.cli:main"
```

---

## Example 4: Adding pyproject.toml to an Existing Project

### Before (using setup.py)

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="mylib",
    version="1.2.0",
    packages=find_packages(),
    install_requires=["numpy>=1.21", "pandas>=1.3"],
    extras_require={"dev": ["pytest", "black"]},
    entry_points={"console_scripts": ["mylib=mylib.cli:main"]},
)
```

### After (pyproject.toml)

```toml
[build-system]
requires = ["setuptools>=75.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mylib"
version = "1.2.0"
requires-python = ">=3.10"
dependencies = [
    "numpy>=1.21",
    "pandas>=1.3",
]

[project.optional-dependencies]
dev = ["pytest", "black"]

[project.scripts]
mylib = "mylib.cli:main"
```

Then delete `setup.py` and `setup.cfg`.
