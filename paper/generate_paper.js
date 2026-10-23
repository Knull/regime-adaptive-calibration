const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, LevelFormat, ExternalHyperlink,
  TabStopType, TabStopPosition,
} = require("docx");

// ─── Helpers ─────────────────────────────────────────────────────────────────

const FONT = "Times New Roman";
const CONTENT_WIDTH = 9360; // US Letter, 1" margins

function heading(level, text) {
  return new Paragraph({
    heading: level,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, font: FONT, bold: true,
      size: level === HeadingLevel.HEADING_1 ? 28 : level === HeadingLevel.HEADING_2 ? 24 : 22 })],
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, font: FONT, size: 22, ...opts })],
  });
}

function italicPara(text) {
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, font: FONT, size: 22, italics: true })],
  });
}

function mathBlock(text) {
  return new Paragraph({
    spacing: { before: 100, after: 100 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, font: "Cambria Math", size: 22, italics: true })],
  });
}

function multiRunPara(runs) {
  return new Paragraph({
    spacing: { after: 120, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
    children: runs.map(r => {
      if (typeof r === "string") return new TextRun({ text: r, font: FONT, size: 22 });
      return new TextRun({ font: FONT, size: 22, ...r });
    }),
  });
}

const border = { style: BorderStyle.SINGLE, size: 1, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };

function headerCell(text, width) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: { fill: "E8EDF2", type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, font: FONT, size: 20, bold: true })] })],
  });
}

function cell(text, width) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, font: FONT, size: 20 })] })],
  });
}

// ─── Read experiment results ────────────────────────────────────────────────
let simRows = [], btRows = [];
try {
  const simCSV = fs.readFileSync("results/simulation_results.csv", "utf-8");
  simRows = simCSV.trim().split("\n").slice(1).map(l => l.split(","));
} catch(e) {}
try {
  const btCSV = fs.readFileSync("results/backtest_results.csv", "utf-8");
  btRows = btCSV.trim().split("\n").slice(1).map(l => l.split(","));
} catch(e) {}

// ─── Document ────────────────────────────────────────────────────────────────

const children = [];

// Title
children.push(new Paragraph({
  spacing: { before: 600, after: 200 },
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Regime-Adaptive Distribution-Free Calibration", font: FONT, size: 32, bold: true })],
}));
children.push(new Paragraph({
  spacing: { after: 200 },
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "for Financial Tail Risk", font: FONT, size: 32, bold: true })],
}));
children.push(new Paragraph({
  spacing: { after: 100 },
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Working Paper, March 2026 (revised October 2026)", font: FONT, size: 22, italics: true })],
}));
children.push(new Paragraph({ spacing: { after: 400 }, children: [] }));

// ─── Abstract ────────────────────────────────────────────────────────────────
children.push(heading(HeadingLevel.HEADING_1, "Abstract"));
children.push(para(
  "We propose a model-agnostic calibration layer for one-sided tail-risk forecasts that provides finite-sample coverage guarantees under heavy tails, temporal dependence, and regime shift. Given any base Value-at-Risk (VaR) forecaster, our method computes calibration residuals, weights them by both exponential time-decay and a regime-similarity kernel derived from observable market features, and inflates the resulting weighted quantile by a correction term derived from the Dvoretzky\u2013Kiefer\u2013Wolfowitz (DKW) inequality scaled to the effective sample size. We give proof sketches for one-sided validity under weighted exchangeability, simultaneous multi-level control across tail levels via a union-bound budget, and a drift-robustness bound decomposing calibration error into weighted empirical-process error, regime mismatch, and base-model estimation error."
));
children.push(para(
  "Experiments on synthetic data (i.i.d. heavy tails, GARCH, Markov-switching regimes, jump-diffusion) and on synthetic assets modelled on SPY, QQQ, IWM, GLD, TLT, and BTC-USD show that at the 99% level the full layer moves every EWMA forecast closer to its target, brings historical simulation within the Kupiec acceptance region on all six asset profiles, and cuts historical-simulation exceedances under GARCH dynamics from 3.13% to 0.88%; where historical simulation is already close to target, calibration moves it away. At the 200-day calibration windows used here the DKW term saturates, so the calibrated forecast is close to the base forecast plus the largest calibration residual, and 95% VaR is far more conservative than required. Ablations show that time-decay weighting on its own is the best-behaved variant across both tail levels, while regime weighting without inflation increases exceedances."
));

// ─── 1. Introduction ────────────────────────────────────────────────────────
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading(HeadingLevel.HEADING_1, "1. Introduction"));
children.push(para(
  "Accurate tail-risk forecasting is a cornerstone of financial risk management. Value-at-Risk (VaR) remains the dominant metric for regulatory capital requirements and internal risk budgeting, yet its reliability depends critically on the calibration of the underlying probability model. In practice, VaR forecasts produced by parametric models (GARCH, EWMA), historical simulation, or machine-learning quantile regressors are frequently miscalibrated: they underestimate losses during market crises and overestimate them during calm regimes. This miscalibration arises from three structural sources: heavy tails in financial returns, temporal dependence and volatility clustering, and regime shifts that violate stationarity assumptions."
));
children.push(para(
  "Recent advances in conformal prediction and distribution-free inference offer a principled framework for post-hoc calibration without distributional assumptions. However, standard conformal methods assume exchangeability of calibration data, an assumption violated by financial time series exhibiting autocorrelation, volatility persistence, and structural breaks. Emerging work on temporal conformal prediction and weighted conformal inference relaxes exchangeability to weighted exchangeability, enabling calibration under non-stationarity, but existing implementations focus on symmetric prediction intervals rather than one-sided tail forecasts, and rarely incorporate regime-awareness into the weighting scheme."
));
children.push(para(
  "This paper makes the following contributions. First, we formulate a one-sided calibration layer for tail-risk forecasts that wraps any base VaR model as a lightweight post-hoc correction. Second, we introduce a regime-adaptive weighting scheme combining exponential time-decay with a kernel-based regime similarity measure computed from observable market features. Third, we derive a finite-sample inflation term based on the DKW inequality scaled to the effective sample size of the weighted calibration set, providing rigorous coverage control. Fourth, we extend the framework to simultaneous multi-level control across multiple VaR tail levels using a union-bound budget allocation. Fifth, we enforce monotonicity across tail levels via isotonic projection."
));

// ─── 2. Related Work ────────────────────────────────────────────────────────
children.push(heading(HeadingLevel.HEADING_1, "2. Related Work"));
children.push(heading(HeadingLevel.HEADING_2, "2.1 Parametric and Historical VaR"));
children.push(para(
  "The classical VaR literature spans parametric approaches (RiskMetrics EWMA, GARCH family models with Gaussian or Student-t innovations), historical simulation, and filtered historical simulation. These methods make strong distributional or stationarity assumptions that are routinely violated during market stress episodes. The Kupiec (1995) and Christoffersen (1998) backtesting frameworks remain the standard for evaluating VaR model adequacy, testing unconditional coverage and the independence of violations respectively."
));
children.push(heading(HeadingLevel.HEADING_2, "2.2 Nonparametric Quantile Intervals"));
children.push(para(
  "Order-statistic-based confidence intervals for population quantiles have a long history in nonparametric statistics. The Dvoretzky\u2013Kiefer\u2013Wolfowitz (DKW) inequality bounds the supremum deviation of the empirical CDF from the true CDF, yielding simultaneous confidence bands for all quantiles. These results assume i.i.d. data and do not directly accommodate dependence or non-stationarity."
));
children.push(heading(HeadingLevel.HEADING_2, "2.3 Conformal Prediction and Risk Control"));
children.push(para(
  "Conformal prediction provides distribution-free prediction sets with finite-sample marginal coverage guarantees under exchangeability. Split conformal prediction is computationally efficient and model-agnostic. Conformal risk control generalises conformal prediction to control arbitrary monotone loss functions. These methods have been applied to regression, classification, and survival analysis, but applications to one-sided financial tail-risk forecasting remain sparse."
));
children.push(heading(HeadingLevel.HEADING_2, "2.4 Nonstationary and Weighted Conformal Calibration"));
children.push(para(
  "Recent work extends conformal prediction to non-exchangeable settings using weighted likelihood ratios or tilted exponential weights. Temporal Conformal Prediction explicitly addresses time-series nonstationarity by adaptively weighting calibration scores. Weighted DKW-type bounds for weighted empirical CDF control provide the theoretical foundation for finite-sample guarantees in the weighted setting. Our work builds directly on this line of research, combining weighted conformal calibration with regime-awareness and DKW-based inflation for one-sided tail-risk applications."
));

// ─── 3. Problem Setup ───────────────────────────────────────────────────────
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading(HeadingLevel.HEADING_1, "3. Problem Setup"));
children.push(para(
  "Let r_t denote the daily log-return of a financial asset at time t. Define losses as L_t = \u2212r_t, so that positive L_t corresponds to a market decline. For a given tail level p (e.g., p = 0.05 for 95% VaR or p = 0.01 for 99% VaR), the one-day-ahead VaR at level 1\u2212p is the smallest threshold q such that P(L_t > q) \u2264 p."
));
children.push(para(
  "A base forecaster produces VaR estimates \u0071\u0302_t^(p) using information available at time t\u22121. The base forecaster may be parametric (GARCH, EWMA), nonparametric (historical simulation), or machine-learning-based (quantile regression, gradient-boosted quantile regression). We do not assume the base forecaster is correctly specified."
));
children.push(heading(HeadingLevel.HEADING_2, "3.1 Calibration Residuals"));
children.push(para(
  "Define calibration residuals as e_i^(p) = L_i \u2212 \u0071\u0302_i^(p). Positive residuals indicate underestimation: the actual loss exceeded the forecast. The empirical distribution of these residuals on a held-out calibration window captures the systematic bias of the base forecaster."
));
children.push(heading(HeadingLevel.HEADING_2, "3.2 Regime Features"));
children.push(para(
  "To capture market regime information without relying on proprietary data, we construct a feature vector z_t from observable return statistics: rolling 5-day and 20-day annualised volatility, rolling 20-day downside semivolatility, rolling 60-day maximum drawdown, rolling 60-day skewness, rolling 60-day excess kurtosis, and the absolute lagged return. These features are z-score normalised and clipped to avoid extreme values."
));

// ─── 4. Method ───────────────────────────────────────────────────────────────
children.push(heading(HeadingLevel.HEADING_1, "4. Method"));
children.push(heading(HeadingLevel.HEADING_2, "4.1 Weighted Calibration Weights"));
children.push(para(
  "For a test time t, we assign weights to each calibration point i combining exponential time-decay and regime similarity:"
));
children.push(mathBlock("w_{i,t} \u221D exp(\u2212\u03BB(t\u2212i)) \u00B7 exp(\u2212\u03B3 \u2016z_i \u2212 z_t\u2016\u00B2)"));
children.push(para(
  "where \u03BB controls the time-decay rate and \u03B3 controls the regime-kernel bandwidth. Weights are normalised to sum to one. The effective sample size is n_eff(t) = (\u03A3 w_i)^2 / \u03A3 w_i^2, which equals 1/\u03A3 w_i^2 for normalised weights."
));

children.push(heading(HeadingLevel.HEADING_2, "4.2 Weighted One-Sided Calibration"));
children.push(para(
  "The weighted empirical CDF of calibration residuals is \u0046\u0302_{w,t}^(p)(u) = \u03A3_i w_{i,t} \u00B7 1{e_i^(p) \u2264 u}. The calibration buffer is the weighted quantile:"
));
children.push(mathBlock("b_t^(p) = \u0046\u0302_{w,t}^{(p),\u22121}(1 \u2212 p + \u03B5_t)"));
children.push(para(
  "where \u03B5_t is a finite-sample inflation term. The calibrated forecast is \u0071\u0303_t^(p) = \u0071\u0302_t^(p) + b_t^(p)."
));

children.push(heading(HeadingLevel.HEADING_2, "4.3 DKW-Style Finite-Sample Inflation"));
children.push(para(
  "The inflation term accounts for the finite precision of the weighted empirical CDF:"
));
children.push(mathBlock("\u03B5_t = c \u00B7 \u221A(log(4K/\u03B4) / (2 \u00B7 n_eff(t)))"));
children.push(para(
  "where K is the number of simultaneous tail levels, \u03B4 is the confidence budget, and c is a safety multiplier. This term ensures that even with a small effective calibration set, the coverage guarantee degrades gracefully rather than failing silently. If \u03B5_t \u2265 p, the level 1 \u2212 p + \u03B5_t exceeds 1 and is clamped to 1, so the buffer becomes the largest calibration residual; Section 7.1 shows that the experiments in this paper operate in that regime."
));

children.push(heading(HeadingLevel.HEADING_2, "4.4 Simultaneous Multi-Level Control"));
children.push(para(
  "When monitoring multiple tail levels p_1, \u2026, p_K simultaneously, we allocate the confidence budget \u03B4 across levels via a union bound, replacing \u03B4 with \u03B4/K in the DKW term (absorbed into the log(4K/\u03B4) factor). This ensures joint control: P(\u2203k : L_t > \u0071\u0303_t^(p_k)) \u2264 \u03B4."
));

children.push(heading(HeadingLevel.HEADING_2, "4.5 Monotonicity Enforcement"));
children.push(para(
  "When forecasting at both 95% and 99% VaR, the calibrated forecasts may cross (quantile crossing). We enforce monotonicity via isotonic regression: if \u0071\u0303_99 < \u0071\u0303_95, the two values are pooled to their average, so that more extreme tail levels always produce larger VaR forecasts. Pooling raises the 99% forecast but lowers the 95% one, so it can worsen exceedance control at the less extreme level; an upper envelope that only raises the 99% forecast to the 95% one would preserve the one-sided bounds at both levels."
));

// ─── 5. Theory ───────────────────────────────────────────────────────────────
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading(HeadingLevel.HEADING_1, "5. Theoretical Guarantees"));

children.push(heading(HeadingLevel.HEADING_2, "Theorem 1 (Weighted One-Sided Validity)"));
children.push(italicPara(
  "Under weighted exchangeability of the calibration residuals (i.e., the joint distribution of (e_1, \u2026, e_n, e_{n+1}) is invariant under permutations weighted by w), the calibrated forecast satisfies:"
));
children.push(mathBlock("P(L_t > \u0071\u0303_t^(p)) \u2264 p + \u03B7_t"));
children.push(italicPara(
  "where \u03B7_t = O(n_eff(t)^{\u22121/2}) is a finite-sample correction that vanishes as the effective sample size grows."
));

children.push(heading(HeadingLevel.HEADING_2, "Theorem 2 (Simultaneous Multi-Level Control)"));
children.push(italicPara(
  "For K tail levels p_1, \u2026, p_K with the union-bound inflation \u03B5_t = c\u221A(log(4K/\u03B4) / (2n_eff(t))):"
));
children.push(mathBlock("P(\u2203 k \u2208 {1,\u2026,K} : L_t > \u0071\u0303_t^(p_k)) \u2264 \u03B4"));
children.push(italicPara(
  "This provides simultaneous coverage across all monitored tail levels with a single confidence budget."
));

children.push(heading(HeadingLevel.HEADING_2, "Theorem 3 (Drift Robustness Bound)"));
children.push(italicPara(
  "Assume the regime-conditional residual distributions satisfy d(F_t, F_s) \u2264 C\u03C1(z_t, z_s) + \u03BE|t\u2212s|, where d is a probability metric and \u03C1 is the regime-feature distance. Then the calibration error decomposes as:"
));
children.push(mathBlock("|\u0050(L_t > \u0071\u0303_t) \u2212 p| \u2264 \u03B5_weighted-empirical + \u03B5_regime-mismatch + \u03B5_base-model"));
children.push(italicPara(
  "where \u03B5_weighted-empirical is O(n_eff^{\u22121/2}), \u03B5_regime-mismatch depends on the weighted average regime distance, and \u03B5_base-model captures the base forecaster\u2019s approximation error."
));

// ─── 6. Experiments ──────────────────────────────────────────────────────────
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading(HeadingLevel.HEADING_1, "6. Experiments"));

children.push(heading(HeadingLevel.HEADING_2, "6.1 Synthetic Simulation Suite"));
children.push(para(
  "We evaluate the calibration layer under four controlled data-generating processes (DGPs), each targeting a specific challenge. Simulation A uses i.i.d. heavy-tailed innovations (Student-t with 4 degrees of freedom, and skewed-t) as a sanity check. Simulation B uses GARCH(1,1) with Student-t innovations to introduce volatility clustering. Simulation C uses a two-state Markov-switching model (calm vs. crisis regimes) with different volatility and tail thickness in each state. Simulation D uses a Merton-style jump-diffusion process with stochastic crash arrivals. For each scenario, we generate 2,500 observations and use a 500-day training window and a 200-day calibration window. Because the calibration window on each test day must be filled with residuals of forecasts made on those days, the first 200 forecast days only build up residual history; every calibrator, including the uncalibrated baseline, is then scored on the same final 1,600 days."
));

children.push(heading(HeadingLevel.HEADING_2, "6.2 Base Forecasters"));
children.push(para(
  "We employ two representative base forecasters: Historical Simulation (HS), which uses the empirical quantile of trailing losses, and Exponentially Weighted Moving Average Normal VaR (EWMA), which applies a RiskMetrics-style volatility model with a Normal quantile. Both are retrained every 50 days on the rolling training window. The training window ends where the 200-day calibration window begins, so the base forecast used on a test day is built from data that ends at least 200 days earlier. This keeps the calibration residuals out of sample, but it leaves the uncalibrated baselines stale, which matters most for EWMA."
));

children.push(heading(HeadingLevel.HEADING_2, "6.3 Calibration Variants"));
children.push(para(
  "We compare five calibration configurations: Uncalibrated (raw base forecaster), Conformal-Plain (unweighted one-sided split conformal), Time+Regime (time-decay and regime-kernel weighting without DKW inflation), Full DKW (time and regime weighting with DKW inflation), and Full+Mono (full calibration with monotonicity enforcement). This ablation design isolates the marginal contribution of each component."
));

// Results table from simulations
children.push(heading(HeadingLevel.HEADING_2, "6.4 Simulation Results"));
children.push(para(
  "Table 1 reports exceedance rates and Kupiec test p-values for the 99% VaR (p = 0.01) across all synthetic scenarios. The target exceedance rate is 1%."
));

// Build a results table from CSV data
const p99SimRows = simRows.filter(r => parseFloat(r[3]) === 0.01);
const colWidths = [1600, 1300, 1700, 1200, 1200, 1200, 1160];
if (p99SimRows.length > 0) {
  const tableRows = [
    new TableRow({ children: [
      headerCell("Scenario", colWidths[0]), headerCell("Forecaster", colWidths[1]),
      headerCell("Calibrator", colWidths[2]), headerCell("Exc. Rate", colWidths[3]),
      headerCell("Deviation", colWidths[4]), headerCell("Kupiec p", colWidths[5]),
      headerCell("Christoff. p", colWidths[6]),
    ]}),
  ];
  // Show a subset of interesting rows
  const show = p99SimRows.filter(r => 
    ["Uncalibrated","Full (DKW)","Full+Mono"].includes(r[2]) && r[1] === "HS"
  );
  for (const r of show) {
    tableRows.push(new TableRow({ children: [
      cell(r[0], colWidths[0]), cell(r[1], colWidths[1]), cell(r[2], colWidths[2]),
      cell(parseFloat(r[4]).toFixed(4), colWidths[3]),
      cell(parseFloat(r[5]).toFixed(4), colWidths[4]),
      cell(parseFloat(r[7]).toFixed(3), colWidths[5]),
      cell(parseFloat(r[9]).toFixed(3), colWidths[6]),
    ]}));
  }
  if (tableRows.length > 1) {
    children.push(new Table({
      width: { size: CONTENT_WIDTH, type: WidthType.DXA },
      columnWidths: colWidths,
      rows: tableRows,
    }));
    children.push(italicPara("Table 1: Simulation results for 99% VaR (p = 0.01), HS forecaster."));
  }
}

children.push(para(
  "With the inflation term, the 99% exceedance rates of the two full variants stay between 0.75% and 1.50% for historical simulation (HS) across the five DGPs. HS improves only in the GARCH scenario (B), where the uncalibrated forecaster breaches 3.13% of the time and Full DKW brings this to 0.88% (Kupiec p = 0.608, not rejected). In the other four scenarios uncalibrated HS is already within two breaches of the 16 that a 1% rate implies over 1,600 days, and calibration leaves it 0.06 to 0.50 pp from the target, further than before (in the Markov-switching scenario, from 0.88% to 1.25%). For EWMA, whose uncalibrated rates are higher (1.56% to 4.63%), both full variants move every scenario closer to 1% (0.81% to 1.38%). At the 95% level the full variants record 0.75% to 1.38% exceedances against a 5% target and are rejected by the Kupiec test in every scenario. Plain conformal calibration sits between the two for HS at 99% (1.00% to 2.69%), and time and regime weighting without inflation is worst (4.81% to 8.50%). Table 1 shows HS only; all variants and both forecasters are in results/simulation_results.csv."
));

// ─── 6.5 Asset Backtests ────────────────────────────────────────────────────
children.push(heading(HeadingLevel.HEADING_2, "6.5 Multi-Asset Backtest Results"));
children.push(para(
  "Table 2 reports 99% VaR backtest results on synthetic assets modelled on six major instruments. Each asset is simulated for 3,500 days (~14 years) using GARCH dynamics with jump-diffusion contamination; the GARCH and jump parameters are set by hand for each ticker rather than fitted to market data. With the same windows and warm-up as Section 6.1, each asset is scored on its final 2,600 days."
));

const p99BtRows = btRows.filter(r => parseFloat(r[3]) === 0.01);
if (p99BtRows.length > 0) {
  const btColWidths = [1400, 1300, 1700, 1200, 1200, 1200, 1360];
  const btTableRows = [
    new TableRow({ children: [
      headerCell("Asset", btColWidths[0]), headerCell("Forecaster", btColWidths[1]),
      headerCell("Calibrator", btColWidths[2]), headerCell("Exc. Rate", btColWidths[3]),
      headerCell("Deviation", btColWidths[4]), headerCell("Kupiec p", btColWidths[5]),
      headerCell("Overshoot", btColWidths[6]),
    ]}),
  ];
  const showBt = p99BtRows.filter(r =>
    ["Uncalibrated", "Full+Mono"].includes(r[2]) && r[1] === "HS"
  );
  for (const r of showBt) {
    btTableRows.push(new TableRow({ children: [
      cell(r[0], btColWidths[0]), cell(r[1], btColWidths[1]), cell(r[2], btColWidths[2]),
      cell(parseFloat(r[4]).toFixed(4), btColWidths[3]),
      cell(parseFloat(r[5]).toFixed(4), btColWidths[4]),
      cell(parseFloat(r[7]).toFixed(3), btColWidths[5]),
      cell(parseFloat(r[11]).toFixed(6), btColWidths[6]),
    ]}));
  }
  if (btTableRows.length > 1) {
    children.push(new Table({
      width: { size: CONTENT_WIDTH, type: WidthType.DXA },
      columnWidths: btColWidths,
      rows: btTableRows,
    }));
    children.push(italicPara("Table 2: Multi-asset backtest results for 99% VaR (p = 0.01), HS forecaster."));
  }
}

children.push(para(
  "Uncalibrated HS breaches 1.35% to 1.88% of the time on the six synthetic assets and passes the Kupiec test only on the IWM profile. Full+Mono brings every asset closer to the 1% target (0.69% to 1.15%) and passes the Kupiec test on all six: for the SPY profile the rate moves from 1.65% to 0.92%, and for the BTC profile from 1.62% to 1.15%. EWMA starts further away (2.69% to 4.19%) and ends at 0.50% to 1.12%, passing on five of six assets. As in the simulations, the 95% forecasts are over-corrected: the full variants record 0.54% to 1.23% exceedances against a 5% target on every asset."
));

// ─── 6.6 Ablation ───────────────────────────────────────────────────────────
children.push(heading(HeadingLevel.HEADING_2, "6.6 Ablation Analysis"));
children.push(para(
  "The ablation (results/ablation_full.csv) runs all seven calibrator variants on the GARCH and Markov-switching scenarios and the SPY and BTC asset profiles, with both base forecasters. Time-decay weighting on its own is the best-behaved variant across both tail levels: compared with plain conformal calibration it moves all eight cases closer to target at both tail levels, and it passes the Kupiec test at 95% in all eight (four of eight at 99%). Regime weighting on its own, and time and regime weighting together without inflation, raise 99% exceedances to between 4.75% and 7.92%. Adding DKW inflation brings the full variants to 0.58% to 1.38% at 99%, with Full DKW passing the Kupiec test in seven of eight cases, but at the cost of the saturation described in Section 7.1: every full variant is rejected at 95%. Monotonicity enforcement changes exceedance rates by at most 0.125 pp in these runs."
));

// ─── 7. Discussion ───────────────────────────────────────────────────────────
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading(HeadingLevel.HEADING_1, "7. Discussion"));
children.push(heading(HeadingLevel.HEADING_2, "7.1 Conservativeness vs. Responsiveness"));
children.push(para(
  "The DKW inflation term introduces deliberate conservativeness: calibrated forecasts will, on average, exceed the minimum necessary VaR. This conservativeness is largest when the effective sample size is small (during novel regimes or rapid transitions) and shrinks as more relevant calibration data accumulates. The degree of conservativeness is controlled by the constant c and the confidence budget \u03B4, offering practitioners a direct tradeoff between safety and capital efficiency."
));
children.push(para(
  "In the experiments reported here, however, the conservativeness is not a tunable margin but a hard ceiling. With K = 2, \u03B4 = 0.05 and c = 1, \u03B5_t stays above 0.05 until n_eff exceeds about 1,000 and above 0.01 until it exceeds about 25,000, while a 200-day calibration window gives n_eff \u2264 200 and therefore \u03B5_t \u2265 0.11. The inflated level 1 \u2212 p + \u03B5_t is clamped to 1 at both tail levels, and the calibrated forecast is the base forecast plus the largest residual in the window. More precisely, it is the largest residual whose weight does not vanish in floating point: residuals from very dissimilar regimes receive regime-kernel weights so small that they drop out. The weights therefore act as a filter on which residuals count rather than shaping a quantile, and the 95% forecasts end up far more conservative than their level requires (Tables 1 and 2 report only 99% VaR; the 95% results are in the repository CSVs)."
));

children.push(heading(HeadingLevel.HEADING_2, "7.2 Effective Sample Size"));
children.push(para(
  "The effective sample size n_eff serves as an automatic diagnostic: when it is low, the method signals that the current regime has few historical precedents and widens the safety buffer accordingly. This is precisely the behaviour desired in risk management: greater uncertainty should produce more conservative estimates, not less. In the current configuration this adaptivity is inactive, because ε_t saturates for every effective sample size the experiments produce (Section 7.1)."
));

children.push(heading(HeadingLevel.HEADING_2, "7.3 Limitations"));
children.push(para(
  "The current framework has several limitations. First, as Section 7.1 shows, the DKW term saturates at the window sizes used here, so the reported results reflect a largest-residual buffer rather than a calibrated quantile; a non-saturating inflation (a smaller c, a tighter bound such as Berk\u2013Jones, or larger effective samples) is needed before the weighting scheme can be judged on its own terms. Second, the base forecasters are trained on windows that end where the calibration window begins, so they are at least 200 days stale at forecast time; part of the improvement over the uncalibrated baselines is the calibration layer correcting that staleness rather than model misspecification. Third, the regime features are hand-crafted from return statistics; a learned feature representation might capture subtler regime structure. Fourth, the bandwidth parameters \u03BB and \u03B3 are set as constants rather than adapted online. Fifth, the theoretical guarantees rely on weighted exchangeability, which is an approximation to the true dependence structure of financial time series. Sixth, the present experiments use synthetic data with hand-set parameters; validation on historical market data with known crisis episodes would strengthen the empirical case."
));

// ─── 8. Conclusion ───────────────────────────────────────────────────────────
children.push(heading(HeadingLevel.HEADING_1, "8. Conclusion"));
children.push(para(
  "We have presented a regime-adaptive, distribution-free calibration layer for financial tail-risk forecasts. The method wraps any base VaR forecaster as a lightweight post-hoc correction, using weighted conformal calibration with DKW-style finite-sample inflation. Our proof sketches cover one-sided validity, simultaneous multi-level control, and drift robustness. In synthetic experiments the layer corrects stale base forecasts at the 99% level, most clearly for EWMA, for historical simulation under GARCH dynamics, and on the synthetic asset profiles. At the window sizes used here, however, the DKW term saturates, so the layer behaves like a largest-residual buffer and is far too conservative at 95%. A non-saturating inflation term, base forecasters refit on current data, and validation on historical returns are the next steps."
));
children.push(para(
  "Future work will extend the framework to Expected Shortfall (CVaR) calibration, develop adaptive bandwidth selection for the time-decay and regime-kernel parameters, and validate on historical market data spanning multiple crisis episodes."
));

// ─── References ──────────────────────────────────────────────────────────────
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading(HeadingLevel.HEADING_1, "References"));

const refs = [
  "Christoffersen, P. (1998). Evaluating interval forecasts. International Economic Review, 39(4), 841\u2013862.",
  "Dvoretzky, A., Kiefer, J., & Wolfowitz, J. (1956). Asymptotic minimax character of the sample distribution function and of the classical multinomial estimator. Annals of Mathematical Statistics, 27(3), 642\u2013669.",
  "Kupiec, P. (1995). Techniques for verifying the accuracy of risk measurement models. Journal of Derivatives, 3(2), 73\u201384.",
  "Lei, J. & Wasserman, L. (2014). Distribution-free prediction bands for non-parametric regression. Journal of the Royal Statistical Society: Series B, 76(1), 71\u201396.",
  "Massart, P. (1990). The tight constant in the Dvoretzky\u2013Kiefer\u2013Wolfowitz inequality. Annals of Probability, 18(3), 1269\u20131283.",
  "Papadopoulos, H., Proedrou, K., Vovk, V., & Gammerman, A. (2002). Inductive confidence machines for regression. European Conference on Machine Learning, 345\u2013356.",
  "Romano, Y., Patterson, E., & Cand\u00E8s, E. J. (2019). Conformalized quantile regression. NeurIPS 2019.",
  "Tibshirani, R. J., Barber, R. F., Cand\u00E8s, E. J., & Ramdas, A. (2019). Conformal prediction under covariate shift. NeurIPS 2019.",
  "Vovk, V. (2012). Conditional validity of inductive conformal predictors. Asian Conference on Machine Learning, 475\u2013490.",
  "Barber, R. F., Cand\u00E8s, E. J., Ramdas, A., & Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability. Annals of Statistics, 51(2), 816\u2013845.",
];
for (const ref of refs) {
  children.push(para(ref));
}

// ─── Appendix A: Implementation Details ─────────────────────────────────────
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(heading(HeadingLevel.HEADING_1, "Appendix A: Implementation Details"));
children.push(para(
  "All experiments are implemented in Python 3.11+ using NumPy, SciPy, pandas, scikit-learn, statsmodels, arch, and LightGBM. The backtesting engine uses a rolling walk-forward design with configurable training, calibration, and test windows. Base forecasters are retrained every 50 trading days to balance computational cost against adaptation speed. Regime features are computed from returns alone, using only returns up to the day before the forecast date, and normalised with z-scoring (means and standard deviations from the initial training window) and clipping at \u00B15 standard deviations. Synthetic assets are seeded from their tickers with CRC32, so every table can be regenerated exactly from the repository. The calibration layer is parameter-free at deployment time given fixed choices of \u03BB, \u03B3, c, and \u03B4; we use \u03BB = 0.01, \u03B3 = 1.0, c = 1.0, and \u03B4 = 0.05 throughout. The complete codebase, including all experiment scripts and this paper\u2019s generation code, is available in the project repository."
));

// ─── Appendix B: Proof Sketches ─────────────────────────────────────────────
children.push(heading(HeadingLevel.HEADING_1, "Appendix B: Proof Sketches"));
children.push(heading(HeadingLevel.HEADING_2, "B.1 Proof Sketch for Theorem 1"));
children.push(para(
  "Under weighted exchangeability, the weighted empirical CDF concentrates around the true weighted CDF at rate O(n_eff^{\u22121/2}) by the weighted DKW inequality. The one-sided calibration quantile at level 1\u2212p+\u03B5_t exceeds the true (1\u2212p)-quantile with probability at least 1\u2212\u03B4, yielding the desired coverage bound. The inflation term \u03B5_t absorbs the empirical-process fluctuation, giving P(L_t > \u0071\u0303_t^(p)) \u2264 p + \u03B7_t where \u03B7_t is controlled by the gap between \u03B5_t and the actual empirical-process deviation."
));
children.push(heading(HeadingLevel.HEADING_2, "B.2 Proof Sketch for Theorem 2"));
children.push(para(
  "For K tail levels, apply Theorem 1 to each level with confidence budget \u03B4/K. By the union bound, the probability that any level is violated is at most K \u00B7 (\u03B4/K) = \u03B4. The log(4K/\u03B4) term in the DKW inflation naturally incorporates this budget allocation."
));
children.push(heading(HeadingLevel.HEADING_2, "B.3 Proof Sketch for Theorem 3"));
children.push(para(
  "Decompose the calibration error into three terms via the triangle inequality. The first term is the weighted empirical-process error (bounded by Theorem 1). The second is the regime-mismatch term: if the true conditional distribution at time t differs from the calibration-set mixture by at most \u03B5_regime (measured by the weighted average distance C\u03A3 w_i \u03C1(z_i, z_t)), then the true quantile is perturbed by at most \u03B5_regime under standard quantile-sensitivity results. The third is the base-model error, which passes through the calibration layer as additive bias."
));

// ─── Appendix C: Revision Notes ─────────────────────────────────────────────
children.push(heading(HeadingLevel.HEADING_1, "Appendix C: Revision Notes (October 2026)"));
children.push(para(
  "The first version of this paper (March 2026) reported results affected by three problems in the experiment code, all fixed in this revision. First, on the first 200 test days the calibration window reached back before the first base forecast, so no calibrated forecast existed: the Full DKW variant's missing forecasts were scored as non-breaches, and Full+Mono silently used the uncalibrated forecast. Evaluation now begins once the calibration window is full, and every calibrator is scored on the same days. Second, the rolling regime features for day t included that day's return and were normalised over the full sample; they now use returns up to t−1 and statistics from the initial training window. Third, the synthetic asset paths were seeded non-reproducibly; they are now seeded from their tickers. In addition, the last column of Table 1 was labelled Clustering but showed the Christoffersen p-value, and the last column of Table 2 was labelled Overshoot but showed the clustering metric. All tables and figures were regenerated. The headline GARCH result changes from 2.78% to 0.67% exceedances in the first version to 3.13% to 0.88% here."
));

// ─── Build ───────────────────────────────────────────────────────────────────

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: FONT },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: FONT },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "Regime-Adaptive Calibration for Tail Risk", font: FONT, size: 18, italics: true, color: "888888" })],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Page ", font: FONT, size: 18 }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })],
        })],
      }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("paper/preprint.docx", buffer);
  console.log("Paper written to paper/preprint.docx (" + buffer.length + " bytes)");
});
