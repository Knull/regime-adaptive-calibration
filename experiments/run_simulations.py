"""
experiments/run_simulations.py — Synthetic simulation suite (Sections A–D).

Generates controlled synthetic data under each of four DGP families,
runs the calibration pipeline, and writes results/simulation_results.csv
(the file behind Table 1 of the working paper) plus figures.

Settings come from config.py: 2,500 observations per scenario, a 500-day
training window, a 200-day calibration window and base forecasters refit
every 50 days. The first 200 forecast days only build the residual history
the calibration window needs, so each scenario is scored on its last 1,600
days, the same days for every calibrator.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.data import (sim_iid_student_t, sim_iid_skewed_t,
                      sim_garch_t, sim_markov_switching, sim_jump_diffusion)
from src.backtest import run_full_experiment
from src.utils import metrics_to_table, save_combined_metrics_csv, plot_var_backtest
from config import (RESULTS_DIR, FIGURES_DIR, TAIL_LEVELS, TRAIN_WINDOW,
                    CALIBRATION_WINDOW, RETRAIN_FREQ, N_SIM_OBS,
                    FORECASTERS, SIM_CALIBRATORS)


def run_scenario(name: str, returns: np.ndarray, forecasters=None):
    """Run a full experiment on one synthetic scenario."""
    if forecasters is None:
        forecasters = FORECASTERS

    print(f"\n{'#'*70}")
    print(f"  SCENARIO: {name}  (n={len(returns)})")
    print(f"{'#'*70}")

    results = run_full_experiment(
        returns=returns,
        asset_name=name,
        forecaster_names=forecasters,
        tail_levels=TAIL_LEVELS,
        train_window=TRAIN_WINDOW,
        cal_window=CALIBRATION_WINDOW,
        retrain_freq=RETRAIN_FREQ,
        calibrator_names=SIM_CALIBRATORS,
        verbose=True,
    )

    # Print tables
    for p in TAIL_LEVELS:
        print(f"\n--- Tail level p = {p} ---")
        print(metrics_to_table(results, p))

    # Save representative plots
    for fc_name in forecasters:
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
    all_results = {}

    # ── Simulation A: i.i.d. Heavy Tails ──
    # (src.data.sim_iid_lognormal is also available but is not part of the
    # reported suite.)
    all_results["A1_StudentT"] = run_scenario(
        "A1_StudentT", sim_iid_student_t(N_SIM_OBS, df=4, scale=0.012, seed=42))
    all_results["A2_SkewedT"] = run_scenario(
        "A2_SkewedT", sim_iid_skewed_t(N_SIM_OBS, df=5, skew_param=-0.3, seed=43))

    # ── Simulation B: GARCH with t-innovations ──
    all_results["B_GARCH_t"] = run_scenario("B_GARCH_t", sim_garch_t(N_SIM_OBS, seed=45))

    # ── Simulation C: Markov-Switching Regime ──
    r_ms, _ = sim_markov_switching(N_SIM_OBS, seed=46)
    all_results["C_MarkovSwitch"] = run_scenario("C_MarkovSwitch", r_ms)

    # ── Simulation D: Jump-Diffusion ──
    all_results["D_JumpDiffusion"] = run_scenario(
        "D_JumpDiffusion", sim_jump_diffusion(N_SIM_OBS, seed=47))

    csv_path = os.path.join(RESULTS_DIR, "simulation_results.csv")
    save_combined_metrics_csv(all_results, "scenario", TAIL_LEVELS, csv_path)

    print("\n\nAll simulation experiments complete.")
    print(f"Results saved to {csv_path}")
    print(f"Figures saved to {FIGURES_DIR}")


if __name__ == "__main__":
    main()
