"""
src/backtest.py — Rolling walk-forward backtesting engine.

Orchestrates:
  1. Rolling train / calibration / test splits
  2. Base forecaster fitting
  3. Calibration layer application
  4. Metric collection
"""

from __future__ import annotations
import numpy as np
from typing import Optional
from tqdm import tqdm

from src.features import compute_regime_features, normalise_features
from src.forecasters import get_forecaster
from src.calibration import RegimeAdaptiveCalibrator, get_calibrator_variants
from src.metrics import compute_all_metrics


def run_single_backtest(
    returns: np.ndarray,
    forecaster_name: str,
    calibrator: Optional[RegimeAdaptiveCalibrator],
    tail_levels: list[float],
    train_window: int = 750,
    cal_window: int = 250,
    retrain_freq: int = 20,
    verbose: bool = False,
) -> dict:
    """
    Run a full rolling backtest for one (forecaster, calibrator) pair.

    Parameters
    ----------
    returns        : daily return series
    forecaster_name: key in FORECASTER_REGISTRY
    calibrator     : a RegimeAdaptiveCalibrator or None (uncalibrated)
    tail_levels    : list of p values (e.g. [0.05, 0.01])
    train_window   : training window length
    cal_window     : calibration window length
    retrain_freq   : retrain base forecaster every N steps
    verbose        : show progress bar

    Returns
    -------
    dict with keys:
        'losses'     : (T_test,) actual losses on test days
        'forecasts'  : {p: (T_test,) calibrated or uncalibrated VaR}
        'base_fc'    : {p: (T_test,) base (uncalibrated) VaR}
        'metrics'    : {p: metrics_dict}
        'test_idx'   : indices into original series
    """
    losses = -returns  # L_t = -r_t
    n = len(returns)
    features = compute_regime_features(returns)
    features_norm = normalise_features(features)

    start_test = train_window + cal_window
    if start_test >= n:
        raise ValueError("Series too short for the given windows.")

    test_range = range(start_test, n)
    T_test = len(test_range)

    # Storage
    base_forecasts_all = {p: np.full(n, np.nan) for p in tail_levels}
    cal_forecasts = {p: np.zeros(T_test) for p in tail_levels}
    base_forecasts_test = {p: np.zeros(T_test) for p in tail_levels}
    test_losses = np.zeros(T_test)
    test_idx = np.array(list(test_range))

    # Pre-fit base forecaster across the series using rolling windows
    last_trained = -retrain_freq  # force initial train
    forecaster = get_forecaster(forecaster_name)

    iterator = tqdm(enumerate(test_range), total=T_test,
                    desc=f"{forecaster_name}", disable=not verbose)

    for j, t in iterator:
        # ── Re-train base forecaster periodically ──
        if t - last_trained >= retrain_freq:
            train_end = t - cal_window
            train_start = max(0, train_end - train_window)
            train_losses = losses[train_start:train_end]

            # Features for ML-based forecasters
            train_feats = features_norm[train_start:train_end]
            valid = ~np.any(np.isnan(train_feats), axis=1)
            if valid.sum() < 30:
                train_feats = None
            else:
                train_feats = train_feats[valid]
                train_losses_f = train_losses[valid]

            try:
                if train_feats is not None and forecaster_name in ("QR", "LightGBM"):
                    forecaster = get_forecaster(forecaster_name)
                    forecaster.fit(train_losses_f, train_feats)
                else:
                    forecaster = get_forecaster(forecaster_name)
                    forecaster.fit(train_losses)
            except Exception:
                forecaster = get_forecaster("HS")
                forecaster.fit(train_losses)
            last_trained = t

        # ── Base forecast for each tail level ──
        feat_t = features_norm[t] if t < len(features_norm) else None
        feat_t_clean = feat_t if feat_t is not None and not np.any(np.isnan(feat_t)) else None
        for p in tail_levels:
            try:
                base_var = forecaster.predict(p, feat_t_clean)
            except Exception:
                base_var = float(np.quantile(losses[max(0, t - train_window):t], 1 - p))
            base_forecasts_all[p][t] = base_var
            base_forecasts_test[p][j] = base_var

        test_losses[j] = losses[t]

        # ── Calibration ──
        if calibrator is not None:
            cal_start = t - cal_window
            cal_end = t
            try:
                cal_result = calibrator.calibrate(
                    base_forecasts=base_forecasts_all,
                    losses=losses,
                    features=features_norm,
                    t=t,
                    cal_start=cal_start,
                    cal_end=cal_end,
                    K=len(tail_levels),
                )
                for p in tail_levels:
                    cal_forecasts[p][j] = cal_result[p]
            except Exception:
                for p in tail_levels:
                    cal_forecasts[p][j] = base_forecasts_test[p][j]
        else:
            for p in tail_levels:
                cal_forecasts[p][j] = base_forecasts_test[p][j]

    # ── Compute metrics ──
    metrics = {}
    for p in tail_levels:
        metrics[p] = compute_all_metrics(
            losses=test_losses,
            var_forecasts=cal_forecasts[p],
            tail_level=p,
            base_forecasts=base_forecasts_test[p],
        )

    return {
        "losses": test_losses,
        "forecasts": cal_forecasts,
        "base_fc": base_forecasts_test,
        "metrics": metrics,
        "test_idx": test_idx,
    }


def run_full_experiment(
    returns: np.ndarray,
    asset_name: str = "Asset",
    forecaster_names: list[str] | None = None,
    tail_levels: list[float] | None = None,
    train_window: int = 750,
    cal_window: int = 250,
    verbose: bool = True,
) -> dict:
    """
    Run all (forecaster × calibrator variant) combinations.

    Returns nested dict:
        results[forecaster_name][calibrator_name] = backtest_result
    """
    if forecaster_names is None:
        forecaster_names = ["HS", "EWMA", "GARCH-t"]
    if tail_levels is None:
        tail_levels = [0.05, 0.01]

    cal_variants = get_calibrator_variants()
    results = {}

    for fc_name in forecaster_names:
        results[fc_name] = {}
        for cal_name, calibrator in cal_variants.items():
            if verbose:
                print(f"\n{'='*60}")
                print(f"  {asset_name} | {fc_name} + {cal_name}")
                print(f"{'='*60}")
            try:
                bt = run_single_backtest(
                    returns=returns,
                    forecaster_name=fc_name,
                    calibrator=calibrator,
                    tail_levels=tail_levels,
                    train_window=train_window,
                    cal_window=cal_window,
                    verbose=verbose,
                )
                results[fc_name][cal_name] = bt
            except Exception as e:
                if verbose:
                    print(f"  FAILED: {e}")
                results[fc_name][cal_name] = None

    return results
