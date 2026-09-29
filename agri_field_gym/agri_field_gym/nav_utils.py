"""Pure helpers for the farm navigation gym env (no ROS imports: unit-testable)."""
import math
import random

N_LIDAR = 36
MAX_RANGE = 12.0
COLLIDE_DIST = 0.4
ARRIVE_DIST = 0.7

# Obstacles the target sampler must avoid: ((x, y, r), ...).
# Rows y = 8*i+2.2, trees x = 0..35 step 5 (lite rows 0-2; full adds 3-4).
TREES = [(x, 8.0*i + 2.2) for i in range(5) for x in
         [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0]]
BARN = (-6.0, -5.0, 6.0)          # x, y, radius (covers 9.6x8.1 footprint)
TOWER = (38.0, -5.0, 2.0)
FENCE = (-14.5, 44.5, -12.5, 30.5)  # xmin, xmax, ymin, ymax


def angle_wrap(a):
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


def downsample_scan(ranges, n=N_LIDAR, max_range=MAX_RANGE):
    """Min-pool raw ranges into n sectors; inf/nan -> max_range; clip; normalize."""
    clean = [r if r == r and r != float("inf") and r > 0.0 else max_range
             for r in ranges]
    if not clean:
        return [1.0] * n
    out = []
    for i in range(n):
        a = int(i * len(clean) / n)
        b = max(a + 1, int((i + 1) * len(clean) / n))
        out.append(min(clean[a:b]) / max_range)
    return [min(1.0, max(0.02, v)) for v in out]


def is_free(x, y, margin=1.0):
    xmin, xmax, ymin, ymax = FENCE
    if not (xmin + margin < x < xmax - margin and ymin + margin < y < ymax - margin):
        return False
    for tx, ty in TREES:
        if math.hypot(x - tx, y - ty) < 0.6 + margin:
            return False
    for ox, oy, r in (BARN, TOWER):
        if math.hypot(x - ox, y - oy) < r + margin:
            return False
    return True


def sample_target(rng, rx, ry, min_dist=8.0):
    """Random reachable target at least min_dist from the robot."""
    xmin, xmax, ymin, ymax = FENCE
    for _ in range(200):
        x = rng.uniform(xmin + 2.0, xmax - 2.0)
        y = rng.uniform(ymin + 2.0, ymax - 2.0)
        if math.hypot(x - rx, y - ry) >= min_dist and is_free(x, y):
            return (x, y)
    return (xmax - 5.0, (ymin + ymax) / 2.0)  # fallback: east aisle end


def compute_reward(prev_dist, dist, dt, collided, arrived,
                   w=0.0, progress_gain=3.0, time_penalty=0.05,
                   arrive_bonus=20.0, collide_penalty=-10.0, turn_penalty=0.005):
    """Time + closeness shaped reward. Returns (reward, terminated, success)."""
    reward = (prev_dist - dist) * progress_gain - time_penalty * dt \
        - turn_penalty * abs(w)
    if arrived:
        return reward + arrive_bonus, True, True
    if collided:
        return reward + collide_penalty, True, False
    return reward, False, False
