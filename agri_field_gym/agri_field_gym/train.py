#!/usr/bin/env python3
"""Train PPO on the farm nav env. Run AFTER sim + spawn are up:
  terminal 1: ros2 launch agri_agent_bot spawn_husky.launch.py
  terminal 2: python3 train.py --timesteps 200000 --out runs/nav_ppo
Plots (avg reward, length, success) land next to the model.
"""
import argparse
import os

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.monitor import Monitor

from agri_field_gym.farm_nav_env import FarmNavEnv
from agri_field_gym.plot_results import plot_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timesteps", type=int, default=200000)
    ap.add_argument("--out", default="runs/nav_ppo")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(f"{a.out}/eval", exist_ok=True)

    env = Monitor(FarmNavEnv(seed=a.seed), f"{a.out}/monitor.csv")
    eval_env = Monitor(FarmNavEnv(seed=a.seed + 9999))
    eval_cb = EvalCallback(eval_env, best_model_save_path=f"{a.out}/eval",
                           log_path=f"{a.out}/eval", eval_freq=10000,
                           n_eval_episodes=5, deterministic=True)

    model = PPO("MlpPolicy", env, verbose=1, seed=a.seed,
                n_steps=1024, batch_size=256, learning_rate=3e-4)
    model.learn(total_timesteps=a.timesteps, callback=eval_cb)
    model.save(f"{a.out}/final_model")
    env.close()
    eval_env.close()

    plot_all(f"{a.out}/monitor.csv", f"{a.out}/eval/evaluations.npz",
             f"{a.out}/plots.png")
    print(f"saved model + plots in {a.out}")


if __name__ == "__main__":
    main()
