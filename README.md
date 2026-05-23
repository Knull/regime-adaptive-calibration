# Regime-Adaptive Distribution-Free Calibration for Financial Tail Risk

A model-agnostic calibration layer for one-sided tail-risk forecasts under heavy tails, dependence, and regime shift. This project wraps any base VaR forecaster in a **weighted, one-sided, regime-aware conformal calibration layer** with a **DKW-style finite-sample inflation term**.

## Key Idea

Given a base model producing VaR forecasts q̂ₜ⁽ᵖ⁾, the calibrated forecast is:

```
q̃ₜ⁽ᵖ⁾ = q̂ₜ⁽ᵖ⁾ + bₜ⁽ᵖ⁾
```

where bₜ⁽ᵖ⁾ is a **safety buffer** learned from recent, regime-weighted calibration residuals, inflated by a finite-sample correction tied to the effective sample size.

## What's Novel

1. **One-sided tail calibration** — not symmetric prediction intervals
2. **Regime-adaptive weighting** — time-decay × regime-kernel weights
3. **Finite-sample inflation via weighted empirical-process control** — DKW-style, not heuristic
4. **Simultaneous multi-level control** — 95% and 99% VaR jointly
5. **Lightweight post-hoc wrapper** — works with *any* base risk model

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

Runs full rolling backtests on synthetic assets mimicking SPY, QQQ, IWM, GLD, TLT, BTC-USD.

```bash
python experiments/run_backtest.py
```

### 3. Ablation Study

Isolates the marginal contribution of each calibration component.

```bash
python experiments/run_ablations.py
```

## Base Forecasters

| Name       | Description |
|------------|-------------|
| HS         | Historical Simulation (empirical quantile) |
| EWMA       | EWMA-Normal VaR (RiskMetrics-style) |
| GARCH-t    | GARCH(1,1) with Student-t innovations |
| QR         | Linear quantile regression on regime features |
| LightGBM   | Gradient-boosted quantile regression |

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

- **Unconditional exceedance deviation** — |empirical rate − target|
- **Kupiec LR test** — unconditional coverage
- **Christoffersen test** — conditional coverage + independence
- **Violation clustering** — ratio of consecutive violations
- **Buffer width** — average conservativeness
- **Overshoot severity** — E[L − VaR | violation]
- **Regime-conditional exceedance** — stability across market regimes

## Theorem Program

The paper targets three main theoretical results:

1. **Weighted one-sided validity** — P(Lₜ > q̃ₜ⁽ᵖ⁾) ≤ p + ηₜ under weighted exchangeability
2. **Simultaneous multi-level control** — union-bound across K tail levels
3. **Drift robustness bound** — calibration error decomposed into empirical-process error, regime mismatch, and base-model error

## Paper

The accompanying working paper is in [`paper/preprint.pdf`](paper/preprint.pdf) (also available as `.docx`). Supporting notes:

- [`paper/theory_notes.md`](paper/theory_notes.md) — proof sketches and theoretical scaffolding
- [`paper/prospectus.md`](paper/prospectus.md) — project prospectus and motivation

## Citation

If you use this code, please cite:

```bibtex
@unpublished{mahajan2026regime,
  author = {Mahajan, Arnav},
  title  = {Regime-Adaptive Distribution-Free Calibration for Financial Tail Risk},
  year   = {2026},
  note   = {Working paper}
}
```

## License

MIT — see [`LICENSE`](LICENSE).
