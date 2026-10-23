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

*(Updated October 2026 after fixing a scoring bug and a feature look-ahead; see the README.)*

For EWMA, the full calibration layer (with monotonicity) cuts the 99% VaR exceedance-rate deviation by 50 to 93 percent in all five synthetic scenarios. For historical simulation (HS) the picture is mixed. In the GARCH scenario, uncalibrated HS violates at 3.13% (target: 1%) and the full layer brings it to 0.88%. That is the only synthetic scenario where HS improves: in the other four, uncalibrated HS is already within two breaches of the target over 1,600 days, and calibration moves it further away (Markov-switching: 0.88% to 1.25%). On the six synthetic asset profiles, where uncalibrated HS breaches 1.35% to 1.88% of the time, the full layer brings all six within the Kupiec acceptance region.

The DKW inflation term matters more than the weighting scheme. Without it, time-plus-regime weighting actually increases violations. With it, the weights mostly stop mattering: at 200-day calibration windows the inflation term exceeds both tail masses, the inflated quantile level is clamped to 1, and the calibrated forecast is the base forecast plus the largest residual in the window (apart from residuals whose regime weight underflows to zero). That also makes 95% VaR far too conservative: under 1.5% exceedances against a 5% target in every synthetic scenario and asset profile. Time-decay weighting on its own, without inflation, turned out to be the best-behaved variant across both tail levels in the ablation.

### Current Status

- Full codebase implemented in Python: data generators, 5 base forecasters, calibration layer with 7 ablation variants, rolling backtesting engine, metrics suite.
- Simulation and backtest experiments complete with results and figures.
- Theorem statements and proof sketches drafted.
- Working paper draft written.

### Learning Outcomes

Building this from scratch worked through several areas I had only read about before:

- **Conformal prediction beyond the symmetric case.** Most introductions present two-sided intervals. Adapting the construction to one-sided tail forecasts required rewriting the validity argument and rethinking what the calibration residual should be.
- **GARCH-t implementation.** I had used GARCH as a black box before. Writing the GARCH-t simulator myself (the conditional variance recursion, the unit-variance scaling of the t innovations, initialising at the unconditional variance) surfaced edge cases I had not considered. The GARCH-t forecaster itself is fitted by QMLE through the `arch` package rather than my own optimiser.
- **Weighted empirical processes.** The DKW inflation derivation required understanding how the effective sample size $n_{\text{eff}} = (\sum w_i)^2 / \sum w_i^2$ changes the concentration bound. This was the most mathematically demanding part of the project.
- **Backtesting discipline.** Walk-forward evaluation, train/calibration/test splits, and avoiding look-ahead leakage in feature construction were harder to get right than the modeling itself. Most of my early bugs were data-handling, not algorithmic.
- **VaR evaluation methodology.** Kupiec tests unconditional coverage. Christoffersen tests independence of violations. The two can disagree, and a model can pass one and fail the other in ways that matter for actual risk management.

### Reflections

A few things I would do differently or want to come back to:

- **The synthetic asset backtest is not a real backtest.** I generated returns calibrated to the statistical profiles of SPY, QQQ, and so on, not the actual return series. This was a deliberate choice to avoid data licensing issues, but it limits the claims I can make. A genuine out-of-sample test on real returns is the natural next step.
- **The regime features are hand-engineered.** Rolling volatility, skew, kurtosis, and drawdown are reasonable choices, but I did not test alternatives systematically. A learned regime representation, possibly from a small autoencoder or a hidden Markov model, could be a meaningful improvement.
- **The DKW bound is conservative.** It is finite-sample valid but loose, and at the window sizes I used it saturates outright: with K = 2, δ = 0.05 and c = 1, ε stays above 0.05 until the effective sample size passes about 1,000, and above 0.01 until it passes about 25,000. Tighter alternatives exist (Berk-Jones, weighted bootstrap) that I did not implement. The trade-off between sharpness and finite-sample guarantees is a real research direction.
- **The base forecasters are stale.** Each base forecaster is trained on a window that ends where the 200-day calibration window begins, so on any test day it is working from data at least 200 days old. That keeps the calibration residuals out of sample, but it handicaps the uncalibrated baselines (EWMA most of all), and part of what the calibration layer "fixes" is that staleness.
- **The regime features leaked, and the first test days were mis-scored.** In the first version the rolling features for day t included that day's return and were z-scored over the full sample, and the first 200 test days had no calibrated forecast at all (they were counted as non-breaches or fell back to the uncalibrated forecast). Both were fixed in October 2026; the results above come from the corrected code.
- **Multi-level control via union bound is wasteful.** Splitting the confidence budget across 95% and 99% VaR levels via union bound is the simple choice but throws away dependence structure between the two estimates. A joint construction would be tighter.
- **No unit tests.** I checked outputs against known reference values during development, but a proper test suite would make the project more credible and easier to extend. Adding tests is on my list.

What I take away from this project: distribution-free guarantees are achievable on financial data, but only if you accept conservative bounds, and only after you have thought carefully about which exchangeability assumption you are relaxing. The interesting research questions are about tightening the bounds while preserving the guarantees.

---

*Code and results available at: https://github.com/Knull/regime-adaptive-calibration*
