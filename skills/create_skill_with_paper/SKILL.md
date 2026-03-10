---
name: create_skill_with_paper
description: Turn an academic paper into a reusable Claude Code skill for quick reference and reproduction in future projects.
---

# create_skill_with_paper

Turn an academic paper (+ optional code repo) into a reusable skill so you can quickly adopt the method in any project.

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
| Code repo | Optional | GitHub URL (search if not provided) |
| Skill name | Optional | Default: `snake_case` of short paper name |

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

### Step 3: Find & Examine the Code

- If repo URL provided: use it
- Otherwise: check the paper for a GitHub link, or search `github.com <paper-title>`
- Clone/browse the repo to extract:

| What to Extract | Where to Look |
|----------------|---------------|
| Dependencies & versions | `requirements.txt`, `setup.py`, `pyproject.toml`, `environment.yml` |
| Entry points | `train.py`, `run.py`, `main.py`, CLI args |
| Config system | `configs/`, argparse, hydra, omegaconf |
| Core model code | `models/`, `networks/`, `modules/` |
| Data pipeline | `datasets/`, `data/`, dataloader setup |
| Pre-trained weights | README download links, model zoo |

**Don't** copy entire files — summarize the structure and key APIs.

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
| Key CLI commands & config flags | Exhaustive API docs |
| Dependency list with versions | Code that can be read from the repo |
| Common usage scenarios | Minor implementation details |
| Known gotchas / tips | Related work survey |
| Links to paper, repo, weights | Full training logs |

## Key Principles

1. **Skim-friendly** — tables and code blocks over prose
2. **Reproducible** — enough info to set up and run from scratch
3. **Linkable** — always include paper URL, repo URL, weight URLs
4. **Minimal** — you can always `git clone` for details; the skill is a cheat sheet
5. **Scenario-driven** — organize around "I want to do X" not "Section 3.2 says..."
