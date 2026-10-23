# Regime-Adaptive Distribution-Free Calibration for Financial Tail Risk

A model-agnostic calibration layer for one-sided tail-risk forecasts under heavy tails, dependence, and regime shift. This project wraps any base VaR forecaster in a **weighted, one-sided, regime-aware conformal calibration layer** with a **DKW-style finite-sample inflation term**.

## Key Idea

Given a base model producing VaR forecasts q̂ₜ⁽ᵖ⁾, the calibrated forecast is:

```
q̃ₜ⁽ᵖ⁾ = q̂ₜ⁽ᵖ⁾ + bₜ⁽ᵖ⁾
```

where bₜ⁽ᵖ⁾ is a **safety buffer** learned from recent, regime-weighted calibration residuals, inflated by a finite-sample correction tied to the effective sample size.

## What's Novel

1. **One-sided tail calibration** - not symmetric prediction intervals
2. **Regime-adaptive weighting** - time-decay × regime-kernel weights
3. **Finite-sample inflation via weighted empirical-process control** - DKW-style, not heuristic
4. **Simultaneous multi-level control** - 95% and 99% VaR jointly
5. **Lightweight post-hoc wrapper** - works with *any* base risk model

## Project Structure

```
.
├── config.py                   # Global configuration
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── data.py                 # Synthetic data generators (Sim A–D) + asset profiles
│   ├── features.py             # Regime features (rolling vol, skew, kurtosis, …)
│   ├── forecasters.py          # Base VaR forecasters (HS, EWMA, GARCH-t, QR, LightGBM)
│   ├── calibration.py          # Core calibration layer + ablation variants
│   ├── metrics.py              # Kupiec, Christoffersen, clustering, overshoot, …
│   ├── backtest.py             # Rolling walk-forward backtesting engine
│   └── utils.py                # Plotting and reporting helpers
├── experiments/
│   ├── run_simulations.py      # Synthetic suite: i.i.d., GARCH, Markov, Jump-Diffusion
│   ├── run_backtest.py         # Multi-asset backtesting (synthetic profiles of SPY, QQQ, …)
│   └── run_ablations.py        # Component ablation study
├── results/                    # Output CSV tables and figures
│   └── figures/
└── paper/
    ├── preprint.pdf            # Working paper (PDF)
    ├── preprint.docx           # Working paper (DOCX source)
    ├── theory_notes.md         # Proof sketches and theoretical scaffolding
    ├── prospectus.md           # Project prospectus and motivation
    └── generate_paper.js       # Build script for the preprint .docx
```

## Installation

```bash
pip install -r requirements.txt
```

## Running Experiments

### 1. Synthetic Simulation Suite (Sections A–D)

Tests calibration under controlled DGPs: i.i.d. heavy tails, GARCH volatility clustering, Markov-switching regimes, and jump-diffusion shocks.

```bash
python experiments/run_simulations.py
```

### 2. Multi-Asset Backtest

Runs full rolling backtests on synthetic assets modelled on SPY, QQQ, IWM, GLD, TLT, BTC-USD. The GARCH and jump parameters for each ticker are hand-set in `src/data.py`; nothing is fitted to market data.

```bash
python experiments/run_backtest.py
```

### 3. Ablation Study

Isolates the marginal contribution of each calibration component.

```bash
python experiments/run_ablations.py
```

## Reproducing the Results

All experiment settings live in `config.py`: a 500-day training window, a 200-day calibration window, base forecasters refit every 50 days, 2,500 observations per synthetic scenario, 3,500 days per synthetic asset, and the HS and EWMA base forecasters. The first 200 forecast days of each run only build up residual history for the calibration window; every calibrator is then scored on the same remaining days (1,600 per scenario, 2,600 per asset).

- `run_simulations.py` writes `results/simulation_results.csv` (Table 1 of the paper).
- `run_backtest.py` writes `results/backtest_results.csv` (Table 2). Each asset is seeded from its ticker with CRC32, so reruns give identical paths.
- `run_ablations.py` writes `results/ablation_full.csv`.

To rebuild the paper, run `node paper/generate_paper.js` from the repository root (it reads the CSVs in `results/`), then convert `paper/preprint.docx` to PDF.

## October 2026 Revision

The first release had four problems that affected its numbers. All are fixed and every result has been regenerated:

1. **No calibrated forecast on the first 200 test days.** The calibration window on those days reached back before the first base forecast, so its residuals were missing. Full (DKW) produced no forecast and the metrics counted those days as non-breaches; Full+Mono silently used the uncalibrated forecast. Evaluation now starts once the calibration window is full, and a missing forecast raises an error instead of being scored.
2. **Regime features looked ahead.** The rolling features for day t included that day's return, and normalisation used full-sample statistics. Features now use returns up to t−1 and are normalised with statistics from the initial training window.
3. **Code defaults did not match the paper.** The scripts used 750/250-day windows and other series lengths; they now take the paper's settings from `config.py`.
4. **Asset backtests were not reproducible.** Seeds came from Python's `hash()`, which is salted per process; they now come from CRC32.

The headline GARCH result (99% VaR, historical simulation) moves from 2.78% → 0.67% breaches to 3.13% → 0.88% (50 and 14 breaches in 1,600 days; Kupiec p = 0.61), measured on the corrected test window.

## Known Limitations

- **The DKW term saturates.** With K = 2, δ = 0.05 and c = 1, ε = √(log(4K/δ)/(2·n_eff)) is at least 0.11 for a 200-day calibration window. That exceeds both tail masses, so the level 1 − p + ε is clamped to 1 and the calibrated forecast is the base forecast plus the largest residual in the window, apart from residuals whose regime weight is so small it vanishes in floating point. The weights act as a filter rather than shaping a quantile, and the 95% forecasts are far more conservative than their level requires.
- **The base forecasters are stale.** They are trained on a window that ends where the calibration window begins, so on a test day they use data at least 200 days old. This keeps calibration residuals out of sample but handicaps the uncalibrated baselines, EWMA especially, and part of what calibration fixes is that staleness.
- **Monotonicity pools rather than raises.** When the 95% and 99% forecasts cross, isotonic regression sets both to their average, which lowers the 95% forecast. The envelope in `paper/theory_notes.md` would only raise the 99% forecast, and only that version inherits the one-sided bounds.
- **Synthetic data only.** No experiment uses real market returns, and the asset profiles use hand-set parameters.

## Base Forecasters

| Name       | Description |
|------------|-------------|
| HS         | Historical Simulation (empirical quantile) |
| EWMA       | EWMA-Normal VaR (RiskMetrics-style) |
| GARCH-t    | GARCH(1,1) with Student-t innovations |
| QR         | Linear quantile regression on regime features |
| LightGBM   | Gradient-boosted quantile regression |

The reported experiments use HS and EWMA. GARCH-t, QR and LightGBM are implemented but not evaluated in `results/`.

## Calibration Variants (Ablation)

| Variant | Time Weights | Regime Weights | DKW Inflation | Monotonicity |
|---------|:---:|:---:|:---:|:---:|
| Uncalibrated | — | — | — | — |
| Conformal-Plain | ✗ | ✗ | ✗ | ✗ |
| Time-Weighted | ✓ | ✗ | ✗ | ✗ |
| Regime-Weighted | ✗ | ✓ | ✗ | ✗ |
| Time+Regime | ✓ | ✓ | ✗ | ✗ |
| Full (DKW) | ✓ | ✓ | ✓ | ✗ |
| Full+Mono | ✓ | ✓ | ✓ | ✓ |

## Evaluation Metrics

- **Unconditional exceedance deviation** - |empirical rate − target|
- **Kupiec LR test** - unconditional coverage
- **Christoffersen test** - conditional coverage + independence
- **Violation clustering** - ratio of consecutive violations
- **Buffer width** - average conservativeness
- **Overshoot severity** - E[L − VaR | violation]
- **Regime-conditional exceedance** - stability across market regimes (implemented, not used in the reported results)

## Theorem Program

The paper targets three main theoretical results:

1. **Weighted one-sided validity**: P(Lₜ > q̃ₜ⁽ᵖ⁾) ≤ p + ηₜ under weighted exchangeability
2. **Simultaneous multi-level control**: union-bound across K tail levels
3. **Drift robustness bound**: calibration error decomposed into empirical-process error, regime mismatch, and base-model error

## Paper

The accompanying working paper is in [`paper/preprint.pdf`](paper/preprint.pdf) (also available as `.docx`). Supporting notes:

- [`paper/theory_notes.md`](paper/theory_notes.md) — proof sketches and theoretical scaffolding
- [`paper/prospectus.md`](paper/prospectus.md) — project prospectus and motivation

## License

MIT — see [`LICENSE`](LICENSE).
