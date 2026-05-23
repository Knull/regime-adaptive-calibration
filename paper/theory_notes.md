# Theory Notes: Proof Memo
## Regime-Adaptive Distribution-Free Calibration for Financial Tail Risk

This document contains the assumptions, statements, proof skeletons, and supporting lemmas for the three main theorems.

---

## Notation

- $r_t$: daily log-return at time $t$
- $L_t = -r_t$: loss (positive when market falls)
- $p$: tail level (e.g., 0.05 or 0.01)
- $\hat{q}_t^{(p)}$: base VaR forecast
- $e_i^{(p)} = L_i - \hat{q}_i^{(p)}$: calibration residual
- $w_{i,t}$: weight for calibration point $i$ at test time $t$
- $n_{\text{eff}}(t) = 1 / \sum_i w_{i,t}^2$: effective sample size (normalized weights)
- $z_t \in \mathbb{R}^d$: regime feature vector
- $\hat{F}_{w,t}^{(p)}$: weighted empirical CDF of residuals
- $\tilde{q}_t^{(p)} = \hat{q}_t^{(p)} + b_t^{(p)}$: calibrated forecast

---

## Theorem 1: Weighted One-Sided Validity

### Assumptions

1. **(Weighted Exchangeability)** The sequence of calibration residuals $(e_1^{(p)}, \ldots, e_n^{(p)}, e_{n+1}^{(p)})$ is *weighted exchangeable* with respect to weights $w$: for any permutation $\pi$,

   $$\mathbb{P}(e_{\pi(1)}, \ldots, e_{\pi(n+1)}) = \prod_{i=1}^{n+1} w_{\pi(i),t} \cdot \mathbb{P}(e_1, \ldots, e_{n+1})$$

   This is the key assumption that replaces i.i.d. More precisely, we use the formulation from Tibshirani et al. (2019) and Barber et al. (2023): the test residual is drawn from the weighted mixture $\sum_i w_i \delta_{e_i}$ plus $w_{n+1} \delta_{e_{n+1}}$.

2. **(Continuity)** The true CDF of residuals is continuous (no atoms).

3. **(Finite Effective Sample)** $n_{\text{eff}}(t) \geq 1$.

### Statement

$$\mathbb{P}\left(L_t > \tilde{q}_t^{(p)}\right) \leq p + \eta_t$$

where

$$\eta_t = c \sqrt{\frac{\log(4K/\delta)}{2 \, n_{\text{eff}}(t)}}$$

### Proof Skeleton

1. **Reduce to residual domain.** The event $L_t > \tilde{q}_t^{(p)}$ is equivalent to $e_{t}^{(p)} > b_t^{(p)}$ where $b_t^{(p)}$ is the weighted $(1-p+\varepsilon_t)$-quantile of the calibration residuals.

2. **Apply weighted DKW inequality.** Under weighted exchangeability, the weighted empirical CDF satisfies (see Barber et al., 2023, Lemma 3):

   $$\mathbb{P}\left(\sup_u \left|\hat{F}_{w,t}(u) - F_w(u)\right| > \varepsilon\right) \leq 2 \exp\left(-2 n_{\text{eff}} \varepsilon^2\right)$$

3. **Bound the tail probability.** Since $b_t^{(p)} = \hat{F}_{w,t}^{-1}(1-p+\varepsilon_t)$ and $\|\hat{F}_{w,t} - F_w\|_\infty \leq \varepsilon_t$ with probability $\geq 1-\delta/(2K)$:

   $$F_w(b_t^{(p)}) \geq 1 - p + \varepsilon_t - \varepsilon_t = 1 - p$$

   Therefore $\mathbb{P}(e_t > b_t^{(p)}) \leq p$, giving the result. $\blacksquare$

### Needed Lemmas

- **Lemma (Weighted DKW).** Concentration of the weighted empirical CDF. Source: Barber et al. (2023), adapted from Massart (1990).
- **Lemma (Quantile sensitivity).** If $\|F - G\|_\infty \leq \varepsilon$, then $|F^{-1}(q) - G^{-1}(q)| \leq \varepsilon / \inf f$ where $f$ is the density near the quantile. Standard; see e.g. van der Vaart, Ch. 21.

---

## Theorem 2: Simultaneous Multi-Level Control

### Assumptions

Same as Theorem 1, applied to each of $K$ tail levels $p_1, \ldots, p_K$.

### Statement

$$\mathbb{P}\left(\exists k \in \{1,\ldots,K\} : L_t > \tilde{q}_t^{(p_k)}\right) \leq \delta$$

### Proof Skeleton

1. Apply Theorem 1 to each level $p_k$ with individual confidence $\delta/K$.
2. By the union bound:

   $$\mathbb{P}(\exists k : L_t > \tilde{q}_t^{(p_k)}) \leq \sum_{k=1}^K \frac{\delta}{K} = \delta$$

3. The $\log(4K/\delta)$ term in $\varepsilon_t$ absorbs the $K$ factor. $\blacksquare$

### Possible Improvement

A Holm–Bonferroni or step-down procedure could yield a sharper bound when some levels have larger margins. This is optional but would strengthen the paper.

---

## Theorem 3: Drift Robustness Bound

### Assumptions

1. **(Smooth Drift)** The regime-conditional residual CDF satisfies:

   $$d_{\text{KS}}(F_{e|z_t}, F_{e|z_s}) \leq C \rho(z_t, z_s) + \xi |t - s|$$

   where $C, \xi > 0$ are constants, $\rho$ is the feature-space distance, and $d_{\text{KS}}$ is the Kolmogorov–Smirnov distance.

2. **(Weight Concentration)** Weights $w_{i,t}$ assign mass primarily to observations with $\rho(z_i, z_t)$ small and $|t-i|$ moderate.

3. **(Base Model Regularity)** The base forecaster's conditional quantile error $|\hat{q}_t^{(p)} - q_t^{(p)}|$ is bounded by $\varepsilon_{\text{base}}$.

### Statement

$$\left|\mathbb{P}(L_t > \tilde{q}_t^{(p)}) - p\right| \leq \underbrace{\varepsilon_{\text{emp}}}_{\text{weighted empirical}} + \underbrace{\varepsilon_{\text{regime}}}_{\text{regime mismatch}} + \underbrace{\varepsilon_{\text{base}}}_{\text{model error}}$$

where:

- $\varepsilon_{\text{emp}} = O(n_{\text{eff}}^{-1/2})$
- $\varepsilon_{\text{regime}} = C \sum_i w_{i,t} \rho(z_i, z_t) + \xi \sum_i w_{i,t} |t-i|$
- $\varepsilon_{\text{base}}$ is the base model quantile estimation error.

### Proof Skeleton

1. **Triangle inequality decomposition.** Write the true exceedance probability as:

   $$\mathbb{P}(L_t > \tilde{q}_t^{(p)}) = \mathbb{P}(e_t^{(p)} > b_t^{(p)}) = 1 - F_{e_t|z_t}(b_t^{(p)})$$

2. **Compare to weighted mixture.** The calibration buffer $b_t^{(p)}$ targets the $(1-p+\varepsilon_t)$-quantile of the weighted residual mixture $\sum_i w_{i,t} F_{e_i|z_i}$. By the smooth-drift assumption:

   $$\left\|\sum_i w_{i,t} F_{e_i|z_i} - F_{e_t|z_t}\right\|_\infty \leq \varepsilon_{\text{regime}}$$

3. **Combine with empirical approximation.**

   $$\left\|\hat{F}_{w,t} - F_{e_t|z_t}\right\|_\infty \leq \varepsilon_{\text{emp}} + \varepsilon_{\text{regime}}$$

4. **Pass through base model error.** The residual $e_t = L_t - \hat{q}_t^{(p)}$ differs from the oracle residual by $\varepsilon_{\text{base}}$, which shifts the quantile by at most $\varepsilon_{\text{base}}$.

5. **Combine.** The total calibration error is bounded by the sum. $\blacksquare$

### Needed Lemmas

- **Lemma (KS distance under mixture).** A weighted mixture of CDFs is close to the target CDF if all components are close. Standard convexity argument.
- **Lemma (Quantile Lipschitz).** If the density is bounded below near the quantile, quantile perturbation is Lipschitz in CDF perturbation.

---

## Optional Theorem 4: Monotone Tail-Surface Consistency

### Statement

If $\tilde{q}_t^{(p_1)} > \tilde{q}_t^{(p_2)}$ for $p_1 > p_2$ (quantile crossing), then the isotonic projection $\bar{q}_t$ satisfies:

$$\mathbb{P}(L_t > \bar{q}_t^{(p_k)}) \leq \mathbb{P}(L_t > \tilde{q}_t^{(p_k)}) \leq p_k + \eta_t \quad \forall k$$

### Proof Sketch

Isotonic projection only increases the smaller forecast and decreases the larger one. Since the smaller forecast corresponds to the less extreme tail level (larger $p$), increasing it only makes it more conservative (lower exceedance probability). $\blacksquare$

---

## Key References for Proofs

1. Barber, Candès, Ramdas, Tibshirani (2023). *Conformal prediction beyond exchangeability.* Weighted exchangeability, weighted DKW, main framework.

2. Massart (1990). *The tight constant in the DKW inequality.* Tight DKW constant.

3. Tibshirani, Barber, Candès, Ramdas (2019). *Conformal prediction under covariate shift.* Weighted conformal prediction.

4. Romano, Patterson, Candès (2019). *Conformalized quantile regression.* Conformal quantile regression framework.

5. Vovk (2012). *Conditional validity of inductive conformal predictors.* Conditional coverage in conformal prediction.
