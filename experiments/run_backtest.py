"""
experiments/run_backtest.py — Multi-asset backtesting experiment.

Uses synthetic assets modelled on SPY, QQQ, IWM, GLD, TLT and BTC-USD.
Each asset is generated with GARCH + jump-diffusion dynamics whose
parameters are hand-set per ticker in src/data.py (nothing is fitted to
market data). Writes results/backtest_results.csv (Table 2 of the
working paper) plus figures.

Each asset's seed is derived from its ticker with CRC32, so runs are
reproducible. (An earlier version used Python's hash(), which is salted
per process, so its asset paths could not be reproduced.)
"""

import sys, os, zlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from src.data import generate_synthetic_asset
from src.backtest import run_full_experiment
from src.utils import (metrics_to_table, save_combined_metrics_csv,
                       plot_var_backtest, plot_crisis_window)
from config import (RESULTS_DIR, FIGURES_DIR, TAIL_LEVELS, ASSET_TICKERS,
                    TRAIN_WINDOW, CALIBRATION_WINDOW, RETRAIN_FREQ,
                    N_ASSET_DAYS, FORECASTERS, BACKTEST_CALIBRATORS)


N_DAYS = N_ASSET_DAYS  # ~14 years of trading days


def asset_seed(ticker: str) -> int:
    """Stable per-ticker seed (unlike hash(), identical across runs)."""
    return zlib.crc32(ticker.encode()) % 2**31


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

        asset = generate_synthetic_asset(ticker, n=N_DAYS, seed=asset_seed(ticker))
        returns = asset["returns"]

        results = run_full_experiment(
            returns=returns,
            asset_name=ticker,
            forecaster_names=FORECASTERS,
            tail_levels=TAIL_LEVELS,
            train_window=TRAIN_WINDOW,
            cal_window=CALIBRATION_WINDOW,
            retrain_freq=RETRAIN_FREQ,
            calibrator_names=BACKTEST_CALIBRATORS,
            verbose=True,
        )
        all_results[ticker] = results

        # Print summary tables
        for p in TAIL_LEVELS:
            print(f"\n--- {ticker} | Tail level p = {p} ---")
            print(metrics_to_table(results, p))

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

        # Crisis-window analysis (on the evaluated test days)
        test_start = int(results[FORECASTERS[0]]["Uncalibrated"]["test_idx"][0])
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

    csv_path = os.path.join(RESULTS_DIR, "backtest_results.csv")
    save_combined_metrics_csv(all_results, "asset", TAIL_LEVELS, csv_path)

    print("\n\nAll asset backtests complete.")
    print(f"Results saved to {csv_path}")


if __name__ == "__main__":
    main()
