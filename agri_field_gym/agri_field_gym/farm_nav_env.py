"""Gymnasium env: drive the Husky around farm_lite on lidar.

Obs (39,): 36 min-pooled lidar sectors [0..1] + dist_norm + sin/cos(heading_err).
Action [v, w]: v in [0, 1] m/s, w in [-1.5, 1.5] rad/s.
Needs: running farm_lite sim + agri_agent_bot spawn (pose TF bridge on /farm/pose_info).
"""
import math
import subprocess
import threading
import time

import gymnasium as gym
import numpy as np
from gymnasium import spaces

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from tf2_msgs.msg import TFMessage

from agri_field_gym.nav_utils import (
    N_LIDAR, MAX_RANGE, COLLIDE_DIST, ARRIVE_DIST,
    angle_wrap, downsample_scan, sample_target, compute_reward,
)

STEP_DT = 0.2
MAX_STEPS = 400
START_POSE = (-6.0, 4.0, 0.0)  # aisle-0 entrance, facing +X


class FarmNavEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, lidar_topic="/a300_0000/sensors/lidar3d_0/scan",
                 cmd_topic="/a300_0000/cmd_vel",
                 pose_topic="/farm/pose_info",
                 robot_frame="base_link",
                 seed=None):
        super().__init__()
        self.rng = np.random.default_rng(seed)
        self.observation_space = spaces.Box(0.0, 1.0, shape=(N_LIDAR + 3,),
                                            dtype=np.float32)
        self.action_space = spaces.Box(
            np.array([0.0, -1.5], dtype=np.float32),
            np.array([1.0, 1.5], dtype=np.float32))

        if not rclpy.ok():
            rclpy.init()
        self.node = Node("farm_nav_env")
        self.cmd_pub = self.node.create_publisher(Twist, cmd_topic, 10)
        self.scan = None
        self.pose = None  # (x, y, yaw)
        self.node.create_subscription(LaserScan, lidar_topic, self._on_scan, 10)
        self.node.create_subscription(TFMessage, pose_topic, self._on_tf, 10)
        self._robot_frame = robot_frame
        self._spin = threading.Thread(
            target=rclpy.spin, args=(self.node,), daemon=True)
        self._spin.start()

        self.target = (0.0, 0.0)
        self.prev_dist = 0.0
        self.steps = 0
        self.last_v = 0.0
        self.last_w = 0.0

    # -- ROS callbacks ----------------------------------------------------
    def _on_scan(self, msg):
        self.scan = list(msg.ranges)

    def _on_tf(self, msg):
        for t in msg.transforms:
            if self._robot_frame in t.child_frame_id:
                x = t.transform.translation.x
                y = t.transform.translation.y
                q = t.transform.rotation
                yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                                 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
                self.pose = (x, y, yaw)
                return

    def _wait(self, cond, what, timeout=15.0):
        t0 = time.time()
        while not cond():
            if time.time() - t0 > timeout:
                raise TimeoutError(f"no {what} (is the sim + spawn running?)")
            time.sleep(0.05)

    @staticmethod
    def _set_pose(name, x, y, yaw):
        subprocess.run(
            ["gz", "service", "-s", "/world/farm/set_pose",
             "--reqtype", "gz.msgs.Pose", "--reptype", "gz.msgs.Boolean",
             "--timeout", "5000", "--req",
             f'name: "{name}" position: {{x: {x}, y: {y}, z: 0.3}} '
             f'orientation: {{x: 0, y: 0, z: {math.sin(yaw/2):.4f}, w: {math.cos(yaw/2):.4f}}}'],
            capture_output=True, timeout=20)

    def _stop(self):
        self.cmd_pub.publish(Twist())
        self.last_v = 0.0
        self.last_w = 0.0

    # -- gym API ----------------------------------------------------------
    def _obs(self):
        ranges = self.scan if self.scan else [MAX_RANGE] * 360
        lidar = downsample_scan(ranges)
        x, y, yaw = self.pose
        dx, dy = self.target[0] - x, self.target[1] - y
        dist = math.hypot(dx, dy)
        err = angle_wrap(math.atan2(dy, dx) - yaw)
        return np.array(lidar + [min(1.0, dist / 50.0),
                                 math.sin(err), math.cos(err)], dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self._wait(lambda: self.scan is not None, "lidar scan")
        self._wait(lambda: self.pose is not None, "robot pose")
        self._set_pose("a300_0000/robot", *START_POSE)
        time.sleep(0.3)
        self._stop()
        self.target = sample_target(self.rng, *START_POSE[:2])
        self.prev_dist = math.hypot(self.target[0] - START_POSE[0],
                                    self.target[1] - START_POSE[1])
        self.steps = 0
        return self._obs(), {"target": self.target}

    def step(self, action):
        v = float(np.clip(action[0], 0.0, 1.0))
        w = float(np.clip(action[1], -1.5, 1.5))
        msg = Twist()
        msg.linear.x, msg.angular.z = v, w
        self.cmd_pub.publish(msg)
        self.last_v, self.last_w = v, w
        time.sleep(STEP_DT)
        self.steps += 1

        ranges = self.scan if self.scan else [MAX_RANGE] * 360
        min_range = min([r for r in ranges
                         if r == r and r != float("inf") and r > 0.0]
                        or [MAX_RANGE])
        x, y, _ = self.pose
        dist = math.hypot(self.target[0] - x, self.target[1] - y)
        collided = min_range < COLLIDE_DIST
        arrived = dist < ARRIVE_DIST
        reward, terminated, success = compute_reward(
            self.prev_dist, dist, STEP_DT, collided, arrived, w)
        self.prev_dist = dist
        truncated = self.steps >= MAX_STEPS
        if terminated or truncated:
            self._stop()
        return self._obs(), reward, terminated, truncated, \
            {"is_success": success, "dist": dist, "min_range": min_range}

    def close(self):
        try:
            self._stop()
            self.node.destroy_node()
        except Exception:
            pass
