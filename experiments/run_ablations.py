"""
experiments/run_ablations.py — Ablation study.

Runs all calibrator variants (plain conformal, time-weighted, regime-weighted,
time+regime, full DKW, full+mono) on a representative subset of scenarios
to isolate the contribution of each component.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import csv
from src.data import sim_garch_t, sim_markov_switching, generate_synthetic_asset
from src.backtest import run_full_experiment
from src.utils import metrics_to_table
from config import RESULTS_DIR, FIGURES_DIR, TAIL_LEVELS


SCENARIOS = {
    "GARCH-t": lambda: sim_garch_t(3000, seed=45),
    "Markov-Switch": lambda: sim_markov_switching(3000, seed=46)[0],
    "SPY-Synth": lambda: generate_synthetic_asset("SPY", n=4000, seed=100)["returns"],
    "BTC-Synth": lambda: generate_synthetic_asset("BTC-USD", n=4000, seed=200)["returns"],
}

FORECASTERS = ["HS", "EWMA"]


def main():
    all_rows = []

    for sc_name, gen_fn in SCENARIOS.items():
        returns = gen_fn()
        print(f"\n{'#'*70}")
        print(f"  ABLATION: {sc_name}")
        print(f"{'#'*70}")

        results = run_full_experiment(
            returns=returns,
            asset_name=sc_name,
            forecaster_names=FORECASTERS,
            tail_levels=TAIL_LEVELS,
            train_window=750,
            cal_window=250,
            verbose=True,
        )

        for p in TAIL_LEVELS:
            print(f"\n--- {sc_name} | p = {p} ---")
            print(metrics_to_table(results, p))

        # Collect rows for summary
        for fc_name, cal_dict in results.items():
            for cal_name, bt in cal_dict.items():
                if bt is None:
                    continue
                for p in TAIL_LEVELS:
                    m = bt["metrics"].get(p, {})
                    row = {
                        "scenario": sc_name,
                        "forecaster": fc_name,
                        "calibrator": cal_name,
                        "tail_level": p,
                        **m,
                    }
                    all_rows.append(row)

    # Save full ablation CSV
    if all_rows:
        path = os.path.join(RESULTS_DIR, "ablation_full.csv")
        keys = all_rows[0].keys()
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nAblation results saved to {path}")

    # Print summary: for each scenario × tail level, which calibrator has
    # the best exceedance deviation while keeping Kupiec p > 0.05?
    print("\n\n" + "=" * 70)
    print("  ABLATION SUMMARY: Best calibrator per scenario")
    print("=" * 70)
    for sc_name in SCENARIOS:
        for p in TAIL_LEVELS:
            candidates = [
                r for r in all_rows
                if r["scenario"] == sc_name and r["tail_level"] == p
                   and r.get("kupiec_pval", 0) > 0.05
            ]
            if candidates:
                best = min(candidates, key=lambda r: r.get("exceedance_deviation", 1))
                print(f"  {sc_name} p={p}: {best['forecaster']}+{best['calibrator']} "
                      f"(exc.dev={best['exceedance_deviation']:.4f}, "
                      f"Kupiec p={best['kupiec_pval']:.3f})")
            else:
                print(f"  {sc_name} p={p}: No method passes Kupiec at 5%")

    print("\nAblation study complete.")


if __name__ == "__main__":
    main()
