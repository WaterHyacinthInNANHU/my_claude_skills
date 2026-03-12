# IBRL — Usage Examples & Reproduction Recipes

## Setup

### 1. Install MuJoCo 2.1

```bash
# Download and extract MuJoCo 2.1
wget https://mujoco.org/download/mujoco210-linux-x86_64.tar.gz
mkdir -p ~/.mujoco
tar -xzf mujoco210-linux-x86_64.tar.gz -C ~/.mujoco/
# Result: ~/.mujoco/mujoco210/
```

### 2. Create Environment

```bash
git clone --recursive https://github.com/hengyuan-hu/ibrl.git
cd ibrl
conda create -n ibrl python=3.9
conda activate ibrl
source set_env.sh  # Sets MUJOCO_PY_MUJOCO_PATH and PYTHONPATH
```

### 3. Install Dependencies

```bash
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
cd common_utils && make && cd ..  # Compile C++ replay buffer
```

### 4. Download Data & Pretrained Models

Download from [Google Drive](https://drive.google.com/file/d/1F2yH84Iqv0qRPmfH8o-kSzgtfaoqMzWE/view?usp=sharing) and extract into `release/`.

Expected structure:
```
release/
├── data/robomimic/{can,square}/processed_data96.hdf5
└── model/robomimic/{can,square}/model0.pt
```

---

## Scenario 1: Train IBRL on PickPlaceCan (Pixel)

```bash
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_ibrl.yaml \
  --save_dir exp/can_ibrl \
  --use_wb 0
```

Key config values in `can_ibrl.yaml`:
```yaml
task_name: "PickPlaceCan"
bc_policy: "release/model/robomimic/can/model0.pt"
preload_num_data: 10
preload_datapath: "release/data/robomimic/can/processed_data96.hdf5"
q_agent:
  act_method: "ibrl"
  enc_type: "vit"
  vit:
    embed_style: "embed2"
    depth: 1
  actor:
    dropout: 0.5
```

---

## Scenario 2: Train IBRL on PickPlaceSquare (Pixel)

```bash
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/square_ibrl.yaml \
  --save_dir exp/square_ibrl \
  --use_wb 0
```

---

## Scenario 3: Train State-Based IBRL

```bash
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_state_ibrl.yaml \
  --save_dir exp/can_state_ibrl \
  --use_wb 0
```

Uses `StateBcPolicy` + `FcActor` + `MultiFcQ` (10 Q-networks, RED-Q style).

---

## Scenario 4: Train Baselines for Comparison

### RLPD (demo-augmented replay)
```bash
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_rlpd.yaml \
  --save_dir exp/can_rlpd \
  --use_wb 0
```

### RFT (reward fine-tuning with BC loss)
```bash
# Step 1: Pretrain
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_rft.yaml \
  --pretrain_only 1 \
  --save_dir exp/can_pretrain \
  --use_wb 0

# Step 2: Fine-tune
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_rft.yaml \
  --load_pretrained_agent exp/can_pretrain/model0.pt \
  --save_dir exp/can_rft \
  --use_wb 0
```

---

## Scenario 5: Meta-World Tasks

```bash
# IBRL on Assembly
python mw_main/train_rl_mw.py \
  --config_path release/cfgs/metaworld/ibrl_basic.yaml \
  --bc_policy assembly \
  --save_dir exp/mw_assembly_ibrl \
  --use_wb 0

# RLPD on Assembly
python mw_main/train_rl_mw.py \
  --config_path release/cfgs/metaworld/rlpd.yaml \
  --bc_policy assembly \
  --save_dir exp/mw_assembly_rlpd \
  --use_wb 0
```

Available Meta-World tasks: `assembly`, `boxclose`, `coffeepush`, `stickpull`

---

## Scenario 6: Train BC Policy from Scratch

```bash
python train_bc.py \
  --task_name PickPlaceCan \
  --datapath release/data/robomimic/can/processed_data96.hdf5 \
  --save_dir exp/bc_can \
  --use_wb 0
```

---

## Scenario 7: Custom Config Overrides

Override any config field from CLI via pyrallis:

```bash
python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_ibrl.yaml \
  --num_train_step 500000 \
  --batch_size 512 \
  --q_agent.lr 3e-4 \
  --q_agent.soft_ibrl_beta 5.0 \
  --save_dir exp/custom \
  --use_wb 0
```

---

## SLURM Template

```bash
#!/bin/bash
#SBATCH --job-name=ibrl_can
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=logs/ibrl_can_%j.out

conda activate ibrl
cd /path/to/ibrl
source set_env.sh

python train_rl.py \
  --config_path release/cfgs/robomimic_rl/can_ibrl.yaml \
  --save_dir exp/can_ibrl_${SLURM_JOB_ID} \
  --use_wb 1
```

---

## Tips & Gotchas

- **MuJoCo lock files**: if training crashes, remove `~/.mujoco/mujoco210/bin/*.lock`
- **C++ build**: `common_utils` requires cmake and a C++ compiler; if `make` fails, check `gcc` version
- **Memory**: pixel-based training needs ~16GB GPU RAM with ViT encoder
- **Warm-up**: the 50-episode warm-up phase uses BC policy — ensure `bc_policy` path is correct
- **WandB**: disable with `--use_wb 0` for local runs; set `WANDB_API_KEY` for cloud logging
- **Evaluation**: runs 10 episodes every 5000 steps by default; use `--mp_eval 1` for parallel eval
