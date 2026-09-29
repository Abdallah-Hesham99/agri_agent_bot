# agri_field_gym — Husky orchard navigation training (SB3 + Gymnasium)

## Task
Drive the Clearpath Husky around `farm_lite` on lidar to a randomly sampled
target each episode.

* **Obs (39,)**: 36 min-pooled lidar sectors + normalized distance + sin/cos heading error
* **Action**: `[v, w]`, v in [0, 1] m/s, w in [-1.5, 1.5] rad/s
* **Reward**: `3.0 * progress - 0.05*dt - 0.005*|w|`; **+20 arrival** (d < 0.7m);
  **-10 collision** (lidar < 0.4m, episode ends); 400-step timeout
* **Reset**: robot teleported to aisle-0 entrance, new target ≥8m away

## Prereqs (once)
```bash
pip install --break-system-packages gymnasium stable-baselines3
pip install --break-system-packages --index-url https://download.pytorch.org/whl/cpu torch
```

## Run
```bash
# terminal 1: sim + robot (includes /clock and /farm/pose_info TF bridges)
source ~/dev_ws/install/setup.bash
ros2 launch agri_agent_bot spawn_husky.launch.py
# terminal 2: train
source ~/dev_ws/install/setup.bash
python3 ~/dev_ws/src/agri_field_gym/agri_field_gym/train.py --timesteps 200000 --out runs/nav_ppo
# plots: runs/nav_ppo/plots.png (reward, length, eval reward, success rate)
# unit tests (no sim needed):
python3 ~/dev_ws/src/agri_field_gym/agri_field_gym/test_units.py
```
