---
name: paper_rob__bpp
description: BPP (Big Picture Policies) -- long-context robot imitation learning via VLM-detected keyframes to reduce history distribution shift
---

# paper_rob__bpp

**Big Picture Policies (BPP)** conditions robot policies on VLM-detected behaviorally salient keyframes instead of raw observation histories. By projecting diverse rollout histories onto a compact set of task-relevant events, BPP reduces distribution shift between training and deployment, achieving 70% higher real-world success rates than the best baseline.

## Paper Info

| Field | Value |
|-------|-------|
| Title | BPP: Long-Context Robot Imitation Learning by Focusing on Key History Frames |
| Authors | Max Sobol Mark, Jacky Liang, Maria Attarian, Chuyuan Fu, Debidatta Dwibedi, Dhruv Shah, Aviral Kumar |
| Affiliation | Google DeepMind / Carnegie Mellon University |
| Year | 2026 |
| Venue | arXiv preprint |
| Paper | [arXiv:2602.15010](https://arxiv.org/abs/2602.15010) |
| Project Page | [bigpicturepolicies.github.io](https://bigpicturepolicies.github.io/) |
| Code | **Not publicly released** (as of March 2026) |

## Problem & Motivation

Many manipulation tasks require memory of past events (e.g., which drawer was already opened, which mug was picked up). Naive approaches:

- **Current-observation-only**: Fails on tasks needing history (14.4% avg success)
- **Full history conditioning**: Creates spurious correlations -- policies latch onto incidental features of training histories that don't generalize to out-of-distribution trajectories at deployment (12.8% avg success)

BPP's insight: condition on a **minimal, semantically meaningful** subset of history frames (keyframes) detected by a VLM, dramatically reducing the space of possible inputs the policy must handle.

## Method Overview

```
                              VLM (Gemini 3 Pro)
                              "Has a drawer just been opened?"
                                       │
                                       ▼
Wrist camera stream ──> 1 Hz query ──> Binary classifier ──> Rising-edge detector
   (50 Hz)                                                         │
                                                                   ▼
                                                        Keyframe set K_t
                                                        (latency-masked: Δ=3s)
                                                                   │
                                                                   ▼
                              ┌─────────────────────────────────────┐
                              │     Diffusion Transformer Policy    │
                              │                                     │
                              │  Inputs:                            │
                              │   • Current obs o_t (4 cameras)     │
                              │   • Keyframe obs {o_k} for k ∈ K_t │
                              │   • Proprioceptive state            │
                              │                                     │
                              │  Output:                            │
                              │   • 50-step action chunk            │
                              │     (joint positions + grippers)    │
                              └─────────────────────────────────────┘
```

### Keyframe Detection

1. **VLM query**: Gemini 3 Pro receives wrist camera image at 1 Hz with a task-specific binary prompt (e.g., "has the robot just picked up a mug?")
2. **Rising-edge detection**: Keyframe registered when VLM output transitions from NO to YES:
   ```
   K = {t : φ(o_t) = 1 ∧ φ(o_{t-1}) = 0}
   ```
3. **Latency masking**: During training, keyframes newer than Δ=3 seconds are excluded to simulate real-world VLM latency (3-5s per query):
   ```
   K_t^Δ = {k ∈ K_t : k ≤ t - Δ}
   ```

### Policy Architecture

| Component | Specification |
|-----------|---------------|
| Image encoder | ResNet34, separate weights per camera view, shared across timesteps |
| Policy backbone | 7-layer Transformer decoder |
| Hidden size | 512 |
| Attention heads | 8 |
| Dropout | 0.1 |
| Action decoder | DDPM diffusion |
| Action chunk length | 50 timesteps |
| Control frequency | 50 Hz |

The policy conditions on: `π_θ(a_t | o_t, {o_k}_{k ∈ K_t^Δ})`

### VLM Prompts (Examples)

| Task | Prompt (abbreviated) |
|------|---------------------|
| Mug Replacement | "Decide whether the robot hand has **just picked up** a mug. If the gripper is completely grabbing a mug and it wasn't before, answer YES." |
| Marshmallows | "Decide whether the robot hand has **just dropped marshmallows** into the red bowl. If the gripper is open and on top of the red bowl, and was closed before, answer YES." |
| Drawer Search | "Determine whether in any of the two wrist views, **a drawer is open**. If a drawer is open, answer YES." |
| Stacking Puzzle | "Decide whether the robot hand has **just picked up a piece**. If the gripper is completely grabbing a piece and wasn't before, answer YES." |

## Robot Platform

**ALOHA 2** (bimanual):

| Spec | Value |
|------|-------|
| Cameras | 4 RGB views: top, worm's-eye, 2 wrist-mounted |
| Action space | Target joint positions + gripper commands (both arms) |
| Control rate | 50 Hz |
| Observation | 4 RGB images + proprioceptive state |

## Tasks & Data

### Real-World Tasks (ALOHA 2)

| Task | Demos | History Need |
|------|-------|-------------|
| Mug Replacement | 200 (of 900 collected) | Remember which mug was picked up |
| Marshmallows | 250 | Remember which marshmallows were already placed |
| Drawer Search | 200 | Remember which drawers were already checked |
| Stacking Puzzle | 200 | Remember which pieces were already stacked |

### Simulation Tasks (MuJoCo)

| Task | Demos | Description |
|------|-------|-------------|
| Ingredient-Insertion | 900 | Sequential insertion requiring memory |
| Fixed-Password | 600 | Fixed sequence recall |
| Variable-Password | 900 | Variable sequence recall |

Data collected from 1-5 human teleoperators to introduce behavioral diversity.

## Key Hyperparameters

| Parameter | Value |
|-----------|-------|
| Action chunk length | 50 timesteps |
| History window | 4-5 past keyframes (task-dependent) |
| Observation horizon | 12-40 seconds |
| VLM query frequency | 1 Hz |
| VLM latency mask (Δ) | 3 seconds |
| VLM model | Gemini 3 Pro |
| Diffusion steps (DDPM) | 50 |

## Results

### Real-World Success Rates

| Task | Current-Only | Naive History | PTP | **BPP** |
|------|-------------|---------------|-----|---------|
| Drawer Search | 11.1% | 0% | 0% | **33.3%** |
| Marshmallows | 40% | 25% | 35% | **65%** |
| Mug Replacement | 0% | 5% | 40% | **60%** |
| Stacking Puzzle | 6.5% | 21% | 52% | **56%** |
| **Average** | 14.4% | 12.8% | 31.8% | **53.6%** |

BPP achieves **70% relative improvement** over the best baseline (PTP) on average.

### Key Ablations

| Ablation | Success (Mug task) | Notes |
|----------|-------------------|-------|
| Oracle keyframes | 70% | Upper bound with perfect detection |
| VLM keyframes (BPP) | 60% | 10% gap from VLM noise |
| Frozen encoder | 43.5% vs 55.5% | Unfreezing encoder helps (Fixed Password) |
| Data scaling (Naive) | Matches BPP at ~600+ demos | BPP is far more data-efficient |

## Integration Notes

### Reimplementation Guide

Since no code is released, here's how to reimplement BPP:

**1. Keyframe detector** (can be independent module):
```python
# Pseudocode for VLM keyframe detection
class KeyframeDetector:
    def __init__(self, vlm, prompt, query_hz=1.0, latency_mask=3.0):
        self.vlm = vlm          # e.g., Gemini 3 Pro API
        self.prompt = prompt     # task-specific binary question
        self.query_hz = query_hz
        self.latency_mask = latency_mask
        self.prev_response = False
        self.keyframes = []

    def update(self, obs_t, t):
        response = self.vlm.query(obs_t["wrist_image"], self.prompt)  # binary
        # Rising-edge detection
        if response and not self.prev_response:
            self.keyframes.append(t)
        self.prev_response = response
        # Return latency-masked keyframes
        return [k for k in self.keyframes if k <= t - self.latency_mask]
```

**2. Policy architecture**: Standard Diffusion Transformer with action chunking. Can build on existing codebases:
- [Diffusion Policy](https://github.com/real-stanford/diffusion_policy) (Chi et al., 2023)
- [ACT](https://github.com/tonyzhaozh/act) (for ALOHA platform)

**3. Key modifications to standard diffusion policy**:
- Accept variable number of keyframe observations as additional context
- ResNet34 encoder with separate weights per camera, shared across timesteps
- Concatenate/cross-attend keyframe tokens with current observation tokens

### Combining with Other Methods

BPP's keyframe detection is **policy-agnostic** -- it can be applied to any history-conditioned policy:
- Replace naive history with VLM-detected keyframes in any transformer-based policy
- Compatible with ACT, Diffusion Policy, or VLA-based approaches
- The VLM component runs independently at 1 Hz, decoupled from the 50 Hz control loop

## Tips & Gotchas

- **Latency masking is critical**: Without it, training assumes instant keyframe detection but deployment has 3-5s VLM latency, causing distribution shift.
- **Rising-edge detection matters**: Raw binary VLM output would give continuous "YES" after an event; rising-edge captures the *moment* of change.
- **Task-specific prompts required**: Each task needs a custom prompt describing the behaviorally salient event. Prompts focus on state *transitions* ("has **just** picked up"), not static states.
- **VLM cost**: Gemini 3 Pro at 1 Hz is feasible for real-time robotics but adds API cost and latency. Consider local VLMs for deployment.
- **Data diversity helps**: Using multiple teleoperators creates naturally diverse histories, which BPP handles better than naive conditioning.
- **BPP is most valuable when**: (a) tasks require history, (b) diverse demonstrations exist, and (c) full history conditioning fails due to distribution shift.
