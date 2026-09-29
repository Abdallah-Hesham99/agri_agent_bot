"""Unit tests for pure helpers (no ROS, no sim needed). Run: python3 test_units.py"""
import math
import random

from agri_field_gym.nav_utils import (
    angle_wrap, compute_reward, downsample_scan, is_free, sample_target,
)

fails = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


check("wrap", abs(angle_wrap(3 * math.pi) - math.pi) < 1e-9)
check("downsample_n", len(downsample_scan([5.0] * 360)) == 36)
check("downsample_minpool",
      downsample_scan([10.0] * 360)[0] > downsample_scan([10.0] * 180 + [0.5] * 180)[-1])
check("downsample_inf", all(v == 1.0 for v in downsample_scan([float("inf")] * 360)))
r, term, succ = compute_reward(10.0, 9.0, 0.2, False, False)
check("progress_reward", r > 0 and not term)
r2, term2, succ2 = compute_reward(5.0, 0.5, 0.2, False, True)
check("arrive", term2 and succ2 and r2 > 15)
r3, term3, succ3 = compute_reward(5.0, 4.9, 0.2, True, False)
check("collide", term3 and not succ3 and r3 < -5)
check("tree_blocked", not is_free(0.0, 2.2))
check("aisle_free", is_free(-6.0, 4.0))
rng = random.Random(0)
import numpy as np
t = sample_target(np.random.default_rng(0), -6.0, 4.0)
check("target_far", math.hypot(t[0] + 6.0, t[1] - 4.0) >= 8.0 and is_free(*t))

print("FAILURES:", fails or "none")
raise SystemExit(1 if fails else 0)
