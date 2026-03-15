---
name: create_skill_with_paper
description: Turn an academic paper into a reusable Claude Code skill for quick reference and reproduction in future projects.
---

# create_skill_with_paper

Turn an academic paper + its code repo into a reusable skill so you can quickly adopt and integrate the method in any project, staying faithful to the original implementation.

## When to Use

- User provides a paper (PDF path, arXiv link, or title)
- User wants to reuse a paper's method in a new project
- User wants a quick-reference card for a paper's setup, dependencies, and core API

## Workflow

### Step 1: Gather Inputs

Ask the user for:

| Input | Required | Example |
|-------|----------|---------|
| Paper | Yes | arXiv link, PDF path, or title |
| Code repo | Yes (search if not provided) | GitHub URL |
| Skill name | Optional | Default: `snake_case` of short paper name |

A code repo is **required**. If the user doesn't provide one, you must search for it (check the paper, Papers With Code, GitHub). If no official repo exists, tell the user and ask how to proceed.

### Step 2: Read the Paper

- If PDF path: read with the Read tool
- If arXiv link: fetch the abstract page, then download/read the PDF
- If title only: web-search for the paper, find arXiv or official link

Extract these key elements:

1. **Paper identity** — title, authors, year, venue, links
2. **Problem & contribution** — what problem does it solve, what's novel
3. **Method overview** — high-level algorithm / architecture (not full math)
4. **Key components** — named modules, losses, architectures worth remembering
5. **Evaluation highlights** — main benchmarks, key results, comparisons

### Step 3: Clone & Deep-Read the Code

**You MUST clone the repo and read the actual source code.** Do not just skim the README.

```bash
# Clone into a temp location
git clone <repo_url> /tmp/paper_skill_<method_name>
```

#### 3a: Understand project structure

Map out the repo — entry points, core modules, config system, data pipeline:

| What to Extract | Where to Look |
|----------------|---------------|
| Dependencies & versions | `requirements.txt`, `setup.py`, `pyproject.toml`, `environment.yml` |
| Entry points | `train.py`, `run.py`, `main.py`, CLI args |
| Config system | `configs/`, argparse, hydra, omegaconf |
| Core model code | `models/`, `networks/`, `modules/` |
| Data pipeline | `datasets/`, `data/`, dataloader setup |
| Pre-trained weights | README download links, model zoo |

#### 3b: Read core implementation files

Read the actual source files for the method's core components. For each key module:

- Read the file completely (don't just skim)
- Record the **exact class names, function signatures, and constructor arguments**
- Trace the forward pass / main algorithm flow through the code
- Note which classes/functions a user would need to import and call
- Identify default hyperparameters and their values in code (not just CLI flags)

#### 3c: Cross-reference paper ↔ code

Build an explicit mapping between paper concepts and code locations:

- Which class implements the model described in Section X?
- Which function implements the loss from Equation Y?
- Where are the key hyperparameters (from Table Z) set in code?
- How does the data preprocessing match what the paper describes?

This mapping becomes the **Paper-Code Mapping** section in the skill.

#### 3d: Identify integration patterns

Figure out how someone would **use this code in their own project** (not just run the repo's scripts):

- What are the minimal imports needed?
- How do you instantiate the model, load weights, and run inference?
- What data format does the model expect (tensor shapes, dtypes, normalization)?
- Are there clean API boundaries, or is everything entangled with the training script?
- If the code is entangled, document the minimum extraction needed

#### 3e: Clean up

```bash
rm -rf /tmp/paper_skill_<method_name>
```

### Step 4: Name & Organize the Skill

#### Naming Convention

Use the pattern: `paper_<domain>__<method_name>` (double underscore separates domain from method).

The `paper_` prefix distinguishes paper-derived skills from other skill types (tools, workflows, etc.).

| Domain Prefix | Area | Example Skill Names |
|---------------|------|---------------------|
| `paper_3d__` | 3D vision, NeRF, reconstruction | `paper_3d__gaussian_splatting`, `paper_3d__instant_ngp` |
| `paper_gen__` | Generative models, diffusion | `paper_gen__stable_diffusion`, `paper_gen__flow_matching` |
| `paper_det__` | Object detection | `paper_det__yolov9`, `paper_det__detr` |
| `paper_seg__` | Segmentation | `paper_seg__sam`, `paper_seg__mask2former` |
| `paper_llm__` | Large language models | `paper_llm__llama3`, `paper_llm__moe_routing` |
| `paper_vlm__` | Vision-language models | `paper_vlm__llava`, `paper_vlm__clip` |
| `paper_rl__` | Reinforcement learning | `paper_rl__ppo`, `paper_rl__grpo` |
| `paper_opt__` | Optimization, training methods | `paper_opt__lora`, `paper_opt__deepspeed` |
| `paper_data__` | Data processing, augmentation | `paper_data__webdataset`, `paper_data__albumentations` |
| `paper_rob__` | Robotics, embodied AI | `paper_rob__diffusion_policy`, `paper_rob__act` |
| `paper_accel__` | Acceleration, inference speedup | `paper_accel__vllm`, `paper_accel__tensorrt` |
| `paper_misc__` | Doesn't fit elsewhere | `paper_misc__<name>` |

**Rules:**
- Domain prefix groups related papers — they sort together alphabetically
- Method name should be the widely-known short name (e.g. `sam` not `segment_anything_model`)
- If the paper introduces a named method, use that name; otherwise use a descriptive 2-3 word slug
- If a paper spans multiple domains, pick the primary one
- Ask the user to confirm the name if ambiguous

#### Adding New Domain Prefixes

If none of the existing prefixes fit, create a new one:
- Keep it to 2-5 lowercase chars
- Add it to this table (edit this skill file) so future skills stay consistent

### Step 5: Generate the Skill

Create the skill directory under the user's skills path:

In the repo, paper skills go under `skills/papers/`. They get installed flat into `~/.claude/skills/`.

```
skills/papers/paper_<domain>__<method_name>/
├── SKILL.md          # Core reference
├── examples.md       # Reproduction & usage recipes
└── templates/        # Config/script templates if useful
```

Use the templates below for each file.

## What to Include vs. Skip

| Include | Skip |
|---------|------|
| Core method description (1-2 paragraphs) | Full mathematical derivations |
| Architecture diagram (ASCII or description) | Every ablation result |
| Installation commands | Prose explanations of background |
| Key CLI commands & config flags | Exhaustive API docs (list what matters) |
| Dependency list with versions | Related work survey |
| Common usage scenarios | Full training logs |
| Known gotchas / tips | |
| Links to paper, repo, weights | |
| **Paper-Code Mapping** (paper concept → file:class) | |
| **Exact class names, imports, function signatures** | |
| **Code Integration Guide** (how to use in your project) | |
| **Input/output tensor shapes & data formats** | |

## Key Principles

1. **Code-faithful** — use the original code's class names, function signatures, and patterns; never invent wrapper APIs that don't exist in the repo
2. **Skim-friendly** — tables and code blocks over prose
3. **Reproducible** — enough info to set up and run from scratch
4. **Linkable** — always include paper URL, repo URL, weight URLs
5. **Integration-ready** — a reader should be able to import and use the paper's code in their own project by following the skill
6. **Scenario-driven** — organize around "I want to do X" not "Section 3.2 says..."
