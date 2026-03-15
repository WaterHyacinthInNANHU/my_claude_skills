# BPP Examples & Reproduction Recipes

## Scenario 1: Add VLM Keyframe Detection to an Existing Policy

If you have a working diffusion policy (e.g., from Diffusion Policy or ACT codebase) and want to add BPP-style keyframe conditioning:

### Step 1: Set up VLM keyframe detector

```python
import google.generativeai as genai
import time

class BPPKeypointDetector:
    """VLM-based keyframe detector following BPP (Sobol Mark et al., 2026)."""

    def __init__(self, task_prompt: str, query_hz: float = 1.0, latency_delta: float = 3.0):
        self.model = genai.GenerativeModel("gemini-3-pro")
        self.task_prompt = task_prompt
        self.query_interval = 1.0 / query_hz
        self.latency_delta = latency_delta
        self.prev_response = False
        self.keyframes = []  # list of (timestamp, observation)
        self.last_query_time = 0

    def update(self, wrist_image, obs_dict, timestamp):
        """Call at each control step. Returns latency-masked keyframe observations."""
        # Only query VLM at specified frequency
        if timestamp - self.last_query_time >= self.query_interval:
            response = self._query_vlm(wrist_image)
            # Rising-edge detection
            if response and not self.prev_response:
                self.keyframes.append((timestamp, obs_dict.copy()))
            self.prev_response = response
            self.last_query_time = timestamp

        # Return latency-masked keyframes
        return [obs for t, obs in self.keyframes if t <= timestamp - self.latency_delta]

    def _query_vlm(self, image):
        prompt = (
            f"{self.task_prompt}\n"
            "Answer only YES or NO."
        )
        response = self.model.generate_content([prompt, image])
        return "YES" in response.text.upper()

    def reset(self):
        self.prev_response = False
        self.keyframes = []
        self.last_query_time = 0
```

### Step 2: Modify policy input to include keyframes

```python
import torch

def build_bpp_observation(current_obs, keyframe_obs_list, max_keyframes=5):
    """
    Combine current observation with keyframe observations for policy input.

    Args:
        current_obs: dict with 'images' (N_cams, C, H, W) and 'state' (D,)
        keyframe_obs_list: list of dicts, each same format as current_obs
        max_keyframes: max number of keyframes to include

    Returns:
        Combined observation dict for the policy
    """
    # Take most recent keyframes up to max
    recent_keyframes = keyframe_obs_list[-max_keyframes:]

    # Stack images: current + keyframes along time dimension
    all_images = [current_obs['images']]  # (N_cams, C, H, W)
    for kf in recent_keyframes:
        all_images.append(kf['images'])

    # Pad if fewer keyframes than max
    while len(all_images) < max_keyframes + 1:
        all_images.append(torch.zeros_like(current_obs['images']))

    return {
        'images': torch.stack(all_images, dim=0),  # (1+K, N_cams, C, H, W)
        'state': current_obs['state'],
        'num_keyframes': len(recent_keyframes),
    }
```

### Step 3: Training with latency-masked keyframes

```python
def prepare_training_batch(demo, keyframe_timestamps, delta=3.0):
    """
    Prepare a training example with latency-masked keyframes.

    During training, exclude keyframes newer than delta seconds
    to simulate real-world VLM detection latency.
    """
    batch = []
    for t in range(len(demo['actions'])):
        current_obs = demo['observations'][t]

        # Latency-masked keyframes (only those older than delta)
        masked_kf_indices = [
            k for k in keyframe_timestamps
            if k <= t - int(delta * demo['fps'])
        ]
        keyframe_obs = [demo['observations'][k] for k in masked_kf_indices]

        obs = build_bpp_observation(current_obs, keyframe_obs)
        obs['actions'] = demo['actions'][t:t+50]  # 50-step action chunk

        batch.append(obs)
    return batch
```

## Scenario 2: Design VLM Prompts for a New Task

BPP requires a task-specific VLM prompt that detects behaviorally salient state transitions. Follow these guidelines:

### Prompt Design Rules

1. **Focus on transitions**, not static states: "has **just** picked up" not "is holding"
2. **Binary output**: Always ask for YES/NO
3. **Reference previous state**: "it wasn't grabbing it in the previous observation"
4. **Be specific about visual cues**: "gripper is completely grabbing" not "gripper has object"

### Template

```
Decide whether the robot has just [COMPLETED ACTION].
If [VISUAL EVIDENCE OF COMPLETION] and [VISUAL EVIDENCE IT WASN'T TRUE BEFORE],
then answer YES. Otherwise answer NO.
```

### Examples for Common Manipulation Primitives

| Primitive | Prompt |
|-----------|--------|
| Pick | "Decide whether the robot has just picked up [OBJECT]. If the gripper is closed around [OBJECT] and it was open before, answer YES." |
| Place | "Decide whether the robot has just placed [OBJECT] on [SURFACE]. If [OBJECT] is resting on [SURFACE] and the gripper is open, and the gripper was closed before, answer YES." |
| Open | "Decide whether [CONTAINER] has just been opened. If [CONTAINER] is open now and was closed before, answer YES." |
| Pour | "Decide whether the robot has just poured [SUBSTANCE] into [CONTAINER]. If [SUBSTANCE] is visible in [CONTAINER] and the source container is tilted, answer YES." |

## Scenario 3: Evaluate BPP on a New Task

### Evaluation Protocol (following the paper)

```python
def evaluate_bpp(policy, keyframe_detector, env, num_episodes=20):
    """
    Evaluate a BPP policy.

    Key: keyframe detector runs at 1 Hz independently of 50 Hz control.
    """
    successes = 0

    for ep in range(num_episodes):
        obs = env.reset()
        keyframe_detector.reset()
        done = False
        t = 0.0
        dt = 1.0 / 50  # 50 Hz control

        while not done:
            # Update keyframe detector (internally rate-limited to 1 Hz)
            keyframe_obs = keyframe_detector.update(
                obs['wrist_image'], obs, timestamp=t
            )

            # Build policy input
            policy_input = build_bpp_observation(obs, keyframe_obs)

            # Get action chunk (50 steps)
            actions = policy.predict(policy_input)

            # Execute action chunk (or partial)
            for action in actions:
                obs, reward, done, info = env.step(action)
                t += dt
                if done:
                    break

            # Re-query keyframes between chunks
            keyframe_obs = keyframe_detector.update(
                obs['wrist_image'], obs, timestamp=t
            )

        if info.get('success', False):
            successes += 1

    return successes / num_episodes
```

### Baselines to Compare Against

| Baseline | Description | Implementation |
|----------|-------------|----------------|
| Current-only | Policy sees only current observation | Remove all history inputs |
| Naive history | Policy sees last N frames uniformly sampled | Replace keyframes with uniform temporal sampling |
| PTP (Past Token Prediction) | Auxiliary loss predicting past observations | See [PTP paper](https://arxiv.org/abs/2404.04867) |
| Oracle keyframes | Ground-truth keyframes from human annotation | Replace VLM detector with manual labels |

## Scenario 4: Architecture Implementation

### Minimal Diffusion Transformer with Keyframe Conditioning

```python
import torch
import torch.nn as nn
from torchvision.models import resnet34

class BPPPolicy(nn.Module):
    """
    Simplified BPP policy architecture.
    ResNet34 encoder + Transformer decoder + DDPM action head.
    """

    def __init__(
        self,
        n_cameras=4,
        state_dim=14,       # ALOHA 2 joint dims
        action_dim=14,
        action_horizon=50,
        max_keyframes=5,
        d_model=512,
        n_heads=8,
        n_layers=7,
        dropout=0.1,
    ):
        super().__init__()
        self.action_horizon = action_horizon
        self.max_keyframes = max_keyframes

        # Separate ResNet34 per camera (shared across timesteps)
        self.image_encoders = nn.ModuleList([
            resnet34(pretrained=True) for _ in range(n_cameras)
        ])
        # Remove classification heads, get feature dim
        for enc in self.image_encoders:
            enc.fc = nn.Identity()
        img_feat_dim = 512  # ResNet34 output

        # Project image features to transformer dim
        self.img_proj = nn.Linear(img_feat_dim, d_model)
        self.state_proj = nn.Linear(state_dim, d_model)

        # Transformer decoder
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=d_model, nhead=n_heads, dropout=dropout, batch_first=True
        )
        self.transformer = nn.TransformerDecoder(decoder_layer, num_layers=n_layers)

        # Diffusion timestep embedding
        self.time_embed = nn.Sequential(
            nn.Linear(1, d_model),
            nn.SiLU(),
            nn.Linear(d_model, d_model),
        )

        # Action prediction head
        self.action_head = nn.Linear(d_model, action_dim)

        # Learnable action tokens
        self.action_tokens = nn.Parameter(torch.randn(action_horizon, d_model))

    def encode_obs(self, images, state):
        """
        Encode a single timestep observation.

        Args:
            images: (B, N_cams, C, H, W)
            state: (B, state_dim)
        Returns:
            tokens: (B, N_cams + 1, d_model)
        """
        cam_tokens = []
        for i, enc in enumerate(self.image_encoders):
            feat = enc(images[:, i])  # (B, 512)
            cam_tokens.append(self.img_proj(feat))  # (B, d_model)

        state_token = self.state_proj(state)  # (B, d_model)
        tokens = torch.stack(cam_tokens + [state_token], dim=1)  # (B, N+1, d_model)
        return tokens

    def forward(self, current_obs, keyframe_obs, diffusion_t, noisy_actions):
        """
        Args:
            current_obs: dict with 'images' (B, N_cams, C, H, W), 'state' (B, D)
            keyframe_obs: list of dicts, each same format (variable length)
            diffusion_t: (B, 1) diffusion timestep
            noisy_actions: (B, action_horizon, action_dim)
        """
        # Encode current observation
        context = self.encode_obs(current_obs['images'], current_obs['state'])

        # Encode and concatenate keyframe observations
        for kf in keyframe_obs:
            kf_tokens = self.encode_obs(kf['images'], kf['state'])
            context = torch.cat([context, kf_tokens], dim=1)

        # Prepare action query tokens with time embedding
        time_emb = self.time_embed(diffusion_t)  # (B, d_model)
        action_queries = self.action_tokens.unsqueeze(0).expand(
            noisy_actions.shape[0], -1, -1
        ) + time_emb.unsqueeze(1)

        # Transformer decode
        decoded = self.transformer(action_queries, context)  # (B, H, d_model)

        # Predict noise
        predicted_noise = self.action_head(decoded)  # (B, H, action_dim)
        return predicted_noise
```

**Note**: This is a simplified reference implementation. The actual BPP paper may use additional architectural details not described in the paper. Key elements preserved:
- Separate ResNet34 per camera, shared across timesteps
- 7-layer transformer decoder (512 dim, 8 heads, 0.1 dropout)
- DDPM with 50-step action chunks
- Variable number of keyframe context tokens
