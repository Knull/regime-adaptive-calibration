"""
src/metrics.py — Risk-backtest evaluation metrics.

Covers:
  - Unconditional exceedance deviation
  - Kupiec likelihood-ratio test (unconditional coverage)
  - Christoffersen conditional coverage / independence test
  - Exceedance clustering metric
  - Average conservativeness (buffer width)
  - Overshoot severity
  - Regime-conditional exceedance stability
"""

from __future__ import annotations
import numpy as np
from scipy.stats import chi2


def exceedance_rate(losses: np.ndarray, var_forecasts: np.ndarray) -> float:
    """Fraction of days where actual loss exceeded VaR forecast."""
    return float(np.mean(losses > var_forecasts))


def exceedance_deviation(losses: np.ndarray, var_forecasts: np.ndarray,
                         tail_level: float) -> float:
    """Absolute difference between empirical exceedance rate and target."""
    emp = exceedance_rate(losses, var_forecasts)
    return abs(emp - tail_level)


def kupiec_test(losses: np.ndarray, var_forecasts: np.ndarray,
                tail_level: float) -> dict:
    """
    Kupiec (1995) proportion-of-failures test.

    H0: true exceedance probability = tail_level
    Returns dict with keys: 'statistic', 'p_value', 'reject_5pct',
                             'observed_rate', 'expected_rate'.
    """
    n = len(losses)
    violations = losses > var_forecasts
    x = violations.sum()
    p0 = tail_level

    if x == 0 or x == n:
        # Degenerate: LR not well-defined
        return {"statistic": 0.0, "p_value": 1.0, "reject_5pct": False,
                "observed_rate": x / n, "expected_rate": p0}

    p_hat = x / n
    lr = -2 * (x * np.log(p0 / p_hat) + (n - x) * np.log((1 - p0) / (1 - p_hat)))
    pval = 1 - chi2.cdf(lr, df=1)
    return {
        "statistic": float(lr),
        "p_value": float(pval),
        "reject_5pct": pval < 0.05,
        "observed_rate": float(p_hat),
        "expected_rate": float(p0),
    }


def christoffersen_test(losses: np.ndarray, var_forecasts: np.ndarray,
                        tail_level: float) -> dict:
    """
    Christoffersen (1998) conditional coverage test.

    Tests both unconditional coverage AND independence of violations.
    Returns dict: 'statistic', 'p_value', 'reject_5pct',
                  'independence_stat', 'coverage_stat'.
    """
    violations = (losses > var_forecasts).astype(int)
    n = len(violations)

    # Transition counts
    n00, n01, n10, n11 = 0, 0, 0, 0
    for i in range(1, n):
        prev, curr = violations[i - 1], violations[i]
        if prev == 0 and curr == 0: n00 += 1
        elif prev == 0 and curr == 1: n01 += 1
        elif prev == 1 and curr == 0: n10 += 1
        else: n11 += 1

    # Avoid division by zero
    def safe_log(x):
        return np.log(max(x, 1e-15))

    # Independence LR
    p01 = n01 / max(n00 + n01, 1)
    p11 = n11 / max(n10 + n11, 1)
    p_hat = (n01 + n11) / max(n, 1)

    if p_hat <= 0 or p_hat >= 1:
        lr_ind = 0.0
    else:
        lr_ind = -2 * (
            (n00 + n10) * safe_log(1 - p_hat) + (n01 + n11) * safe_log(p_hat)
            - n00 * safe_log(1 - p01) - n01 * safe_log(p01)
            - n10 * safe_log(1 - p11) - n11 * safe_log(p11)
        )
        lr_ind = max(lr_ind, 0.0)

    # Coverage LR (Kupiec)
    kup = kupiec_test(losses, var_forecasts, tail_level)
    lr_cov = kup["statistic"]

    lr_cc = lr_cov + lr_ind
    pval = 1 - chi2.cdf(lr_cc, df=2)

    return {
        "statistic": float(lr_cc),
        "p_value": float(pval),
        "reject_5pct": pval < 0.05,
        "independence_stat": float(lr_ind),
        "coverage_stat": float(lr_cov),
    }


def exceedance_clustering(losses: np.ndarray, var_forecasts: np.ndarray) -> float:
    """
    Measure of violation clustering: ratio of consecutive violations
    to total violations. Lower is better (more independent).

    Returns 0.0 if fewer than 2 violations.
    """
    violations = (losses > var_forecasts).astype(int)
    total = violations.sum()
    if total < 2:
        return 0.0
    consecutive = np.sum(violations[1:] * violations[:-1])
    return float(consecutive / (total - 1))


def average_buffer_width(var_forecasts: np.ndarray,
                         base_forecasts: np.ndarray) -> float:
    """Average absolute calibration buffer (conservativeness measure)."""
    return float(np.mean(np.abs(var_forecasts - base_forecasts)))


def overshoot_severity(losses: np.ndarray, var_forecasts: np.ndarray) -> float:
    """
    Average severity of violations: E[L − VaR | L > VaR].
    Returns 0.0 if no violations.
    """
    mask = losses > var_forecasts
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(losses[mask] - var_forecasts[mask]))


def regime_conditional_exceedance(
    losses: np.ndarray,
    var_forecasts: np.ndarray,
    regime_labels: np.ndarray,
) -> dict[int, float]:
    """
    Exceedance rate broken down by regime label.
    Returns {regime_id: exceedance_rate}.
    """
    result = {}
    for regime in np.unique(regime_labels):
        mask = regime_labels == regime
        if mask.sum() == 0:
            continue
        result[int(regime)] = float(np.mean(losses[mask] > var_forecasts[mask]))
    return result


def compute_all_metrics(
    losses: np.ndarray,
    var_forecasts: np.ndarray,
    tail_level: float,
    base_forecasts: np.ndarray | None = None,
    regime_labels: np.ndarray | None = None,
) -> dict:
    """Compute the full metrics suite and return as a flat dict."""
    metrics = {}
    metrics["exceedance_rate"] = exceedance_rate(losses, var_forecasts)
    metrics["exceedance_deviation"] = exceedance_deviation(losses, var_forecasts, tail_level)

    kup = kupiec_test(losses, var_forecasts, tail_level)
    metrics["kupiec_stat"] = kup["statistic"]
    metrics["kupiec_pval"] = kup["p_value"]

    chris = christoffersen_test(losses, var_forecasts, tail_level)
    metrics["christoffersen_stat"] = chris["statistic"]
    metrics["christoffersen_pval"] = chris["p_value"]

    metrics["clustering"] = exceedance_clustering(losses, var_forecasts)
    metrics["overshoot_severity"] = overshoot_severity(losses, var_forecasts)

    if base_forecasts is not None:
        metrics["avg_buffer_width"] = average_buffer_width(var_forecasts, base_forecasts)

    if regime_labels is not None:
        rc = regime_conditional_exceedance(losses, var_forecasts, regime_labels)
        for k, v in rc.items():
            metrics[f"exceedance_regime_{k}"] = v

    return metrics
