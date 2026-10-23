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

# Rolling backtest windows (trading days). These are the settings behind the
# results in results/ and the working paper; changing them changes the numbers.
TRAIN_WINDOW = 500
CALIBRATION_WINDOW = 200
RETRAIN_FREQ = 50                   # Refit base forecasters every N test days
MIN_CALIBRATION = 100

# Series lengths
N_SIM_OBS = 2500                    # Synthetic DGP simulations (Sections A–D)
N_ASSET_DAYS = 3500                 # Synthetic asset backtests

# Forecasters and calibrator variants used in the reported experiments
FORECASTERS = ["HS", "EWMA"]
SIM_CALIBRATORS = ["Uncalibrated", "Conformal-Plain", "Time+Regime", "Full (DKW)", "Full+Mono"]
BACKTEST_CALIBRATORS = ["Uncalibrated", "Full (DKW)", "Full+Mono"]

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
