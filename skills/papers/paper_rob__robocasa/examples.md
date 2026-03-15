# RoboCasa Examples & Recipes

## Scenario 1: Quick Start — Run a Task with Rendering

```bash
# Install
git clone https://github.com/robocasa/robocasa.git && cd robocasa
pip install -e .
python robocasa/scripts/download_kitchen_assets.py

# Interactive demo with keyboard control
python robocasa/demos/demo_kitchen_scenes.py \
    --task PickPlaceCounterToCabinet \
    --layout 1 --style 1 \
    --device keyboard

# Teleop demo with SpaceMouse
python robocasa/demos/demo_teleop.py \
    --task PickPlaceCounterToCabinet \
    --device spacemouse
```

## Scenario 2: Create Environment for Policy Training

```python
import numpy as np
import robosuite
from robosuite.controllers import load_composite_controller_config

# Standard setup for BC/RL training
env = robosuite.make(
    env_name="PickPlaceCounterToCabinet",
    robots="PandaOmron",
    controller_configs=load_composite_controller_config(robot="PandaOmron"),
    has_renderer=False,
    has_offscreen_renderer=True,
    use_camera_obs=True,
    camera_names=["robot0_agentview_left", "robot0_agentview_right", "robot0_eye_in_hand"],
    camera_heights=128,
    camera_widths=128,
    control_freq=20,
    horizon=500,
    layout_ids=-2,                    # Train layouts only
    style_ids=-2,                     # Train styles only
    obj_instance_split="train",       # Train object instances
    generative_textures="100p",       # AI textures for diversity
    seed=42,
)

obs = env.reset()

# Get language instruction
ep_meta = env.get_ep_meta()
print(ep_meta["lang"])  # "Pick the apple from the counter and place it in the cabinet."

# Random policy loop
for _ in range(500):
    action = np.random.randn(12)  # 12-dim action for PandaOmron
    obs, reward, done, info = env.step(action)
    if done:
        break

print("Success:", env._check_success())
```

## Scenario 3: Use Gym Wrapper (for stable-baselines3, tianshou, etc.)

```python
from robocasa.wrappers.gym_wrapper import RoboCasaGymEnv

env = RoboCasaGymEnv(
    env_name="PickPlaceCounterToCabinet",
    camera_names=["robot0_agentview_left", "robot0_eye_in_hand"],
    camera_widths=128,
    camera_heights=128,
    split="pretrain",
    enable_render=False,
)

obs, info = env.reset()
print("Obs space:", env.observation_space)
print("Act space:", env.action_space)

# Standard gym loop
for _ in range(100):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()
```

## Scenario 4: Download and Playback Demonstration Data

```bash
# Set dataset base path first
python robocasa/scripts/setup_macros.py

# Download datasets for a task
python robocasa/scripts/download_datasets.py --tasks PickPlaceCounterToCabinet

# Playback with video export
python robocasa/scripts/dataset_scripts/playback_dataset.py \
    --dataset /path/to/dataset.hdf5 \
    --render \
    --render-image-names robot0_agentview_center \
    --video-path /tmp/playback.mp4 \
    --n 5
```

```python
# Programmatic playback
from robocasa.scripts.dataset_scripts.playback_dataset import playback_dataset

playback_dataset(
    dataset="/path/to/PickPlaceCounterToCabinet.hdf5",
    use_actions=True,             # Open-loop action replay
    render=True,
    render_image_names=["robot0_agentview_center"],
    camera_height=512,
    camera_width=768,
    video_path="/tmp/demo_video.mp4",
    video_skip=5,                  # Record every 5th frame
    n=3,                           # Playback 3 episodes
)
```

## Scenario 5: Load Dataset for Policy Training (with robomimic)

```python
import h5py
import numpy as np

dataset_path = "/path/to/PickPlaceCounterToCabinet.hdf5"

with h5py.File(dataset_path, "r") as f:
    # List demos
    demos = list(f["data"].keys())
    print(f"Found {len(demos)} demonstrations")

    # Load a single demo
    demo = f["data/demo_0"]
    actions = demo["actions"][:]                              # (T, 12)
    states = demo["obs/robot0_eef_pos"][:]                   # (T, 3)
    images = demo["obs/robot0_agentview_left_image"][:]      # (T, H, W, 3)

    # Get language instruction
    import json
    ep_meta = json.loads(demo.attrs["ep_meta"])
    print("Task:", ep_meta["lang"])

    # Get env creation args for replay
    env_args = json.loads(f["data"].attrs["env_args"])
```

## Scenario 6: Iterate Over All 365 Tasks

```python
from robocasa.environments.kitchen.kitchen import REGISTERED_KITCHEN_ENVS
from robocasa.utils.dataset_registry import ATOMIC_TASK_DATASETS, COMPOSITE_TASK_DATASETS

# List all registered task names
print(f"Total tasks: {len(REGISTERED_KITCHEN_ENVS)}")
for task_name in sorted(REGISTERED_KITCHEN_ENVS.keys()):
    print(f"  {task_name}")

# Get dataset info for atomic tasks
for task, info in ATOMIC_TASK_DATASETS.items():
    print(f"{task}: horizon={info['horizon']}")
```

## Scenario 7: Evaluate a Policy Across Diverse Scenes

```python
import robosuite
from robosuite.controllers import load_composite_controller_config
from robocasa.utils.env_utils import KITCHEN_SCENES_5X5

def evaluate_policy(policy, task_name, num_episodes_per_scene=10):
    """Evaluate across 25 diverse kitchen scenes (5 layouts × 5 styles)."""
    results = []

    for layout_id, style_id in KITCHEN_SCENES_5X5:
        env = robosuite.make(
            env_name=task_name,
            robots="PandaOmron",
            controller_configs=load_composite_controller_config(robot="PandaOmron"),
            has_renderer=False,
            has_offscreen_renderer=True,
            use_camera_obs=True,
            camera_names=["robot0_agentview_left", "robot0_agentview_right", "robot0_eye_in_hand"],
            camera_heights=128,
            camera_widths=128,
            layout_ids=layout_id,
            style_ids=style_id,
            obj_instance_split="test",    # Held-out objects
        )

        successes = 0
        for ep in range(num_episodes_per_scene):
            obs = env.reset()
            for step in range(env.horizon):
                action = policy.predict(obs)
                obs, reward, done, info = env.step(action)
                if done:
                    break
            if env._check_success():
                successes += 1

        rate = successes / num_episodes_per_scene
        results.append((layout_id, style_id, rate))
        print(f"Layout {layout_id}, Style {style_id}: {rate:.0%}")

        env.close()

    avg = sum(r[2] for r in results) / len(results)
    print(f"\nOverall: {avg:.1%} across {len(results)} scenes")
    return results
```

## Scenario 8: Define a Custom Composite Task

```python
from robocasa.environments.kitchen.kitchen import *

class MakeBreakfast(Kitchen):
    """Pick eggs from fridge and place on counter near stove."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _setup_kitchen_references(self):
        super()._setup_kitchen_references()
        self.fridge = self.register_fixture_ref("fridge", dict(id=FixtureType.FRIDGE))
        self.stove = self.register_fixture_ref("stove", dict(id=FixtureType.STOVE))
        self.counter = self.register_fixture_ref(
            "counter", dict(id=FixtureType.COUNTER, ref=self.stove)
        )
        self.init_robot_base_ref = self.fridge

    def _setup_scene(self):
        super()._setup_scene()
        self.fridge.open_door(env=self)

    def _get_obj_cfgs(self):
        return [
            dict(
                name="egg",
                obj_groups="egg",
                graspable=True,
                placement=dict(
                    fixture=self.fridge,
                    size=(0.3, 0.25),
                    pos=(0, -1.0),
                    sample_region_kwargs=dict(z_range=(1, 1.5)),
                ),
            ),
        ]

    def get_ep_meta(self):
        ep_meta = super().get_ep_meta()
        ep_meta["lang"] = "Take the egg from the fridge and place it on the counter near the stove."
        return ep_meta

    def _check_success(self):
        import robocasa.utils.object_utils as OU
        return (OU.check_obj_fixture_contact(self, "egg", self.counter)
                and OU.gripper_obj_far(self))

# Auto-registered! Use directly:
# env = robosuite.make(env_name="MakeBreakfast", robots="PandaOmron", ...)
```

## Scenario 9: Convert Dataset to LeRobot Format

```bash
# Convert HDF5 to LeRobot format for use with pi0/openpi
python robocasa/scripts/dataset_scripts/convert_hdf5_lerobot.py \
    --dataset /path/to/dataset.hdf5 \
    --output /path/to/lerobot_dataset
```

## Scenario 10: Collect Human Demonstrations

```python
import robosuite
from robosuite.controllers import load_composite_controller_config
from robosuite.devices import SpaceMouse
from robocasa.scripts.collect_demos import collect_human_trajectory

env = robosuite.make(
    env_name="PickPlaceCounterToCabinet",
    robots="PandaOmron",
    controller_configs=load_composite_controller_config(robot="PandaOmron"),
    has_renderer=True,
    has_offscreen_renderer=True,
    use_camera_obs=True,
    camera_names=["robot0_agentview_center"],
    layout_ids=-2,           # Sample from train layouts
    style_ids=-2,
)

device = SpaceMouse(env=env, pos_sensitivity=4.0, rot_sensitivity=4.0)

# Collect one trajectory
ep_directory, discard = collect_human_trajectory(
    env=env,
    device=device,
    arm="right",
    env_configuration="single-arm-opposed",
    mirror_actions=True,
    render=True,
    max_fr=30,
)

if not discard:
    print(f"Saved demo to: {ep_directory}")
```
