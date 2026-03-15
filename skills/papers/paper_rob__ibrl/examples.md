# IBRL -- Examples & Recipes

## Setup

### 1. Install MuJoCo 2.1

```bash
wget https://mujoco.org/download/mujoco210-linux-x86_64.tar.gz
mkdir -p ~/.mujoco
tar -xzf mujoco210-linux-x86_64.tar.gz -C ~/.mujoco/
# Result: ~/.mujoco/mujoco210/
```

### 2. Clone & Create Environment

```bash
git clone --recursive https://github.com/hengyuan-hu/ibrl.git
cd ibrl
conda create -n ibrl python=3.9
conda activate ibrl
source set_env.sh  # MUST run once per shell
```

### 3. Install Dependencies

```bash
# PyTorch (adjust CUDA version as needed)
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121

# Other packages
pip install -r requirements.txt

# Compile C++ replay buffer
cd common_utils && make && cd ..
```

If you hit `GLIBCXX_3.4.30 not found`:
```bash
CONDA_LIB=$(python -c "import sys; print(sys.prefix)")/lib
ln -sf /lib/x86_64-linux-gnu/libstdc++.so.6 $CONDA_LIB/libstdc++.so
ln -sf /lib/x86_64-linux-gnu/libstdc++.so.6 $CONDA_LIB/libstdc++.so.6
```

### 4. Download Data & Pretrained Models

Download from [Google Drive](https://drive.google.com/file/d/1F2yH84Iqv0qRPmfH8o-kSzgtfaoqMzWE/view?usp=sharing) and extract into `release/`:
```
release/
├── cfgs/                    # Already in repo
├── data/
│   ├── robomimic/
│   │   ├── can/processed_data96.hdf5
│   │   └── square/processed_data96.hdf5
│   └── metaworld/
│       ├── Assembly_frame_stack_1_96x96_end_on_success/dataset.hdf5
│       ├── BoxClose_frame_stack_1_96x96_end_on_success/dataset.hdf5
│       ├── CoffeePush_frame_stack_1_96x96_end_on_success/dataset.hdf5
│       └── StickPull_frame_stack_1_96x96_end_on_success/dataset.hdf5
└── model/
    ├── robomimic/
    │   ├── can/model0.pt
    │   ├── can_pretrain/model0.pt
    │   ├── square/model0.pt
    │   └── square_pretrain/model0.pt
    └── metaworld/
        └── path{TaskName}_num_data3_num_epoch2_seed1/model1.pt
```

---

## Scenario 1: IBRL on PickPlaceCan (pixel)

The core use case. Uses ViT encoder, prop_stack=3, IBRL action selection.

```bash
source set_env.sh

python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_ibrl.yaml \
  --save_dir exp/can_ibrl \
  --use_wb 0
```

Config highlights from `can_ibrl.yaml`:
```yaml
task_name: "PickPlaceCan"
rl_camera: "robot0_eye_in_hand"
prop_stack: 3
bc_policy: "release/model/robomimic/can/model0.pt"
preload_num_data: 10       # preload 10 demo episodes
num_warm_up_episode: 40    # BC-guided warm-up
num_train_step: 200000
replay_buffer_size: 1000
q_agent:
  act_method: "ibrl"       # Q-based RL/BC selection
  use_prop: 1
  vit:
    embed_style: "embed2"
    depth: 1
  actor:
    dropout: 0.5           # important for IBRL
    hidden_dim: 1024
    feature_dim: 128
  critic:
    spatial_emb: 1024
    hidden_dim: 1024
```

---

## Scenario 2: IBRL on NutAssemblySquare (pixel)

Harder task, same method:

```bash
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/square_ibrl.yaml \
  --save_dir exp/square_ibrl \
  --use_wb 0
```

---

## Scenario 3: RLPD Baseline (demo-augmented replay)

Mix 50% demo data with 50% online data in each batch. No BC policy for action selection.

```bash
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_rlpd.yaml \
  --save_dir exp/can_rlpd \
  --use_wb 0
```

Key difference from IBRL config:
```yaml
q_agent:
  act_method: "rl"        # pure RL actions, no IBRL selection
mix_rl_rate: 0.5           # 50% RL data, 50% demo data in each batch
```

---

## Scenario 4: RFT Baseline (Regularized Fine-Tuning)

Two-step process: pretrain RL actor+encoder with BC loss, then fine-tune with RL + BC regularization.

### Step 1: Pretrain

```bash
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_rft.yaml \
  --pretrain_only 1 \
  --pretrain_num_epoch 5 \
  --load_pretrained_agent None \
  --save_dir exp/can_pretrain \
  --use_wb 0
```

### Step 2: RL fine-tune with BC loss

```bash
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_rft.yaml \
  --load_pretrained_agent exp/can_pretrain/model0.pt \
  --save_dir exp/can_rft \
  --use_wb 0
```

RFT-specific config:
```yaml
q_agent:
  act_method: "rl"
  bc_loss_coef: 0.1        # weight for BC regularization
  bc_loss_dynamic: 1        # dynamically scale BC loss via Q-value comparison
add_bc_loss: 1
```

---

## Scenario 5: State-Based IBRL

Uses `FcActor` + `MultiFcQ` (10 Q-networks, RED-Q style). No image encoder.

```bash
# IBRL (state)
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_state_ibrl.yaml \
  --save_dir exp/can_state_ibrl \
  --use_wb 0

# RLPD (state)
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_state_rlpd.yaml \
  --save_dir exp/can_state_rlpd \
  --use_wb 0

# RFT (state) -- pretrain + finetune in one command
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_state_rft.yaml \
  --save_dir exp/can_state_rft \
  --use_wb 0
```

---

## Scenario 6: Meta-World Tasks

Meta-World uses DrQ encoder (4-layer conv), 96x96 images, episode_length=100.

```bash
# IBRL on Assembly
python mw_main/train_rl_mw.py \
  --config_path release/cfgs/metaworld/ibrl_basic.yaml \
  --bc_policy assembly \
  --save_dir exp/mw_assembly_ibrl \
  --use_wb 0

# Available tasks: assembly, boxclose, coffeepush, stickpull
# The --bc_policy name maps to BC_POLICIES dict in mw_main/train_rl_mw.py

# RLPD baseline
python mw_main/train_rl_mw.py \
  --config_path release/cfgs/metaworld/rlpd.yaml \
  --bc_policy assembly \
  --save_dir exp/mw_rlpd \
  --use_wb 0

# RFT baseline (pretrain + finetune in one step)
python mw_main/train_rl_mw.py \
  --config_path release/cfgs/metaworld/rft.yaml \
  --bc_policy assembly \
  --save_dir exp/mw_rft \
  --use_wb 0
```

---

## Scenario 7: Train BC Policy from Scratch

### Pixel-based BC (Robomimic)

```bash
python train_bc.py \
  --config_path release/cfgs/robomimic_bc/can.yaml \
  --save_dir exp/bc_can \
  --use_wb 0

# Square
python train_bc.py \
  --config_path release/cfgs/robomimic_bc/square.yaml \
  --save_dir exp/bc_square \
  --use_wb 0
```

### State-based BC

```bash
python train_bc.py \
  --config_path release/cfgs/robomimic_bc/can_state.yaml \
  --save_dir exp/bc_can_state \
  --use_wb 0
```

### Meta-World BC

```bash
python mw_main/train_bc_mw.py \
  --dataset.path Assembly \
  --save_dir exp/bc_mw_assembly
```

---

## Scenario 8: Custom Config Overrides

Override any nested config field via pyrallis CLI:

```bash
# Increase training steps, change learning rate, use soft IBRL
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_ibrl.yaml \
  --num_train_step 500000 \
  --batch_size 512 \
  --q_agent.lr 3e-4 \
  --q_agent.act_method ibrl_soft \
  --q_agent.soft_ibrl_beta 5.0 \
  --q_agent.actor.dropout 0.3 \
  --q_agent.critic.hidden_dim 2048 \
  --save_dir exp/custom_run \
  --use_wb 0

# Switch encoder to ResNet
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_ibrl.yaml \
  --q_agent.enc_type resnet \
  --save_dir exp/can_resnet \
  --use_wb 0

# Use multi-camera
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_ibrl.yaml \
  --rl_camera "robot0_eye_in_hand+agentview" \
  --save_dir exp/can_multicam \
  --use_wb 0
```

---

## Scenario 9: Load & Evaluate a Trained Model

```python
import torch
import train_rl
from evaluate import run_eval

# Load RL agent (with BC policy if configured)
agent, eval_env, eval_env_params = train_rl.load_model("exp/can_ibrl/model0.pt", "cuda")

# Run evaluation
scores = run_eval(
    env_params=eval_env_params,
    agent=agent,
    num_game=50,
    seed=0,
    record_dir=None,
    verbose=True,
)
print(f"Success rate: {sum(scores) / len(scores):.2%}")
```

---

## SLURM Template

```bash
#!/bin/bash
#SBATCH --job-name=ibrl_can
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=12
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=logs/ibrl_%j.out
#SBATCH --error=logs/ibrl_%j.err

module load cuda/12.1  # adjust to your cluster

cd /path/to/ibrl
conda activate ibrl
source set_env.sh

export MUJOCO_GL=egl   # headless rendering

TASK=${1:-can}
METHOD=${2:-ibrl}

python train_rl.py \
  --config_path release/cfgs/robomimic_rl/${TASK}_${METHOD}.yaml \
  --save_dir exp/${TASK}_${METHOD}_${SLURM_JOB_ID} \
  --use_wb 1 \
  --mp_eval 1
```

Usage:
```bash
sbatch run_ibrl.sh can ibrl
sbatch run_ibrl.sh square ibrl
sbatch run_ibrl.sh can rlpd
```

---

## Tips

- **Always `source set_env.sh`** before running anything. Without it, imports fail and parallel eval is slow.
- **BC policy quality**: IBRL is not sensitive to exact BC performance; a mediocre BC still helps exploration significantly.
- **Actor dropout**: 0.5 is the default for IBRL pixel experiments; setting it to 0 degrades performance.
- **stddev_max**: released configs use `0.1` (minimal exploration noise); the linear schedule from `stddev_max` to `stddev_min` over `stddev_step` environment steps controls noise decay.
- **Replay buffer size**: measured in episodes (not transitions). Default 500-1000 episodes.
- **Preload data**: `preload_num_data: 10` loads 10 demo episodes into the replay buffer before training starts.
- **`assert False` at termination**: both training scripts intentionally crash at the end to signal completion; this is expected behavior.
- **EGL rendering**: set `MUJOCO_GL=egl` for headless GPU rendering on clusters (done automatically in the training scripts' `__main__` blocks).
- **Multi-camera**: specify cameras with `+` separator: `--rl_camera "robot0_eye_in_hand+agentview"`. The BC policy's cameras are loaded from its saved config and merged automatically.
- **WandB**: configure with `--use_wb 1`, set `WANDB_API_KEY` env var. Project/run/group names configurable via `--wb_exp`, `--wb_run`, `--wb_group`.
