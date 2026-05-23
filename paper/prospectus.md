# Research Prospectus
## Regime-Adaptive Distribution-Free Calibration for Financial Tail Risk

---

### Motivation

Value-at-Risk (VaR) forecasts are routinely miscalibrated under heavy tails,
volatility clustering, and regime shifts. Existing distribution-free calibration
methods (conformal prediction) assume exchangeability, which financial time series
violate. Recent work on temporal and weighted conformal prediction relaxes this
assumption but focuses on symmetric intervals rather than one-sided tail-risk
forecasts.

### Research Question

Can we build a **model-agnostic, one-sided calibration layer** for VaR forecasts
that provides **finite-sample coverage guarantees** under non-stationarity and
regime shift, while remaining **lightweight enough for real-time deployment**?

### Proposed Method

We wrap any base VaR forecaster in a **weighted one-sided conformal calibration
layer** with three key ingredients:

1. **Calibration residuals** e_i = L_i − q̂_i capture systematic forecast bias.
2. **Regime-adaptive weights** combine exponential time-decay with an RBF kernel
   on regime features (rolling vol, skew, kurtosis, drawdown) — so the calibration
   set is concentrated on historically similar market conditions.
3. **DKW-style inflation** scaled to effective sample size provides a finite-sample
   safety buffer that widens when the current regime has few precedents.

The calibrated forecast is: q̃_t = q̂_t + F̂_{w}^{−1}(1 − p + ε_t), where ε_t
depends on n_eff and the confidence budget δ.

### Theoretical Contributions

- **Theorem 1 (Validity):** P(L_t > q̃_t) ≤ p + η_t under weighted exchangeability.
- **Theorem 2 (Multi-level):** Joint coverage across 95% and 99% VaR via union bound.
- **Theorem 3 (Drift robustness):** Error decomposes into empirical-process,
  regime-mismatch, and base-model terms.

### Empirical Design

**Synthetic simulations** (4 DGPs): i.i.d. heavy tails, GARCH, Markov-switching,
jump-diffusion. **Multi-asset backtests** on synthetic profiles of SPY, QQQ, IWM,
GLD, TLT, BTC-USD. **Ablation study** isolating each calibration component.
**Evaluation**: Kupiec, Christoffersen, violation clustering, buffer width, overshoot.

### Preliminary Results

Across all synthetic scenarios, the full calibration layer reduces 99% VaR
exceedance-rate deviation by 50–90% relative to uncalibrated HS and EWMA baselines.
In the GARCH scenario, uncalibrated HS violates at 2.78% (vs. 1% target);
calibrated: 0.67%. In Markov-switching: uncalibrated 0.83%, calibrated 0.72%.
The DKW inflation is critical: without it, time+regime weighting *increases*
violations by concentrating on noisy recent data.

### Current Status

- Full codebase implemented (Python): data generators, 5 base forecasters,
  calibration layer with 7 ablation variants, rolling backtesting engine,
  comprehensive metrics suite.
- Simulation and backtest experiments complete with results and figures.
- Theorem statements and proof sketches drafted.
- Paper draft written (working-paper stage).

---

*Code and results available at: [GitHub repository link]*
