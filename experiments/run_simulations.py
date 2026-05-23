"""
experiments/run_simulations.py — Synthetic simulation suite (Sections A–D).

Generates controlled synthetic data under each of four DGPs,
runs the calibration pipeline, and reports metrics + figures.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.data import (sim_iid_student_t, sim_iid_skewed_t, sim_iid_lognormal,
                      sim_garch_t, sim_markov_switching, sim_jump_diffusion)
from src.backtest import run_full_experiment
from src.utils import metrics_to_table, save_metrics_csv, plot_var_backtest
from config import RESULTS_DIR, FIGURES_DIR, TAIL_LEVELS


TRAIN = 750
CAL = 250
N_SIM = 3000   # total length per simulation


def run_scenario(name: str, returns: np.ndarray, forecasters=None):
    """Run a full experiment on one synthetic scenario."""
    if forecasters is None:
        forecasters = ["HS", "EWMA", "GARCH-t"]

    print(f"\n{'#'*70}")
    print(f"  SCENARIO: {name}  (n={len(returns)})")
    print(f"{'#'*70}")

    results = run_full_experiment(
        returns=returns,
        asset_name=name,
        forecaster_names=forecasters,
        tail_levels=TAIL_LEVELS,
        train_window=TRAIN,
        cal_window=CAL,
        verbose=True,
    )

    # Print tables
    for p in TAIL_LEVELS:
        print(f"\n--- Tail level p = {p} ---")
        print(metrics_to_table(results, p))

    # Save CSV
    csv_path = os.path.join(RESULTS_DIR, f"sim_{name.replace(' ', '_')}.csv")
    save_metrics_csv(results, TAIL_LEVELS, csv_path)

    # Save representative plot
    for fc_name in forecasters[:1]:
        for cal_name in ["Uncalibrated", "Full (DKW)"]:
            bt = results.get(fc_name, {}).get(cal_name)
            if bt is None:
                continue
            for p in TAIL_LEVELS:
                fname = f"sim_{name}_{fc_name}_{cal_name}_p{int(p*100)}.png"
                fname = fname.replace(" ", "_").replace("(", "").replace(")", "")
                plot_var_backtest(
                    losses=bt["losses"],
                    var_forecasts=bt["forecasts"][p],
                    tail_level=p,
                    title=f"{name} | {fc_name} + {cal_name}",
                    save_path=os.path.join(FIGURES_DIR, fname),
                )
    return results


def main():
    np.random.seed(42)

    # ── Simulation A: i.i.d. Heavy Tails ──
    for dist_name, gen in [
        ("A1_StudentT", lambda: sim_iid_student_t(N_SIM, df=4, scale=0.012, seed=42)),
        ("A2_SkewedT",  lambda: sim_iid_skewed_t(N_SIM, df=5, skew_param=-0.3, seed=43)),
        ("A3_LogNorm",  lambda: sim_iid_lognormal(N_SIM, sigma=0.8, seed=44)),
    ]:
        run_scenario(dist_name, gen())

    # ── Simulation B: GARCH with t-innovations ──
    run_scenario("B_GARCH_t", sim_garch_t(N_SIM, seed=45))

    # ── Simulation C: Markov-Switching Regime ──
    r_ms, _ = sim_markov_switching(N_SIM, seed=46)
    run_scenario("C_MarkovSwitch", r_ms)

    # ── Simulation D: Jump-Diffusion ──
    run_scenario("D_JumpDiffusion", sim_jump_diffusion(N_SIM, seed=47))

    print("\n\nAll simulation experiments complete.")
    print(f"Results saved to {RESULTS_DIR}")
    print(f"Figures saved to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
