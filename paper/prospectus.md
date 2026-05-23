# Research Prospectus
## Regime-Adaptive Distribution-Free Calibration for Financial Tail Risk

---

### Motivation

Value-at-Risk (VaR) forecasts are routinely miscalibrated under heavy tails, volatility clustering, and regime shifts. Existing distribution-free calibration methods (conformal prediction) assume exchangeability, which financial time series violate. Recent work on temporal and weighted conformal prediction relaxes this assumption but focuses on symmetric intervals rather than one-sided tail-risk forecasts.

### Research Question

Can we build a model-agnostic, one-sided calibration layer for VaR forecasts that provides finite-sample coverage guarantees under non-stationarity and regime shift, while remaining lightweight enough for real-time deployment?

### Proposed Method

We wrap any base VaR forecaster in a weighted one-sided conformal calibration layer with three ingredients:

1. **Calibration residuals** $e_i = L_i - \hat{q}_i$ capture systematic forecast bias.
2. **Regime-adaptive weights** combine exponential time-decay with an RBF kernel on regime features (rolling volatility, skew, kurtosis, drawdown), so the calibration set is concentrated on historically similar market conditions.
3. **DKW-style inflation** scaled to effective sample size provides a finite-sample safety buffer that widens when the current regime has few precedents.

The calibrated forecast is:

$$\tilde{q}_t = \hat{q}_t + \hat{F}_w^{-1}(1 - p + \varepsilon_t)$$

where $\varepsilon_t$ depends on $n_{\text{eff}}$ and the confidence budget $\delta$.

### Theoretical Contributions

- **Theorem 1 (Validity):** $P(L_t > \tilde{q}_t) \leq p + \eta_t$ under weighted exchangeability.
- **Theorem 2 (Multi-level):** Joint coverage across 95% and 99% VaR via union bound.
- **Theorem 3 (Drift robustness):** Error decomposes into empirical-process, regime-mismatch, and base-model terms.

### Empirical Design

**Synthetic simulations** (4 DGPs): i.i.d. heavy tails, GARCH, Markov-switching, jump-diffusion.

**Multi-asset backtests** on synthetic profiles of SPY, QQQ, IWM, GLD, TLT, BTC-USD.

**Ablation study** isolating each calibration component.

**Evaluation**: Kupiec, Christoffersen, violation clustering, buffer width, overshoot severity.

### Preliminary Results

Across synthetic scenarios, the full calibration layer reduces 99% VaR exceedance-rate deviation by 50 to 90 percent relative to uncalibrated HS and EWMA baselines. In the GARCH scenario, uncalibrated HS violates at 2.78% (target: 1%); calibrated: 0.67%. In Markov-switching: uncalibrated 0.83%, calibrated 0.72%.

The DKW inflation term matters more than the weighting scheme. Without it, time-plus-regime weighting actually increases violations by concentrating on noisy recent data.

### Current Status

- Full codebase implemented in Python: data generators, 5 base forecasters, calibration layer with 7 ablation variants, rolling backtesting engine, metrics suite.
- Simulation and backtest experiments complete with results and figures.
- Theorem statements and proof sketches drafted.
- Working paper draft written.

### Learning Outcomes

Building this from scratch worked through several areas I had only read about before:

- **Conformal prediction beyond the symmetric case.** Most introductions present two-sided intervals. Adapting the construction to one-sided tail forecasts required rewriting the validity argument and rethinking what the calibration residual should be.
- **GARCH-t implementation.** I had used GARCH as a black box before. Implementing the QMLE fit, handling the degrees-of-freedom parameter, and getting the conditional variance recursion right surfaced edge cases I had not considered, especially around initialization and burn-in.
- **Weighted empirical processes.** The DKW inflation derivation required understanding how the effective sample size $n_{\text{eff}} = (\sum w_i)^2 / \sum w_i^2$ changes the concentration bound. This was the most mathematically demanding part of the project.
- **Backtesting discipline.** Walk-forward evaluation, train/calibration/test splits, and avoiding look-ahead leakage in feature construction were harder to get right than the modeling itself. Most of my early bugs were data-handling, not algorithmic.
- **VaR evaluation methodology.** Kupiec tests unconditional coverage. Christoffersen tests independence of violations. The two can disagree, and a model can pass one and fail the other in ways that matter for actual risk management.

### Reflections

A few things I would do differently or want to come back to:

- **The synthetic asset backtest is not a real backtest.** I generated returns calibrated to the statistical profiles of SPY, QQQ, and so on, not the actual return series. This was a deliberate choice to avoid data licensing issues, but it limits the claims I can make. A genuine out-of-sample test on real returns is the natural next step.
- **The regime features are hand-engineered.** Rolling volatility, skew, kurtosis, and drawdown are reasonable choices, but I did not test alternatives systematically. A learned regime representation, possibly from a small autoencoder or a hidden Markov model, could be a meaningful improvement.
- **The DKW bound is conservative.** It is finite-sample valid but loose. Tighter alternatives exist (Berk-Jones, weighted bootstrap) that I did not implement. The trade-off between sharpness and finite-sample guarantees is a real research direction.
- **Multi-level control via union bound is wasteful.** Splitting the confidence budget across 95% and 99% VaR levels via union bound is the simple choice but throws away dependence structure between the two estimates. A joint construction would be tighter.
- **No unit tests.** I checked outputs against known reference values during development, but a proper test suite would make the project more credible and easier to extend. Adding tests is on my list.

What I take away from this project: distribution-free guarantees are achievable on financial data, but only if you accept conservative bounds, and only after you have thought carefully about which exchangeability assumption you are relaxing. The interesting research questions are about tightening the bounds while preserving the guarantees.

---

*Code and results available at: [GitHub repository link]*
