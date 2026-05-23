"""
src/data.py — Synthetic data generators and return-series utilities.

Provides four simulation scenarios plus helpers for loading / generating
realistic financial return series.
"""

import numpy as np
from scipy.stats import t as studentt, lognorm, norm


# ═══════════════════════════════════════════════════════════════════════════════
# Simulation A — i.i.d. Heavy Tails
# ═══════════════════════════════════════════════════════════════════════════════

def sim_iid_student_t(n: int, df: float = 4.0, scale: float = 0.01,
                      seed: int | None = None) -> np.ndarray:
    """i.i.d. Student-t returns (heavy tailed, symmetric)."""
    rng = np.random.default_rng(seed)
    return rng.standard_t(df, size=n) * scale


def sim_iid_skewed_t(n: int, df: float = 5.0, skew_param: float = -0.3,
                     scale: float = 0.01, seed: int | None = None) -> np.ndarray:
    """
    Skewed Student-t via a simple mixture construction:
    r = scale * (t_df + skew_param * |t_df|).
    Produces left-skewed returns when skew_param < 0.
    """
    rng = np.random.default_rng(seed)
    z = rng.standard_t(df, size=n)
    return scale * (z + skew_param * np.abs(z))


def sim_iid_lognormal(n: int, sigma: float = 1.0, mu: float = 0.0,
                      seed: int | None = None) -> np.ndarray:
    """
    i.i.d. Log-normal *losses* (always positive), returned as negative returns
    so that losses L = -r are positive.
    """
    rng = np.random.default_rng(seed)
    raw = lognorm.rvs(s=sigma, scale=np.exp(mu), size=n, random_state=rng)
    return -raw  # negative = loss


# ═══════════════════════════════════════════════════════════════════════════════
# Simulation B — GARCH(1,1) with Student-t innovations
# ═══════════════════════════════════════════════════════════════════════════════

def sim_garch_t(n: int, omega: float = 1e-6, alpha: float = 0.09,
                beta: float = 0.89, df: float = 5.0,
                seed: int | None = None) -> np.ndarray:
    """
    GARCH(1,1) with Student-t innovations.

    sigma_t^2 = omega + alpha * r_{t-1}^2 + beta * sigma_{t-1}^2
    r_t = sigma_t * z_t,  z_t ~ t(df) / sqrt(df/(df-2))
    """
    rng = np.random.default_rng(seed)
    z = rng.standard_t(df, size=n)
    z = z / np.sqrt(df / (df - 2))  # unit-variance standardisation

    r = np.zeros(n)
    sigma2 = np.zeros(n)
    sigma2[0] = omega / (1 - alpha - beta)  # unconditional variance

    for i in range(n):
        r[i] = np.sqrt(sigma2[i]) * z[i]
        if i < n - 1:
            sigma2[i + 1] = omega + alpha * r[i] ** 2 + beta * sigma2[i]

    return r


# ═══════════════════════════════════════════════════════════════════════════════
# Simulation C — Markov-Switching Volatility / Tail Regime
# ═══════════════════════════════════════════════════════════════════════════════

def sim_markov_switching(
    n: int,
    mu_low: float = 0.0003, sigma_low: float = 0.008,
    mu_high: float = -0.0005, sigma_high: float = 0.025,
    p_stay_low: float = 0.98, p_stay_high: float = 0.95,
    df_high: float = 4.0,
    seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Two-state Markov-switching model.

    State 0 (calm):  r ~ N(mu_low, sigma_low^2)
    State 1 (crisis): r ~ t(df_high)*sigma_high + mu_high

    Returns (returns, regime_labels).
    """
    rng = np.random.default_rng(seed)
    states = np.zeros(n, dtype=int)
    r = np.zeros(n)

    for i in range(1, n):
        if states[i - 1] == 0:
            states[i] = 0 if rng.random() < p_stay_low else 1
        else:
            states[i] = 1 if rng.random() < p_stay_high else 0

    for i in range(n):
        if states[i] == 0:
            r[i] = rng.normal(mu_low, sigma_low)
        else:
            z = rng.standard_t(df_high) / np.sqrt(df_high / (df_high - 2))
            r[i] = mu_high + sigma_high * z

    return r, states


# ═══════════════════════════════════════════════════════════════════════════════
# Simulation D — Jump-Diffusion / Crash Contamination
# ═══════════════════════════════════════════════════════════════════════════════

def sim_jump_diffusion(
    n: int,
    mu: float = 0.0003, sigma: float = 0.01,
    jump_intensity: float = 0.02,       # probability of jump each day
    jump_mean: float = -0.03,           # average jump size (negative = crash)
    jump_std: float = 0.04,
    seed: int | None = None,
) -> np.ndarray:
    """
    Merton-style jump-diffusion: r_t = mu + sigma*z_t + J_t * Bernoulli(lambda).
    """
    rng = np.random.default_rng(seed)
    z = rng.normal(0, 1, size=n)
    jumps = rng.binomial(1, jump_intensity, size=n)
    jump_sizes = rng.normal(jump_mean, jump_std, size=n)
    return mu + sigma * z + jumps * jump_sizes


# ═══════════════════════════════════════════════════════════════════════════════
# Synthetic "Real-Like" Asset Generator
# ═══════════════════════════════════════════════════════════════════════════════

def generate_synthetic_asset(
    name: str,
    n: int = 5000,
    seed: int | None = None,
) -> dict:
    """
    Generate a synthetic daily return series that mimics the statistical
    properties of common asset classes. Returns a dict with keys:
        'name', 'returns', 'prices', 'dates_idx'

    Profiles: equity-like, bond-like, gold-like, crypto-like.
    """
    profiles = {
        "SPY":      dict(omega=2e-6, alpha=0.08, beta=0.90, df=6, mu=3e-4,
                         ji=0.01, jm=-0.02, js=0.03),
        "QQQ":      dict(omega=3e-6, alpha=0.10, beta=0.88, df=5, mu=4e-4,
                         ji=0.012, jm=-0.025, js=0.04),
        "IWM":      dict(omega=3e-6, alpha=0.09, beta=0.89, df=5, mu=3e-4,
                         ji=0.015, jm=-0.02, js=0.035),
        "GLD":      dict(omega=1e-6, alpha=0.05, beta=0.93, df=7, mu=1e-4,
                         ji=0.008, jm=-0.01, js=0.02),
        "TLT":      dict(omega=1e-6, alpha=0.04, beta=0.94, df=8, mu=5e-5,
                         ji=0.005, jm=-0.008, js=0.015),
        "BTC-USD":  dict(omega=1e-5, alpha=0.12, beta=0.85, df=4, mu=5e-4,
                         ji=0.03, jm=-0.05, js=0.06),
    }
    p = profiles.get(name, profiles["SPY"])
    rng = np.random.default_rng(seed)

    # GARCH + jumps
    z = rng.standard_t(p["df"], size=n)
    z = z / np.sqrt(p["df"] / (p["df"] - 2))
    sigma2 = np.zeros(n)
    sigma2[0] = p["omega"] / max(1 - p["alpha"] - p["beta"], 1e-8)
    r = np.zeros(n)
    jumps = rng.binomial(1, p["ji"], size=n)
    jsizes = rng.normal(p["jm"], p["js"], size=n)

    for i in range(n):
        r[i] = p["mu"] + np.sqrt(sigma2[i]) * z[i] + jumps[i] * jsizes[i]
        if i < n - 1:
            sigma2[i + 1] = p["omega"] + p["alpha"] * r[i] ** 2 + p["beta"] * sigma2[i]

    prices = 100.0 * np.exp(np.cumsum(r))
    return {"name": name, "returns": r, "prices": prices, "dates_idx": np.arange(n)}
