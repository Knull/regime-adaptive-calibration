"""
config.py — Global configuration for Regime-Adaptive Calibration project.
"""

import os

# ─── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

for d in [RESULTS_DIR, FIGURES_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

# ─── Experiment Defaults ──────────────────────────────────────────────────────
RANDOM_SEED = 42

# Rolling backtest windows (trading days)
TRAIN_WINDOW = 750
CALIBRATION_WINDOW = 250
MIN_CALIBRATION = 100

# VaR tail levels
TAIL_LEVELS = [0.05, 0.01]          # 95% and 99% VaR

# Calibration hyper-parameters
LAMBDA_TIME_DECAY = 0.01            # Exponential time-decay rate
GAMMA_REGIME = 1.0                  # Regime-kernel bandwidth
DELTA_CONFIDENCE = 0.05             # Finite-sample confidence budget
DKW_CONSTANT = 1.0                  # Multiplier c in front of DKW epsilon

# Simulation defaults
N_SIM_SAMPLES = 2000
N_SIM_TRIALS = 5000

# Assets for real-data experiments (tickers)
ASSET_TICKERS = ["SPY", "QQQ", "IWM", "GLD", "TLT", "BTC-USD"]
