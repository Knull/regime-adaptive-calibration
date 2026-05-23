"""
src/calibration.py — Regime-Adaptive Distribution-Free Calibration Layer.

Implements the main method:
    Weighted, one-sided, regime-aware conformal calibration
    with a DKW-style finite-sample inflation term.

Mathematical Summary
--------------------
Given a base forecaster producing VaR forecasts q̂_t^(p) for tail level p,
calibration residuals are:

    e_i^(p) = L_i − q̂_i^(p)

Positive residuals indicate underestimation of loss.

Weights combine time-decay and regime similarity:

    w_{i,t} ∝ exp(−λ(t−i)) · exp(−γ ‖z_i − z_t‖²)

The weighted empirical CDF of residuals yields a calibration buffer:

    b_t^(p) = F̂_{w,t}^{(p),−1}(1 − p + ε_t)

where ε_t is a DKW-type inflation term scaled by effective sample size:

    ε_t = c · √( log(4K/δ) / (2·n_eff(t)) )

The calibrated forecast is:

    q̃_t^(p) = q̂_t^(p) + b_t^(p)
"""

from __future__ import annotations
import numpy as np
from typing import Optional


def compute_weights(
    t: int,
    z_history: np.ndarray,
    z_t: np.ndarray,
    lam: float = 0.01,
    gamma: float = 1.0,
    valid_mask: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Compute combined time-decay × regime-kernel weights for calibration
    points i = 0, …, t−1.

    Parameters
    ----------
    t          : index of the current (test) time step
    z_history  : (t, d) feature matrix for calibration points
    z_t        : (d,) feature vector at time t
    lam        : exponential time-decay rate
    gamma      : RBF kernel bandwidth for regime similarity
    valid_mask : boolean mask of shape (t,); True = usable calibration point

    Returns
    -------
    w : (t,) normalised weight vector
    """
    n = z_history.shape[0]
    assert n <= t, "History length must not exceed t"

    # Time decay: exp(-lam * (t - i))
    ages = t - np.arange(n)
    w_time = np.exp(-lam * ages)

    # Regime similarity: exp(-gamma * ||z_i - z_t||^2)
    if z_history.ndim == 1:
        z_history = z_history.reshape(-1, 1)
    if z_t.ndim == 0:
        z_t = z_t.reshape(1)
    diff = z_history - z_t[np.newaxis, :]
    # Handle NaNs gracefully: if any feature is NaN, set distance to median
    nan_rows = np.any(np.isnan(diff), axis=1)
    sq_dist = np.nansum(diff ** 2, axis=1)
    if np.any(nan_rows):
        median_dist = np.nanmedian(sq_dist[~nan_rows]) if np.any(~nan_rows) else 1.0
        sq_dist[nan_rows] = median_dist
    w_regime = np.exp(-gamma * sq_dist)

    w = w_time * w_regime

    if valid_mask is not None:
        w = w * valid_mask[:n].astype(float)

    # Normalise
    total = w.sum()
    if total < 1e-15:
        w = np.ones(n) / n
    else:
        w = w / total
    return w


def effective_sample_size(w: np.ndarray) -> float:
    """
    n_eff = (Σ w_i)² / Σ w_i²

    For normalised weights (Σ w_i = 1): n_eff = 1 / Σ w_i².
    """
    w_sum = w.sum()
    w_sq = (w ** 2).sum()
    if w_sq < 1e-30:
        return 1.0
    return (w_sum ** 2) / w_sq


def dkw_epsilon(n_eff: float, K: int, delta: float, c: float = 1.0) -> float:
    """
    DKW-style finite-sample inflation term:

        ε = c · √( log(4K / δ) / (2 · n_eff) )

    Parameters
    ----------
    n_eff : effective sample size
    K     : number of simultaneous tail levels
    delta : confidence budget
    c     : safety multiplier (default 1.0)
    """
    if n_eff < 1.0:
        n_eff = 1.0
    return c * np.sqrt(np.log(4 * K / delta) / (2 * n_eff))


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    """
    Compute the q-th quantile of `values` under `weights`.

    Uses the weighted-percentile method: sort by value, compute cumulative
    weights, and interpolate.
    """
    idx = np.argsort(values)
    sorted_vals = values[idx]
    sorted_w = weights[idx]
    cum_w = np.cumsum(sorted_w)
    # Normalise cumulative weights to [0, 1]
    cum_w = cum_w / cum_w[-1]
    # Find first index where cumulative weight >= q
    i = np.searchsorted(cum_w, q)
    i = min(i, len(sorted_vals) - 1)
    return float(sorted_vals[i])


def calibrate_forecast(
    base_forecast: float,
    residuals: np.ndarray,
    weights: np.ndarray,
    tail_level: float,
    n_eff: float,
    K: int = 2,
    delta: float = 0.05,
    c: float = 1.0,
    use_dkw: bool = True,
) -> tuple[float, float]:
    """
    Apply the calibration layer to a base VaR forecast.

    Parameters
    ----------
    base_forecast : q̂_t^(p), the base model's VaR prediction
    residuals     : e_i = L_i − q̂_i  (calibration residuals)
    weights       : normalised weights for the calibration set
    tail_level    : p (e.g. 0.05 for 95% VaR)
    n_eff         : effective sample size
    K             : number of tail levels (for union-bound)
    delta         : confidence budget
    c             : DKW multiplier
    use_dkw       : whether to add the DKW inflation term

    Returns
    -------
    (calibrated_forecast, buffer)
    """
    eps = dkw_epsilon(n_eff, K, delta, c) if use_dkw else 0.0

    # The quantile of residuals we need:
    # We want P(L > q̃) ≤ p, so we need the (1 - p + ε)-quantile of residuals
    target_q = min(1.0 - tail_level + eps, 1.0)
    target_q = max(target_q, 0.0)

    buffer = weighted_quantile(residuals, weights, target_q)
    calibrated = base_forecast + buffer
    return calibrated, buffer


# ═══════════════════════════════════════════════════════════════════════════════
# Monotonicity Enforcement (Theorem 4)
# ═══════════════════════════════════════════════════════════════════════════════

def enforce_monotonicity(forecasts: dict[float, float]) -> dict[float, float]:
    """
    Ensure that more extreme tail levels produce larger VaR forecasts.

    If q̃_99 < q̃_95, apply isotonic rearrangement so that the ordering
    is monotone in tail severity.

    Parameters
    ----------
    forecasts : {tail_level: calibrated_var}  e.g. {0.05: 2.1, 0.01: 3.4}

    Returns
    -------
    Monotone-adjusted forecasts (same dict structure).
    """
    # Sort by tail level descending (less extreme first)
    levels = sorted(forecasts.keys(), reverse=True)
    vals = [forecasts[p] for p in levels]

    # Isotonic regression (pool adjacent violators) — values should be non-decreasing
    from sklearn.isotonic import IsotonicRegression
    ir = IsotonicRegression(increasing=True)
    adjusted = ir.fit_transform(np.arange(len(vals)), vals)

    return {p: float(v) for p, v in zip(levels, adjusted)}


# ═══════════════════════════════════════════════════════════════════════════════
# Full Calibration Pipeline
# ═══════════════════════════════════════════════════════════════════════════════

class RegimeAdaptiveCalibrator:
    """
    End-to-end regime-adaptive calibration layer.

    Wraps any base forecaster and applies weighted one-sided conformal
    calibration with optional DKW inflation and monotonicity enforcement.
    """

    def __init__(
        self,
        lam: float = 0.01,
        gamma: float = 1.0,
        delta: float = 0.05,
        c: float = 1.0,
        use_time_weights: bool = True,
        use_regime_weights: bool = True,
        use_dkw: bool = True,
        enforce_mono: bool = True,
    ):
        self.lam = lam
        self.gamma = gamma
        self.delta = delta
        self.c = c
        self.use_time_weights = use_time_weights
        self.use_regime_weights = use_regime_weights
        self.use_dkw = use_dkw
        self.enforce_mono = enforce_mono

    def calibrate(
        self,
        base_forecasts: dict[float, np.ndarray],
        losses: np.ndarray,
        features: np.ndarray,
        t: int,
        cal_start: int,
        cal_end: int,
        K: int = 2,
    ) -> dict[float, float]:
        """
        Produce calibrated VaR forecasts for time t.

        Parameters
        ----------
        base_forecasts : {tail_level: array of base VaR forecasts for each time step}
        losses         : full loss series
        features       : (n, d) normalised regime features
        t              : current time step (we forecast for t)
        cal_start      : start of calibration window
        cal_end        : end of calibration window (exclusive, == t)
        K              : number of tail levels

        Returns
        -------
        {tail_level: calibrated_var_forecast}
        """
        result = {}
        cal_idx = slice(cal_start, cal_end)
        z_cal = features[cal_idx]
        z_t = features[t] if t < len(features) else features[-1]

        # Compute weights
        effective_lam = self.lam if self.use_time_weights else 0.0
        effective_gamma = self.gamma if self.use_regime_weights else 0.0
        w = compute_weights(
            t=cal_end - cal_start,  # relative index within calibration window
            z_history=z_cal,
            z_t=z_t,
            lam=effective_lam,
            gamma=effective_gamma,
        )
        n_eff = effective_sample_size(w)

        for p, base_arr in base_forecasts.items():
            residuals = losses[cal_idx] - base_arr[cal_idx]
            cal_var, buf = calibrate_forecast(
                base_forecast=base_arr[t] if t < len(base_arr) else base_arr[-1],
                residuals=residuals,
                weights=w,
                tail_level=p,
                n_eff=n_eff,
                K=K,
                delta=self.delta,
                c=self.c,
                use_dkw=self.use_dkw,
            )
            result[p] = cal_var

        if self.enforce_mono and len(result) > 1:
            result = enforce_monotonicity(result)

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# Calibrator Variants for Ablation Studies
# ═══════════════════════════════════════════════════════════════════════════════

def get_calibrator_variants() -> dict[str, RegimeAdaptiveCalibrator]:
    """Return named calibrator variants for ablation experiments."""
    return {
        "Uncalibrated": None,  # special: means no calibration
        "Conformal-Plain": RegimeAdaptiveCalibrator(
            use_time_weights=False, use_regime_weights=False,
            use_dkw=False, enforce_mono=False,
        ),
        "Time-Weighted": RegimeAdaptiveCalibrator(
            use_time_weights=True, use_regime_weights=False,
            use_dkw=False, enforce_mono=False,
        ),
        "Regime-Weighted": RegimeAdaptiveCalibrator(
            use_time_weights=False, use_regime_weights=True,
            use_dkw=False, enforce_mono=False,
        ),
        "Time+Regime": RegimeAdaptiveCalibrator(
            use_time_weights=True, use_regime_weights=True,
            use_dkw=False, enforce_mono=False,
        ),
        "Full (DKW)": RegimeAdaptiveCalibrator(
            use_time_weights=True, use_regime_weights=True,
            use_dkw=True, enforce_mono=False,
        ),
        "Full+Mono": RegimeAdaptiveCalibrator(
            use_time_weights=True, use_regime_weights=True,
            use_dkw=True, enforce_mono=True,
        ),
    }
