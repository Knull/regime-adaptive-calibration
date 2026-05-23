"""
src/forecasters.py — Base one-step-ahead VaR forecasters.

Each forecaster conforms to:
    fit(losses_train, features_train=None) -> self
    predict(tail_level, features_new=None) -> float  (the VaR forecast)

Convention: losses L = -r  (positive when market falls).
A VaR forecast q̂ means: we expect L ≤ q̂ with probability 1 - tail_level.
"""

from __future__ import annotations
import numpy as np
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Historical Simulation
# ═══════════════════════════════════════════════════════════════════════════════

class HistoricalSimulation:
    """Non-parametric VaR: empirical quantile of trailing losses."""

    def __init__(self):
        self.losses = None

    def fit(self, losses: np.ndarray, features: Optional[np.ndarray] = None):
        self.losses = losses.copy()
        return self

    def predict(self, tail_level: float, features_new: Optional[np.ndarray] = None) -> float:
        return float(np.quantile(self.losses, 1 - tail_level))


# ═══════════════════════════════════════════════════════════════════════════════
# 2. EWMA-Normal VaR
# ═══════════════════════════════════════════════════════════════════════════════

class EWMANormalVaR:
    """
    Exponentially Weighted Moving Average volatility → Normal quantile.
    sigma_t^2 = lambda * sigma_{t-1}^2 + (1-lambda) * r_{t-1}^2
    VaR = mu + z_p * sigma_t
    """

    def __init__(self, lam: float = 0.94):
        self.lam = lam
        self.sigma2 = None
        self.mu = None

    def fit(self, losses: np.ndarray, features: Optional[np.ndarray] = None):
        self.mu = np.mean(losses)
        # Run EWMA to get final sigma2
        sigma2 = np.var(losses)
        for l in losses:
            sigma2 = self.lam * sigma2 + (1 - self.lam) * (l - self.mu) ** 2
        self.sigma2 = sigma2
        return self

    def predict(self, tail_level: float, features_new: Optional[np.ndarray] = None) -> float:
        from scipy.stats import norm
        z = norm.ppf(1 - tail_level)
        return float(self.mu + z * np.sqrt(self.sigma2))


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Student-t GARCH(1,1) VaR
# ═══════════════════════════════════════════════════════════════════════════════

class GARCHtVaR:
    """
    GARCH(1,1) with Student-t innovations, fitted via `arch` package.
    """

    def __init__(self):
        self.model_result = None
        self.forecast_var = None
        self.forecast_mu = None
        self.df = None

    def fit(self, losses: np.ndarray, features: Optional[np.ndarray] = None):
        from arch import arch_model
        # arch expects returns (mean model), we pass losses scaled to %
        am = arch_model(losses * 100, vol="Garch", p=1, q=1, dist="t",
                        mean="Constant", rescale=False)
        try:
            res = am.fit(disp="off", show_warning=False)
        except Exception:
            # Fallback: simpler model
            am = arch_model(losses * 100, vol="Garch", p=1, q=1, dist="normal",
                            mean="Constant", rescale=False)
            res = am.fit(disp="off", show_warning=False)

        self.model_result = res
        fcast = res.forecast(horizon=1)
        self.forecast_mu = float(fcast.mean.values[-1, 0]) / 100
        self.forecast_var = float(fcast.variance.values[-1, 0]) / (100 ** 2)
        params = res.params
        self.df = params.get("nu", 30)  # degrees of freedom; default large = normal
        return self

    def predict(self, tail_level: float, features_new: Optional[np.ndarray] = None) -> float:
        from scipy.stats import t as studentt, norm
        sigma = np.sqrt(self.forecast_var)
        if self.df is not None and self.df < 100:
            z = studentt.ppf(1 - tail_level, self.df)
            # Rescale for unit-variance t
            z = z / np.sqrt(self.df / (self.df - 2)) if self.df > 2 else z
        else:
            z = norm.ppf(1 - tail_level)
        return float(self.forecast_mu + z * sigma)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Linear Quantile Regression
# ═══════════════════════════════════════════════════════════════════════════════

class LinearQuantileRegression:
    """
    Quantile regression of losses on regime features.
    Uses statsmodels QuantReg.
    """

    def __init__(self):
        self.models = {}  # keyed by tail_level

    def fit(self, losses: np.ndarray, features: Optional[np.ndarray] = None):
        if features is None:
            # Fallback: just use lagged loss + intercept
            features = np.column_stack([np.ones(len(losses)), losses])
        else:
            # Remove rows with NaN
            mask = ~np.any(np.isnan(features), axis=1)
            features = features[mask]
            losses = losses[mask]
            features = np.column_stack([np.ones(len(features)), features])
        self._features = features
        self._losses = losses
        return self

    def predict(self, tail_level: float, features_new: Optional[np.ndarray] = None) -> float:
        import statsmodels.api as sm
        q = 1 - tail_level  # we want upper tail of losses
        if q not in self.models:
            mod = sm.QuantReg(self._losses, self._features)
            try:
                res = mod.fit(q=q, max_iter=1000)
            except Exception:
                # Fallback to OLS approximation
                return float(np.quantile(self._losses, q))
            self.models[q] = res.params

        params = self.models[q]
        if features_new is not None:
            x = np.concatenate([[1.0], features_new])
        else:
            x = np.concatenate([[1.0], self._features[-1, 1:]])
        return float(x @ params)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. LightGBM Quantile Regression
# ═══════════════════════════════════════════════════════════════════════════════

class LightGBMQuantileVaR:
    """
    Gradient-boosted quantile regression on regime features.
    """

    def __init__(self, n_estimators: int = 200, max_depth: int = 4):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.models = {}

    def fit(self, losses: np.ndarray, features: Optional[np.ndarray] = None):
        if features is None:
            features = np.column_stack([losses, np.arange(len(losses))])
        mask = ~np.any(np.isnan(features), axis=1)
        self._features = features[mask]
        self._losses = losses[mask]
        self.models = {}
        return self

    def predict(self, tail_level: float, features_new: Optional[np.ndarray] = None) -> float:
        import lightgbm as lgb
        q = 1 - tail_level
        if q not in self.models:
            dtrain = lgb.Dataset(self._features, label=self._losses)
            params = {
                "objective": "quantile",
                "alpha": q,
                "num_leaves": 31,
                "max_depth": self.max_depth,
                "learning_rate": 0.05,
                "n_estimators": self.n_estimators,
                "verbose": -1,
            }
            model = lgb.train(params, dtrain, num_boost_round=self.n_estimators)
            self.models[q] = model

        model = self.models[q]
        if features_new is not None:
            x = features_new.reshape(1, -1)
        else:
            x = self._features[-1:, :]
        return float(model.predict(x)[0])


# ═══════════════════════════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════════════════════════

FORECASTER_REGISTRY = {
    "HS":         HistoricalSimulation,
    "EWMA":       EWMANormalVaR,
    "GARCH-t":    GARCHtVaR,
    "QR":         LinearQuantileRegression,
    "LightGBM":   LightGBMQuantileVaR,
}


def get_forecaster(name: str, **kwargs):
    """Instantiate a base forecaster by name."""
    cls = FORECASTER_REGISTRY[name]
    return cls(**kwargs)
