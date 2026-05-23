"""
src — Regime-Adaptive Distribution-Free Calibration for Financial Tail Risk.

Modules
-------
data        Synthetic data generators and return-series utilities.
features    Regime-feature computation (rolling vol, skew, kurtosis, …).
forecasters Base VaR forecasters (HS, EWMA, GARCH-t, QR, LightGBM-QR).
calibration Core weighted one-sided conformal calibration with DKW inflation.
metrics     Risk-backtest metrics (Kupiec, Christoffersen, clustering, …).
backtest    Rolling walk-forward backtesting engine.
utils       Miscellaneous helpers.
"""
