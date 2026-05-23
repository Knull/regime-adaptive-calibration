"""
src/utils.py — Plotting and reporting utilities.
"""

from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os


def plot_var_backtest(
    losses: np.ndarray,
    var_forecasts: np.ndarray,
    tail_level: float,
    title: str = "VaR Backtest",
    save_path: str | None = None,
    figsize: tuple = (14, 5),
):
    """Plot losses vs VaR forecast with violation markers."""
    fig, ax = plt.subplots(figsize=figsize)
    n = len(losses)
    x = np.arange(n)

    ax.plot(x, losses, color="#555555", alpha=0.5, lw=0.5, label="Loss")
    ax.plot(x, var_forecasts, color="#D32F2F", lw=1.2,
            label=f"VaR ({100*(1-tail_level):.0f}%)")

    violations = losses > var_forecasts
    ax.scatter(x[violations], losses[violations], color="#D32F2F",
               s=12, zorder=5, label=f"Violations ({violations.sum()})")

    emp_rate = violations.mean()
    ax.set_title(f"{title}  |  Exc. rate: {emp_rate:.2%} (target {tail_level:.2%})")
    ax.set_xlabel("Time step")
    ax.set_ylabel("Loss")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def plot_crisis_window(
    losses: np.ndarray,
    var_dict: dict[str, np.ndarray],
    window_start: int,
    window_end: int,
    tail_level: float,
    title: str = "Crisis Window",
    save_path: str | None = None,
):
    """Plot a zoomed-in crisis window comparing multiple VaR methods."""
    fig, ax = plt.subplots(figsize=(12, 5))
    sl = slice(window_start, window_end)
    x = np.arange(window_end - window_start)

    ax.fill_between(x, 0, losses[sl], alpha=0.2, color="#555555", label="Loss")
    ax.plot(x, losses[sl], color="#555555", lw=0.8)

    colors = ["#D32F2F", "#1976D2", "#388E3C", "#F57C00", "#7B1FA2", "#00796B"]
    for i, (name, var_arr) in enumerate(var_dict.items()):
        ax.plot(x, var_arr[sl], lw=1.5, color=colors[i % len(colors)],
                label=name, alpha=0.85)

    ax.set_title(f"{title}  (tail level = {tail_level})")
    ax.set_xlabel("Day within window")
    ax.set_ylabel("Loss")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return fig


def metrics_to_table(results: dict, tail_level: float) -> str:
    """
    Format experiment results into a readable text table.

    results: {forecaster: {calibrator: backtest_result_dict}}
    """
    header = (f"{'Forecaster':<12} {'Calibrator':<18} {'Exc.Rate':>9} "
              f"{'Dev':>7} {'Kupiec-p':>9} {'CC-p':>9} {'Cluster':>8} "
              f"{'Overshoot':>10} {'Buffer':>8}")
    lines = [header, "-" * len(header)]

    for fc_name, cal_dict in results.items():
        for cal_name, bt in cal_dict.items():
            if bt is None:
                continue
            m = bt["metrics"].get(tail_level, {})
            line = (
                f"{fc_name:<12} {cal_name:<18} "
                f"{m.get('exceedance_rate', 0):>9.4f} "
                f"{m.get('exceedance_deviation', 0):>7.4f} "
                f"{m.get('kupiec_pval', 0):>9.4f} "
                f"{m.get('christoffersen_pval', 0):>9.4f} "
                f"{m.get('clustering', 0):>8.4f} "
                f"{m.get('overshoot_severity', 0):>10.6f} "
                f"{m.get('avg_buffer_width', 0):>8.5f}"
            )
            lines.append(line)
    return "\n".join(lines)


def save_metrics_csv(results: dict, tail_levels: list[float], path: str):
    """Save all metrics to a CSV file."""
    import csv
    rows = []
    for fc_name, cal_dict in results.items():
        for cal_name, bt in cal_dict.items():
            if bt is None:
                continue
            for p in tail_levels:
                m = bt["metrics"].get(p, {})
                row = {"forecaster": fc_name, "calibrator": cal_name,
                       "tail_level": p}
                row.update(m)
                rows.append(row)

    if not rows:
        return
    keys = rows[0].keys()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
