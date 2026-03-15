---
name: paper_rob__robocasa
description: RoboCasa -- large-scale kitchen simulation framework (365 tasks, 2500 scenes) for training generalist robots, built on robosuite/MuJoCo
---

# paper_rob__robocasa

**RoboCasa** is a large-scale simulation framework for training generalist robots on everyday kitchen tasks. Built on robosuite/MuJoCo, it provides 365 tasks across 2,500+ diverse kitchen scenes with 3,200+ object assets. Supports multiple robot embodiments (mobile manipulators, humanoids, quadrupeds) and integrates with Diffusion Policy, pi0, and GR00T.

## Paper Info

| Field | Value |
|-------|-------|
| Title (v1) | RoboCasa: Large-Scale Simulation of Everyday Tasks for Generalist Robots |
| Title (v2) | RoboCasa365: A Large-Scale Simulation Framework for Training and Benchmarking Generalist Robots |
| Authors | Soroush Nasiriany, Abhiram Maddukuri, Lance Zhang, Adeet Parikh, Aaron Lo, Abhishek Joshi, Ajay Mandlekar, Yuke Zhu |
| Year | 2024 (v1), 2026 (v2 / RoboCasa365) |
| Venue | RSS 2024 (v1), ICLR 2026 (v2) |
| Paper (v1) | [arXiv:2406.02523](https://arxiv.org/abs/2406.02523) |
| Paper (v2) | [arXiv:2603.04356](https://arxiv.org/abs/2603.04356) |
| Code | [robocasa/robocasa](https://github.com/robocasa/robocasa) |
| Project Page | [robocasa.ai](https://robocasa.ai/) |
| Docs | [robocasa.ai/docs](https://robocasa.ai/docs/build/html/introduction/overview.html) |
| License | MIT |

## Method Overview

RoboCasa is not a learning algorithm — it's a **simulation benchmark + data generation platform**. Key components:

1. **Kitchen scenes** — 60 layouts × 60 styles = 2,500+ unique environments with AI-generated textures
2. **Task suite** — 365 tasks: atomic skills (pick/place, door, drawer, knob, lever, button, insertion, navigation, rack, lid) + LLM-generated composite tasks
3. **Object assets** — 3,200+ objects across 150+ categories from Objaverse + Lightwheel + AI-generated
4. **Demonstration data** — 600+ hrs human teleoperation + 1,600+ hrs MimicGen synthetic data
5. **Cross-embodiment** — PandaOmron (default), humanoids (GR1, G1), quadrupeds (GoogleRobot)
6. **Policy integration** — Works with robomimic (BC-Transformer), Diffusion Policy, pi0, GR00T

## Paper-Code Mapping

| Paper Concept | Code Location | Notes |
|---------------|---------------|-------|
| Kitchen env base class | `robocasa/environments/kitchen/kitchen.py:Kitchen` | All tasks inherit from this; uses `KitchenEnvMeta` metaclass for auto-registration |
| Atomic tasks (25→~40) | `robocasa/environments/kitchen/atomic/kitchen_*.py` | Each file defines one skill category (e.g., `PickPlace`, `OpenDoor`) |
| Composite tasks | `robocasa/environments/kitchen/composite/<category>/<task>.py` | LLM-generated multi-step tasks |
| Scene builder | `robocasa/models/scenes/scene_builder.py:KitchenArena` | Loads YAML layout+style blueprints |
| Scene registry | `robocasa/models/scenes/scene_registry.py` | `LayoutType`, `StyleType` enums, path lookups |
| Fixture system | `robocasa/models/fixtures/fixture.py:Fixture` | `FixtureType` enum (27 types), base class |
| Object categories | `robocasa/models/objects/kitchen_objects.py` | `ObjCat` class with properties (graspable, washable, etc.) |
| Object sampling | `robocasa/models/objects/kitchen_object_utils.py:sample_kitchen_object` | Sample by group/registry |
| Task success checks | `robocasa/utils/object_utils` | `obj_inside_of()`, `gripper_obj_far()`, `obj_on_top_of()` |
| Gym wrapper | `robocasa/wrappers/gym_wrapper.py:RoboCasaGymEnv` | Standard Gymnasium interface |
| Dataset registry | `robocasa/utils/dataset_registry.py` | `ATOMIC_TASK_DATASETS`, `COMPOSITE_TASK_DATASETS` |
| Env creation helper | `robocasa/utils/env_utils.py:create_env` | Convenience wrapper around `robosuite.make()` |
| Demo collection | `robocasa/scripts/collect_demos.py:collect_human_trajectory` | SpaceMouse/keyboard teleoperation |
| Dataset playback | `robocasa/scripts/dataset_scripts/playback_dataset.py` | HDF5 trajectory playback + video export |
| Macros/config | `robocasa/macros.py` | Dataset paths, device IDs |

## Setup

### Dependencies

- Python 3.9+
- `mujoco==3.3.1`
- `numpy==2.2.5`, `scipy==1.15.3`, `numba==0.61.2`
- `tianshou==0.4.10`, `lerobot==0.3.3`, `gymnasium`
- `opencv-python`, `h5py`, `Pillow`, `pyyaml`, `imageio`
- Requires **robosuite** (installed as dependency)

### Installation

```bash
git clone https://github.com/robocasa/robocasa.git
cd robocasa
pip install -e .

# Download kitchen assets (textures, fixtures, objects)
python robocasa/scripts/download_kitchen_assets.py

# Set dataset path
python robocasa/scripts/setup_macros.py
```

### Asset Downloads

| Asset | Script Flag | Contents |
|-------|-------------|----------|
| Textures | `tex` | 400 AI-generated wall/floor/counter/cabinet textures |
| Fixtures (Lightwheel) | `fixtures_lw` | Kitchen fixture MJCF models |
| Objects (Objaverse) | `objs_objaverse` | 1,592 object models |
| Objects (Lightwheel) | `objs_lw` | Additional object models |
| Objects (AI-gen) | `objs_aigen` | AI-generated objects (for composite tasks) |

## Environment System

### Creating an Environment

```python
import robosuite
from robosuite.controllers import load_composite_controller_config

env = robosuite.make(
    env_name="PickPlaceCounterToCabinet",     # Task class name
    robots="PandaOmron",
    controller_configs=load_composite_controller_config(robot="PandaOmron"),
    has_renderer=True,                         # On-screen rendering
    has_offscreen_renderer=True,               # For camera obs
    use_camera_obs=True,
    camera_names=["robot0_agentview_left", "robot0_agentview_right", "robot0_eye_in_hand"],
    camera_heights=256,
    camera_widths=256,
    control_freq=20,                           # 20 Hz control
    horizon=1000,                              # Max steps per episode
    layout_ids=1,                              # Kitchen layout (1-60)
    style_ids=1,                               # Kitchen style (1-60)
    seed=42,
)
```

Or use the convenience wrapper:

```python
from robocasa.utils.env_utils import create_env

env = create_env(
    env_name="PickPlaceCounterToCabinet",
    robots="PandaOmron",
    split="target",                  # "target", "pretrain", "all"
    obj_instance_split="train",      # "train", "test"
    generative_textures="100p",      # AI textures
)
```

### Kitchen `__init__` Key Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `robots` | `"PandaOmron"` | Robot type string |
| `layout_ids` | `None` | Layout ID(s). Special: -1=test, -2=train, -3=all, -4=no island, -5=island |
| `style_ids` | `None` | Style ID(s). Special: -1=test, -2=train, -3=all |
| `control_freq` | `20` | Control frequency (Hz) |
| `horizon` | `1000` | Max episode length |
| `camera_names` | `"agentview"` | Camera name(s) for observations |
| `camera_heights` | `256` | Image height |
| `camera_widths` | `256` | Image width |
| `obj_registries` | `("objaverse", "lightwheel")` | Object asset sources |
| `obj_instance_split` | `None` | `"train"` or `"test"` for held-out objects |
| `generative_textures` | `None` | AI textures: `None`, `False`, or `"100p"` |
| `use_distractors` | `False` | Add distractor objects |
| `randomize_cameras` | `False` | Randomize camera poses |
| `use_novel_instructions` | `False` | Use varied language instructions |

### Scene Splits

| Split | Layouts | Styles | Use |
|-------|---------|--------|-----|
| Train | 11-60 | 11-60 | Training data |
| Test | 1-10 | 1-10 | Evaluation |
| Pretrain (data) | Train scenes | Train scenes | MimicGen + human demos |
| Target (data) | Test scenes | Test scenes | Evaluation demos |

### Observation Space

| Key | Shape | Description |
|-----|-------|-------------|
| `robot0_agentview_left_image` | `(H, W, 3)` uint8 | Left workspace camera |
| `robot0_agentview_right_image` | `(H, W, 3)` uint8 | Right workspace camera |
| `robot0_eye_in_hand_image` | `(H, W, 3)` uint8 | Wrist camera |
| `robot0_eef_pos` | `(3,)` float | End-effector position |
| `robot0_eef_quat` | `(4,)` float | End-effector quaternion |
| `robot0_gripper_qpos` | `(2,)` float | Gripper joint positions |
| `robot0_base_pos` | `(3,)` float | Mobile base position |

### Action Space

Workspace end-effector control (default for PandaOmron):

| Dims | Description |
|------|-------------|
| 0-2 | EEF position delta (x, y, z) |
| 3-5 | EEF rotation delta (rx, ry, rz) |
| 6 | Gripper command (1=open, -1=close) |
| 7-9 | Base velocity (x, y, yaw) |
| 10 | Torso height |
| 11 | Base mode toggle |

## Task System

### Task Hierarchy

```
Kitchen (base)
├── Atomic tasks (~40)
│   ├── PickPlace → PickPlaceCounterToCabinet, PickPlaceSinkToCounter, ...
│   ├── OpenDoor → OpenSingleDoor, OpenDoubleDoor, ...
│   ├── CloseDrawer, OpenDrawer
│   ├── TwistKnob, TurnOnStove, TurnOffStove
│   ├── TurnLever → TurnOnSinkFaucet, TurnOnFaucetSpout, ...
│   ├── PressButton → TurnOnMicrowave, ArrangeBowlsOnStove, ...
│   ├── Insertion → PrepareCoffeeMug, InsertToRack, ...
│   └── Navigation → NavigateTo, ...
└── Composite tasks (~325)
    ├── Brewing/ → BrewCoffee, MakeTea, ...
    ├── Washing/ → WashDishes, WashVegetables, ...
    ├── Restocking/ → RestockPantry, RestockFridge, ...
    ├── MeatPrep/ → SeasonMeat, MarinateChicken, ...
    └── ... (20 categories total)
```

### Defining a New Task

```python
from robocasa.environments.kitchen.kitchen import *

class MyCustomTask(Kitchen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _setup_kitchen_references(self):
        """Register fixture references for the task."""
        super()._setup_kitchen_references()
        self.counter = self.register_fixture_ref(
            "counter", dict(id=FixtureType.COUNTER)
        )
        self.cabinet = self.register_fixture_ref(
            "cabinet", dict(id=FixtureType.CABINET)
        )
        self.init_robot_base_ref = self.counter  # Robot spawns near counter

    def _get_obj_cfgs(self):
        """Define object placements."""
        return [dict(
            name="obj",
            obj_groups="fruit",           # Sample from fruit category
            graspable=True,
            placement=dict(
                fixture=self.counter,
                size=(0.50, 0.30),         # Sampling region size
                pos=("ref", -1.0),         # Position relative to reference
            ),
        )]

    def _setup_scene(self):
        """Set initial scene state (e.g., open doors)."""
        super()._setup_scene()
        self.cabinet.open_door(env=self)

    def get_ep_meta(self):
        """Return episode metadata including language instruction."""
        ep_meta = super().get_ep_meta()
        obj_lang = self.get_obj_lang()
        ep_meta["lang"] = f"Pick the {obj_lang} and place it in the cabinet."
        return ep_meta

    def _check_success(self):
        """Check if task is completed."""
        import robocasa.utils.object_utils as OU
        return (OU.obj_inside_of(self, "obj", self.cabinet)
                and OU.gripper_obj_far(self))
```

Tasks are **auto-registered** via the `KitchenEnvMeta` metaclass — just define the class and it becomes available via `robosuite.make(env_name="MyCustomTask", ...)`.

### Fixture Types

```python
from robocasa.models.fixtures.fixture import FixtureType

# Key types:
FixtureType.COUNTER          # 14
FixtureType.CABINET          # 18
FixtureType.FRIDGE           # 8
FixtureType.SINK             # 4
FixtureType.STOVE            # 2
FixtureType.MICROWAVE        # 1
FixtureType.OVEN             # 3
FixtureType.DISHWASHER       # 9
FixtureType.COFFEE_MACHINE   # 5
FixtureType.DRAWER           # 23
FixtureType.ISLAND           # 15
FixtureType.DISH_RACK        # 26
```

## Demonstration Data

### Dataset Registry

```python
from robocasa.utils.dataset_registry import ATOMIC_TASK_DATASETS, COMPOSITE_TASK_DATASETS
from robocasa.utils.dataset_registry_utils import get_ds_path, get_ds_meta

# Get dataset path for a task
path = get_ds_path("PickPlaceCounterToCabinet", source="human", split="pretrain")
meta = get_ds_meta("PickPlaceCounterToCabinet")  # horizon, etc.
```

### HDF5 Dataset Format

```
dataset.hdf5
├── data/
│   ├── demo_0/
│   │   ├── states         # (T, state_dim) MuJoCo simulation state
│   │   ├── actions        # (T, action_dim) action vectors
│   │   ├── obs/           # Observations dict
│   │   │   ├── robot0_agentview_left_image   # (T, H, W, 3)
│   │   │   ├── robot0_eye_in_hand_image      # (T, H, W, 3)
│   │   │   ├── robot0_eef_pos                # (T, 3)
│   │   │   └── ...
│   │   └── ep_meta        # JSON: {"lang": "...", "object_cfgs": {...}}
│   ├── demo_1/
│   └── ...
└── env_args               # JSON: env creation kwargs
```

### Data Splits

| Split | Scenes | Purpose |
|-------|--------|---------|
| `pretrain` | Train layouts/styles (11-60) | Training data |
| `target` | Test layouts/styles (1-10) | Evaluation demos |

| Source | Volume | Method |
|--------|--------|--------|
| `human` | 50 demos/task | SpaceMouse teleoperation |
| `mg` (MimicGen) | 3,000 demos/task (atomic) | Automated trajectory generation |

## Gym Wrapper

```python
from robocasa.wrappers.gym_wrapper import RoboCasaGymEnv

env = RoboCasaGymEnv(
    env_name="PickPlaceCounterToCabinet",
    camera_names=["robot0_agentview_left", "robot0_agentview_right", "robot0_eye_in_hand"],
    camera_widths=128,
    camera_heights=128,
    split="test",
)

obs, info = env.reset()
obs, reward, terminated, truncated, info = env.step(action)
```

## Supported Robots

| Robot | Type | Notes |
|-------|------|-------|
| `PandaOmron` | Single-arm mobile manipulator | Default; Panda arm on Omron base |
| `GR1FloatingBody` | Humanoid | Fourier GR1 |
| `G1FloatingBody` | Humanoid | Unitree G1 |
| `GoogleRobot` | Single-arm mobile | |
| Various ALOHA configs | Bimanual | Via robosuite |

## Predefined Evaluation Scenes

```python
from robocasa.utils.env_utils import KITCHEN_SCENES_5X5, KITCHEN_SCENES_5X1

# 5×5 = 25 scenes for thorough eval
KITCHEN_SCENES_5X5  # layouts [11,15,18,40,50] × styles [14,28,34,46,58]

# 5×1 = 5 scenes for quick eval
KITCHEN_SCENES_5X1  # layouts [11,15,18,40,50] × style [34]
```

## Repo Structure

| Path | Purpose |
|------|---------|
| `robocasa/environments/kitchen/kitchen.py` | Base `Kitchen` class, `REGISTERED_KITCHEN_ENVS` |
| `robocasa/environments/kitchen/atomic/` | Atomic task definitions |
| `robocasa/environments/kitchen/composite/` | Composite task definitions (by category) |
| `robocasa/models/fixtures/` | `Fixture` base, `FixtureType` enum, all fixture implementations |
| `robocasa/models/objects/` | `ObjCat`, object registries, `sample_kitchen_object()` |
| `robocasa/models/scenes/` | `KitchenArena`, `LayoutType`/`StyleType`, YAML blueprints |
| `robocasa/models/assets/` | MJCF models, textures, object meshes |
| `robocasa/utils/env_utils.py` | `create_env()`, scene constants |
| `robocasa/utils/object_utils.py` | Success check helpers (`obj_inside_of`, etc.) |
| `robocasa/utils/dataset_registry.py` | Task → dataset path mapping |
| `robocasa/utils/robomimic/` | Robomimic integration (dataset utils, env wrapper) |
| `robocasa/wrappers/gym_wrapper.py` | `RoboCasaGymEnv` Gymnasium wrapper |
| `robocasa/scripts/collect_demos.py` | Human teleoperation data collection |
| `robocasa/scripts/download_kitchen_assets.py` | Asset downloader |
| `robocasa/scripts/download_datasets.py` | Dataset downloader |
| `robocasa/scripts/dataset_scripts/` | Playback, conversion, info utilities |
| `robocasa/demos/` | Demo scripts (tasks, scenes, teleop, objects) |
| `robocasa/macros.py` | Global config (dataset path, device IDs) |

## Tips & Gotchas

- **Run `download_kitchen_assets.py` before anything else** — environments won't render without textures and fixture models.
- **Run `setup_macros.py`** to set `DATASET_BASE_PATH` in `macros_private.py` — needed for dataset downloading/loading.
- **Layout/style IDs start at 1**, not 0. Use negative IDs for groups (-1=test, -2=train, -3=all).
- **`obj_instance_split="test"`** holds out specific object instances for generalization evaluation — always use this for eval.
- **Composite tasks often need `"aigen"` in `obj_registries`** — some composite tasks auto-add it, but if objects fail to load, add it manually.
- **Control frequency is 20 Hz** (not 50 Hz like ALOHA). Real robot controller runs at 15 Hz.
- **The `render_camera` arg** controls the on-screen view; `camera_names` controls observation cameras — they're independent.
- **MimicGen data only exists for atomic tasks** — composite tasks have human demos only.
- **Auto-registered tasks**: defining a class that inherits from `Kitchen` automatically registers it via `KitchenEnvMeta`. No manual registration needed.
- **robosuite is the underlying framework** — `robosuite.make()` is the canonical env creation path. RoboCasa extends it with kitchen-specific environments.
- **For policy training**, use the robomimic integration or the Gym wrapper — don't train directly against the raw robosuite env API.
- **Generative textures (`"100p"`)** add visual diversity but slow down scene loading. Disable for debugging.
