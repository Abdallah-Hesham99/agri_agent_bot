"""Plots from SB3 Monitor CSV + EvalCallback evaluations.npz."""
import csv
import numpy as np


def _load_monitor(path):
    r, l, t = [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            r.append(float(row["r"]))
            l.append(float(row["l"]))
            t.append(float(row["t"]))
    return np.array(r), np.array(l), np.array(t)


def _roll(x, w=20):
    if len(x) < w:
        return x
    return np.convolve(x, np.ones(w) / w, mode="valid")


def plot_all(monitor_csv, eval_npz, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r, l, _ = _load_monitor(monitor_csv)
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))

    ax[0, 0].plot(_roll(r))
    ax[0, 0].set_title("episode reward (rolling mean)")
    ax[0, 0].set_xlabel("episode")
    ax[0, 1].plot(_roll(l))
    ax[0, 1].set_title("episode length (rolling mean)")
    ax[0, 1].set_xlabel("episode")

    try:
        ev = np.load(eval_npz)
        steps, means, succ = ev["timesteps"], ev["results"].mean(1), None
        ax[1, 0].plot(steps, means)
        ax[1, 0].set_title("eval mean reward")
        ax[1, 0].set_xlabel("timesteps")
        if "successes" in ev:
            ax[1, 1].plot(steps, ev["successes"].mean(1))
            ax[1, 1].set_title("eval success rate")
            ax[1, 1].set_xlabel("timesteps")
        else:
            ax[1, 1].text(0.5, 0.5, "no success data", ha="center")
    except FileNotFoundError:
        ax[1, 0].text(0.5, 0.5, "no eval data yet", ha="center")
        ax[1, 1].text(0.5, 0.5, "no eval data yet", ha="center")

    fig.tight_layout()
    fig.savefig(out_png, dpi=100)
    print(f"plots -> {out_png}")
