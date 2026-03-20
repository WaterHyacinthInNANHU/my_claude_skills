# Any3D-VLA -- Examples & Recipes

## 1. Setup from Scratch

```bash
# Create environment
conda create -n any3dvla_env python=3.12 -y
conda activate any3dvla_env

# Install dependencies (CUDA 11.8)
pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cu118

# Install core package
pip install -e src/vla_network

# Install Concerto 3D encoder
git clone https://github.com/Pointcept/Concerto.git
cd Concerto && pip install -e . && cd ..

# Download checkpoint
# Option A: Use huggingface-cli
huggingface-cli download XianzheFan/Any3D-VLA --local-dir storage/ckpt/exp/grit-Concerto-mono-dinosiglip-16-128-40000/checkpoint-340000/

# Option B: Direct download
# Get model.safetensors from https://huggingface.co/XianzheFan/Any3D-VLA
```

## 2. Run Inference Server

```bash
# Basic server on port 6666
bash serve_mono.sh

# With torch.compile for ~50% speedup (3min warmup)
bash serve_mono.sh --compile
```

### Client code (ZMQ)

```python
import zmq
import pickle
import numpy as np

context = zmq.Context()
socket = context.socket(zmq.DEALER)
socket.connect("tcp://localhost:6666")

sample = {
    'text': 'pick up elephant',
    'image_array': [img_front],           # (256, 256, 3) uint8
    'image_wrist_array': [img_wrist],     # (256, 256, 3) uint8
    'depth_array': [depth_front],         # (256, 256, 1) float32
    'depth_wrist_array': [depth_wrist],   # (256, 256, 1) float32
    'proprio_array': [proprio] * 4,       # list of 4 x (7,) float32
    'traj_metadata': None,
    'env_id': 1,
    'compressed': False,
}

socket.send_multipart([b'', pickle.dumps(sample)])
_, response = socket.recv_multipart()
result = pickle.loads(response)
# result['result']: list of interpolated delta actions
# result['debug']['pose']: goal pose (if CoT mode)
# result['debug']['bbox']: bounding boxes (if CoT mode)
```

## 3. Python API (Direct Inference)

```python
from vla_network.model.vla import VLAAgent
import numpy as np

# Load
agent = VLAAgent(
    path="path/to/model.safetensors",
    device="cuda:0",
    compile=False,  # set True for faster repeated inference
)
agent.preprocessor.config.robot_rep = "identity"

# Single sample
sample = {
    'text': 'pick up toy car',
    'image_array': [front_img],           # (256,256,3) uint8
    'image_wrist_array': [wrist_img],     # (256,256,3) uint8
    'depth_array': [front_depth],         # (256,256,1) float32
    'depth_wrist_array': [wrist_depth],   # (256,256,1) float32
    'proprio_array': [proprio_t3, proprio_t0],  # 2 timesteps of (7,) float32
    'traj_metadata': None,
    'env_id': 0,
}

results = agent([sample])
action = results[0]['action']  # (action_len, 7) before interpolation
# After batch_process interpolation: (action_len * dt_steps, 7)
# Columns: [delta_x, delta_y, delta_z, delta_roll, delta_pitch, delta_yaw, gripper]
```

## 4. Sending Compressed Images (for network efficiency)

```python
import io
from PIL import Image

def compress_image(img_array):
    img = Image.fromarray(img_array)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def compress_depth_f32_rgba(depth_array):
    """Encode float32 depth as RGBA PNG (lossless)."""
    h, w = depth_array.shape[:2]
    depth_flat = depth_array.reshape(h, w).astype('<f4')
    rgba = np.frombuffer(depth_flat.tobytes(), dtype=np.uint8).reshape(h, w, 4)
    img = Image.fromarray(rgba, mode='RGBA')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

sample = {
    'text': 'pick up elephant',
    'image_array': [compress_image(front_img)],
    'image_wrist_array': [compress_image(wrist_img)],
    'depth_array': [compress_depth_f32_rgba(front_depth)],
    'depth_wrist_array': [compress_depth_f32_rgba(wrist_depth)],
    'proprio_array': [proprio] * 4,
    'traj_metadata': None,
    'env_id': 1,
    'compressed': True,  # tells server to decompress
}
```

## 5. Understanding the Model Pipeline

### Forward pass (training)

```
1. Images -> backbone_2d (DINOv2 + SigLIP + Concerto fusion) -> proj_feat_2d
2. Tokenize instruction -> embed -> insert proj_feat_2d after BOS -> prefix_embeds
3. [cot_flow_matching mode]:
   a. prefix_embeds + CoT labels -> LLM -> CoT loss (cross-entropy)
   b. action -> add noise (flow matching) -> action_time_embeds
   c. proprio -> proprio_embeds
   d. [proprio_embeds, action_time_embeds] -> Action Expert (with LLM KV cache) -> hidden_states
   e. hidden_states -> action_out_proj -> v_t prediction
   f. MSE loss between v_t and true velocity u_t
   g. Total loss = CoT loss + flow matching loss
```

### Forward pass (inference)

```
1. Images -> backbone_2d -> proj_feat_2d -> LLM prefix encoding (KV cache)
2. Autoregressive generation of CoT tokens (bbox, goal)
3. Sample noise of shape (1, action_len, action_dim)
4. Euler integration over 10 steps:
   - embed [proprio, noisy_action + time] -> Action Expert (with LLM KV cache)
   - predict velocity v_t -> update x_t
5. Final x_t = denoised action
6. Inverse-normalize action -> delta actions
7. Interpolate by dt_steps -> final action sequence
```

## 6. Key Data Formats

### Input images
- Shape: `(256, 256, 3)`, dtype `uint8`, RGB
- Two views: front camera + wrist camera
- Transformed to `(224, 224)` by model's image_transform (separate transforms for DINOv2 and SigLIP)

### Depth maps
- Shape: `(256, 256, 1)`, dtype `float32`
- Metric depth in meters
- If not available, model estimates via DepthAnything3

### Proprioception
- Shape: `(7,)`, dtype `float32`
- Format: `[x, y, z, roll, pitch, yaw, gripper]`
- Multiple history steps (typically 2-4)

### Actions (output)
- Shape: `(action_len, 7)`, dtype `float32`
- Format: `[delta_x, delta_y, delta_z, delta_roll, delta_pitch, delta_yaw, gripper_delta]`
- Gripper: discretized to {-1, 0, 1} at inference
- Interpolated by `dt_steps` for smooth execution
