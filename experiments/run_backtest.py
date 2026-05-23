"""
experiments/run_backtest.py — Multi-asset backtesting experiment.

Uses synthetic assets that mimic the statistical properties of
SPY, QQQ, IWM, GLD, TLT, BTC-USD. Each asset is generated with
GARCH + jump-diffusion dynamics calibrated to approximate the
real asset's behaviour.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.data import generate_synthetic_asset
from src.backtest import run_full_experiment
from src.utils import (metrics_to_table, save_metrics_csv,
                       plot_var_backtest, plot_crisis_window)
from config import (RESULTS_DIR, FIGURES_DIR, TAIL_LEVELS,
                    ASSET_TICKERS, TRAIN_WINDOW, CALIBRATION_WINDOW)


N_DAYS = 5000  # ~20 years of trading days

FORECASTERS = ["HS", "EWMA", "GARCH-t"]  # keep compute manageable


def identify_crisis_windows(losses: np.ndarray, window: int = 60,
                            top_k: int = 3) -> list[tuple[int, int]]:
    """Find the top-k highest-volatility windows as crisis periods."""
    rolling_vol = np.array([
        np.std(losses[max(0, i - window):i]) if i >= window else 0.0
        for i in range(len(losses))
    ])
    windows = []
    for _ in range(top_k):
        peak = np.argmax(rolling_vol)
        ws = max(0, peak - window // 2)
        we = min(len(losses), ws + window)
        windows.append((ws, we))
        # Zero out region to find next peak
        rolling_vol[max(0, ws - window):min(len(rolling_vol), we + window)] = 0
    return sorted(windows)


def main():
    all_results = {}

    for ticker in ASSET_TICKERS:
        print(f"\n{'='*70}")
        print(f"  ASSET: {ticker}  ({N_DAYS} synthetic days)")
        print(f"{'='*70}")

        asset = generate_synthetic_asset(ticker, n=N_DAYS, seed=hash(ticker) % 2**31)
        returns = asset["returns"]

        results = run_full_experiment(
            returns=returns,
            asset_name=ticker,
            forecaster_names=FORECASTERS,
            tail_levels=TAIL_LEVELS,
            train_window=TRAIN_WINDOW,
            cal_window=CALIBRATION_WINDOW,
            verbose=True,
        )
        all_results[ticker] = results

        # Print summary tables
        for p in TAIL_LEVELS:
            print(f"\n--- {ticker} | Tail level p = {p} ---")
            print(metrics_to_table(results, p))

        # Save CSV
        csv_path = os.path.join(RESULTS_DIR, f"backtest_{ticker.replace('-', '_')}.csv")
        save_metrics_csv(results, TAIL_LEVELS, csv_path)

        # Plot VaR backtest for best combination
        losses = -returns
        for fc in FORECASTERS[:1]:
            for cal in ["Uncalibrated", "Full (DKW)"]:
                bt = results.get(fc, {}).get(cal)
                if bt is None:
                    continue
                for p in TAIL_LEVELS:
                    fname = (f"bt_{ticker}_{fc}_{cal}_p{int(p*100)}.png"
                             .replace(" ", "_").replace("(", "").replace(")", ""))
                    plot_var_backtest(
                        bt["losses"], bt["forecasts"][p], p,
                        title=f"{ticker} | {fc} + {cal}",
                        save_path=os.path.join(FIGURES_DIR, fname),
                    )

        # Crisis-window analysis
        test_start = TRAIN_WINDOW + CALIBRATION_WINDOW
        test_losses = losses[test_start:]
        crisis_wins = identify_crisis_windows(test_losses)
        for ci, (ws, we) in enumerate(crisis_wins):
            var_dict = {}
            for cal in ["Uncalibrated", "Full (DKW)"]:
                bt = results.get(FORECASTERS[0], {}).get(cal)
                if bt:
                    var_dict[f"HS+{cal}"] = bt["forecasts"][TAIL_LEVELS[0]]
            if var_dict:
                fname = f"crisis_{ticker}_window{ci}.png".replace("-", "_")
                plot_crisis_window(
                    test_losses, var_dict, ws, we, TAIL_LEVELS[0],
                    title=f"{ticker} Crisis Window {ci+1}",
                    save_path=os.path.join(FIGURES_DIR, fname),
                )

    print("\n\nAll asset backtests complete.")
    print(f"Results in {RESULTS_DIR}")


if __name__ == "__main__":
    main()
