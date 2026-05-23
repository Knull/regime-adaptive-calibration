"""
src/features.py — Regime-feature computation from return series.

All features are computed from returns alone (no proprietary data required).
Each function returns a 1-D array of the same length as the input, with
leading NaNs where the rolling window has not yet filled.
"""

import numpy as np
from typing import Optional


def rolling_volatility(returns: np.ndarray, window: int = 20) -> np.ndarray:
    """Rolling annualised standard deviation."""
    n = len(returns)
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        out[i] = np.std(returns[i - window + 1 : i + 1], ddof=1) * np.sqrt(252)
    return out


def rolling_downside_semivol(returns: np.ndarray, window: int = 20) -> np.ndarray:
    """Rolling downside semivolatility (only negative returns count)."""
    n = len(returns)
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        chunk = returns[i - window + 1 : i + 1]
        neg = chunk[chunk < 0]
        out[i] = np.std(neg, ddof=1) * np.sqrt(252) if len(neg) > 1 else 0.0
    return out


def rolling_skewness(returns: np.ndarray, window: int = 60) -> np.ndarray:
    """Rolling sample skewness."""
    from scipy.stats import skew as sp_skew
    n = len(returns)
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        out[i] = sp_skew(returns[i - window + 1 : i + 1])
    return out


def rolling_kurtosis(returns: np.ndarray, window: int = 60) -> np.ndarray:
    """Rolling excess kurtosis."""
    from scipy.stats import kurtosis as sp_kurt
    n = len(returns)
    out = np.full(n, np.nan)
    for i in range(window - 1, n):
        out[i] = sp_kurt(returns[i - window + 1 : i + 1])
    return out


def rolling_drawdown(returns: np.ndarray, window: int = 60) -> np.ndarray:
    """Rolling maximum drawdown over trailing window (positive number)."""
    n = len(returns)
    out = np.full(n, np.nan)
    cum = np.cumsum(np.concatenate([[0], returns]))  # cumulative log return
    for i in range(window - 1, n):
        window_cum = cum[i - window + 1 : i + 2]     # +2 because of leading 0
        running_max = np.maximum.accumulate(window_cum)
        dd = running_max - window_cum
        out[i] = np.max(dd)
    return out


def abs_lagged_return(returns: np.ndarray) -> np.ndarray:
    """Absolute value of the previous day's return."""
    out = np.full(len(returns), np.nan)
    out[1:] = np.abs(returns[:-1])
    return out


def compute_regime_features(returns: np.ndarray) -> np.ndarray:
    """
    Build the full regime-feature matrix z_t from a return series.

    Features (7 columns):
        0  rolling 5-day volatility
        1  rolling 20-day volatility
        2  downside semivolatility (20-day)
        3  rolling drawdown (60-day)
        4  rolling skewness (60-day)
        5  rolling excess kurtosis (60-day)
        6  absolute lagged return

    Returns shape (n, 7). Leading rows with insufficient history are NaN.
    """
    feats = np.column_stack([
        rolling_volatility(returns, 5),
        rolling_volatility(returns, 20),
        rolling_downside_semivol(returns, 20),
        rolling_drawdown(returns, 60),
        rolling_skewness(returns, 60),
        rolling_kurtosis(returns, 60),
        abs_lagged_return(returns),
    ])
    return feats


def normalise_features(Z: np.ndarray, clip: float = 5.0) -> np.ndarray:
    """
    Z-score normalise feature matrix column-wise (ignoring NaNs),
    then clip to [-clip, clip].
    """
    mu = np.nanmean(Z, axis=0, keepdims=True)
    sigma = np.nanstd(Z, axis=0, keepdims=True)
    sigma[sigma < 1e-12] = 1.0
    out = (Z - mu) / sigma
    return np.clip(out, -clip, clip)
