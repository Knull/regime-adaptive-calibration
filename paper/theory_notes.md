# Theory Notes: Proof Memo

## Regime-Adaptive Distribution-Free Calibration for Financial Tail Risk

This document states the assumptions, theorem sketches, and supporting lemmas for the calibration layer used in the project. It is intended as theoretical scaffolding rather than a fully polished proof appendix.

---

## Notation

- $r_t$: daily log-return at time $t$
- $L_t = -r_t$: loss, positive when the asset falls
- $p \in (0,1)$: target exceedance probability, e.g. $p=0.05$ for 95% VaR and $p=0.01$ for 99% VaR
- $\hat q_t^{(p)}$: base VaR forecast at tail level $p$
- $e_i^{(p)} = L_i - \hat q_i^{(p)}$: calibration residual
- $w_{i,t} \ge 0$: calibration weight assigned to observation $i$ when forecasting time $t$
- $\sum_{i=1}^n w_{i,t}=1$: normalized-weight convention
- $n_{\mathrm{eff}}(t)=1/\sum_{i=1}^n w_{i,t}^2$: effective sample size
- $z_t \in \mathbb{R}^d$: regime feature vector
- $\hat F_{w,t}^{(p)}(u)=\sum_{i=1}^n w_{i,t}\mathbf 1\{e_i^{(p)}\le u\}$: weighted empirical CDF of calibration residuals
- $F_{w,t}^{(p)}(u)=\sum_{i=1}^n w_{i,t}F_i^{(p)}(u)$: weighted mixture CDF, where $F_i^{(p)}$ is the conditional CDF of $e_i^{(p)}$
- $F_t^{(p)}$: target conditional CDF of the test residual $e_t^{(p)}$
- $b_t^{(p)}$: calibration buffer
- $\tilde q_t^{(p)}=\hat q_t^{(p)}+b_t^{(p)}$: calibrated VaR forecast

For $\alpha\in(0,1)$, define the left-continuous weighted empirical quantile

$$
\hat F_{w,t}^{-1}(\alpha)=\inf\{u:\hat F_{w,t}(u)\ge \alpha\}.
$$

---

## Theorem 1: Weighted One-Sided Validity

### Assumptions

1. **Fixed weights.** For a fixed test time $t$, the weights $w_{i,t}$ are treated as fixed after conditioning on the information used to construct them. They are normalized and satisfy $n_{\mathrm{eff}}(t)>0$.

2. **Weighted empirical-process control.** Conditional on the information used to fit the base model and choose the weights, the weighted empirical CDF satisfies the DKW-style concentration bound

   $$
   \Pr\left(\sup_u\left|\hat F_{w,t}^{(p)}(u)-F_{w,t}^{(p)}(u)\right|>\varepsilon\right)
   \le 2\exp\left(-2n_{\mathrm{eff}}(t)\varepsilon^2\right).
   $$

   This is a working empirical-process assumption for the weighted residual sample. It is automatic in the classical unweighted i.i.d. case, but it is not automatic for arbitrary time-series weights.

3. **Exact weighted target or bounded mismatch.** In the exact case,

   $$
   F_t^{(p)} = F_{w,t}^{(p)}.
   $$

   More generally, allow a Kolmogorov mismatch

   $$
   \Delta_t^{(p)}=\left\|F_t^{(p)}-F_{w,t}^{(p)}\right\|_\infty.
   $$

4. **Continuity at the target threshold.** $F_t^{(p)}$ has no atom at the relevant calibration threshold. With ties, use a conservative or randomized conformal quantile convention.

### Statement

For confidence level $1-\delta$, set

$$
\varepsilon_t(\delta)=\sqrt{\frac{\log(2/\delta)}{2n_{\mathrm{eff}}(t)}}.
$$

Choose the inflated buffer

$$
b_t^{(p)}=
\hat F_{w,t}^{(p),-1}\left(1-p+\varepsilon_t(\delta)+\Delta_t^{(p)}\right),
$$

with the convention that the quantile is $+\infty$ if the level exceeds $1$. Then, with probability at least $1-\delta$ over the calibration residuals,

$$
\Pr\left(L_t>\tilde q_t^{(p)}\mid \mathcal C_t\right)\le p,
$$

where $\mathcal C_t$ denotes the calibration sample and all conditioning information used to construct the weights and base model. Consequently,

$$
\Pr\left(L_t>\tilde q_t^{(p)}\right)\le p+\delta.
$$

In the exact weighted-target case $\Delta_t^{(p)}=0$, this reduces to the cleaner DKW-inflated one-sided validity statement.

### Proof Sketch

1. **Reduce to residuals.** Since $\tilde q_t^{(p)}=\hat q_t^{(p)}+b_t^{(p)}$,

   $$
   L_t>\tilde q_t^{(p)} \quad\Longleftrightarrow\quad e_t^{(p)}>b_t^{(p)}.
   $$

2. **Apply weighted empirical-process control.** With probability at least $1-\delta$,

   $$
   \left\|\hat F_{w,t}^{(p)}-F_{w,t}^{(p)}\right\|_\infty\le \varepsilon_t(\delta).
   $$

3. **Transfer the empirical quantile to the target CDF.** By definition of $b_t^{(p)}$,

   $$
   \hat F_{w,t}^{(p)}(b_t^{(p)})
   \ge
   1-p+\varepsilon_t(\delta)+\Delta_t^{(p)}.
   $$

   Therefore, on the high-probability event,

   $$
   F_{w,t}^{(p)}(b_t^{(p)})\ge 1-p+\Delta_t^{(p)}.
   $$

   Since $\|F_t^{(p)}-F_{w,t}^{(p)}\|_\infty\le \Delta_t^{(p)}$,

   $$
   F_t^{(p)}(b_t^{(p)})\ge 1-p.
   $$

4. **Convert CDF control to exceedance control.** Thus

   $$
   \Pr(e_t^{(p)}>b_t^{(p)}\mid\mathcal C_t)
   =1-F_t^{(p)}(b_t^{(p)})
   \le p.
   $$

This proves the conditional-on-calibration high-probability guarantee. Integrating over the calibration sample gives the unconditional $p+\delta$ bound.

### Needed Lemmas

- **Weighted empirical CDF concentration.** Under fixed weights and suitable independence/common-target conditions,

  $$
  \Pr\left(\sup_u\left|\hat F_w(u)-F_w(u)\right|>\varepsilon\right)
  \le 2\exp\left(-2n_{\mathrm{eff}}\varepsilon^2\right).
  $$

  The classical unweighted version is the Dvoretzky--Kiefer--Wolfowitz inequality, with Massart's sharp constant. For arbitrary weighted time-series residuals, this should be treated as an assumption or justified with a separate weighted empirical-process argument.

- **CDF-to-tail conversion.** If $F(b)\ge 1-p$, then $\Pr(X>b)\le p$ for $X\sim F$, with tie handling determined by the chosen quantile convention.

---

## Theorem 2: Simultaneous Multi-Level VaR Control

### Assumptions

The assumptions of Theorem 1 hold for each tail level $p_1,\ldots,p_K$. The same calibration sample may be reused across levels.

### Statement

Let

$$
\varepsilon_{t,K}(\delta)=\sqrt{\frac{\log(2K/\delta)}{2n_{\mathrm{eff}}(t)}}.
$$

For each $k$, choose

$$
b_t^{(p_k)}=
\hat F_{w,t}^{(p_k),-1}
\left(1-p_k+\varepsilon_{t,K}(\delta)+\Delta_t^{(p_k)}\right).
$$

Then, with probability at least $1-\delta$ over the calibration residuals, all $K$ one-sided VaR guarantees hold simultaneously:

$$
\Pr\left(L_t>\tilde q_t^{(p_k)}\mid\mathcal C_t\right)\le p_k
\quad\text{for every }k=1,\ldots,K.
$$

Equivalently,

$$
\Pr\left(\exists k:\Pr(L_t>\tilde q_t^{(p_k)}\mid\mathcal C_t)>p_k\right)\le \delta.
$$

This controls the probability that one of the level-wise guarantees fails. It does not claim that the probability of observing any VaR exceedance across levels is at most $\delta$.

### Proof Sketch

1. Apply Theorem 1 to each $p_k$ with individual failure probability $\delta/K$.
2. The empirical-process inflation becomes

   $$
   \sqrt{\frac{\log(2K/\delta)}{2n_{\mathrm{eff}}(t)}}.
   $$

3. By the union bound, the probability that any one of the $K$ level-wise guarantees fails is at most

   $$
   \sum_{k=1}^K\frac{\delta}{K}=\delta.
   $$

### Possible Improvement

A Holm--Bonferroni or step-down adjustment could produce a less conservative simultaneous guarantee when some levels have larger empirical margins. This is optional and not required for the main calibration argument.

---

## Theorem 3: Drift Robustness Bound

### Assumptions

1. **Smooth residual drift.** For each calibration point $i$ and test time $t$,

   $$
   d_{\mathrm{KS}}\left(F_i^{(p)},F_t^{(p)}\right)
   \le C\rho(z_i,z_t)+\xi |t-i|,
   $$

   where $C,\xi>0$, $\rho$ is a regime-feature distance, and $d_{\mathrm{KS}}$ is Kolmogorov--Smirnov distance.

2. **Weight concentration.** The weights concentrate on observations close to the test point in regime/time:

   $$
   \Delta_{\mathrm{regime},t}^{(p)}
   :=\sum_i w_{i,t}d_{\mathrm{KS}}(F_i^{(p)},F_t^{(p)})
   $$

   is small.

3. **Empirical-process control.** With probability at least $1-\delta$,

   $$
   \left\|\hat F_{w,t}^{(p)}-F_{w,t}^{(p)}\right\|_\infty
   \le \varepsilon_t(\delta).
   $$

4. **Base-model error on probability scale.** If $q_t^{(p),\star}$ is the oracle conditional VaR and the base model satisfies

   $$
   |\hat q_t^{(p)}-q_t^{(p),\star}|\le a_t^{(p)},
   $$

   and the conditional loss density is bounded above by $M_t$ near the relevant threshold, then the induced probability-scale error is bounded by

   $$
   \Delta_{\mathrm{base},t}^{(p)}\le M_t a_t^{(p)}.
   $$

   More generally, define $\Delta_{\mathrm{base},t}^{(p)}$ directly as the KS distance between the oracle residual CDF and the residual CDF generated using $\hat q_t^{(p)}$.

### Statement

The regime mismatch satisfies

$$
\Delta_{\mathrm{regime},t}^{(p)}
\le
C\sum_i w_{i,t}\rho(z_i,z_t)
+
\xi\sum_i w_{i,t}|t-i|.
$$

On the empirical high-probability event, the calibrated one-sided exceedance probability obeys

$$
\Pr\left(L_t>\tilde q_t^{(p)}\mid\mathcal C_t\right)
\le
p+
\Delta_{\mathrm{regime},t}^{(p)}+
\Delta_{\mathrm{base},t}^{(p)}.
$$

If the inflated buffer includes $\Delta_{\mathrm{regime},t}^{(p)}+\Delta_{\mathrm{base},t}^{(p)}$, the right-hand side reduces back to $p$ on the high-probability event. In practice, these two terms are usually unknown, so this theorem should be read as a robustness decomposition rather than a directly implementable finite-sample guarantee.

### Proof Sketch

1. **Mixture-vs-target decomposition.** By convexity of KS distance,

   $$
   \left\|F_{w,t}^{(p)}-F_t^{(p)}\right\|_\infty
   =
   \left\|\sum_i w_{i,t}F_i^{(p)}-F_t^{(p)}\right\|_\infty
   \le
   \sum_i w_{i,t}\left\|F_i^{(p)}-F_t^{(p)}\right\|_\infty.
   $$

2. **Apply the smooth-drift assumption.** Substitute

   $$
   \left\|F_i^{(p)}-F_t^{(p)}\right\|_\infty
   \le C\rho(z_i,z_t)+\xi|t-i|.
   $$

   This gives

   $$
   \Delta_{\mathrm{regime},t}^{(p)}
   \le
   C\sum_i w_{i,t}\rho(z_i,z_t)
   +
   \xi\sum_i w_{i,t}|t-i|.
   $$

3. **Combine empirical and regime errors.** On the empirical event,

   $$
   \left\|\hat F_{w,t}^{(p)}-F_t^{(p)}\right\|_\infty
   \le
   \varepsilon_t(\delta)+\Delta_{\mathrm{regime},t}^{(p)}.
   $$

4. **Include base-model residual error.** Replacing the oracle residual by the residual based on $\hat q_t^{(p)}$ adds at most $\Delta_{\mathrm{base},t}^{(p)}$ on the probability scale.

5. **Convert CDF error to one-sided exceedance control.** The same quantile argument as in Theorem 1 yields

   $$
   \Pr\left(L_t>\tilde q_t^{(p)}\mid\mathcal C_t\right)
   \le
   p+
   \Delta_{\mathrm{regime},t}^{(p)}+\Delta_{\mathrm{base},t}^{(p)}.
   $$

### Needed Lemmas

- **KS distance under mixtures.** If $F_w=\sum_i w_iF_i$ and $\sum_iw_i=1$, then

  $$
  \|F_w-F_t\|_\infty\le\sum_iw_i\|F_i-F_t\|_\infty.
  $$

- **Base-error conversion.** If $|\hat q-q^\star|\le a$ and the relevant loss density is bounded above by $M$, then shifting the residual threshold changes the exceedance probability by at most $Ma$ locally.

---

## Optional Theorem 4: Conservative Monotone Tail-Surface Consistency

### Statement

Suppose the target tail levels are ordered

$$
p_1>p_2>\cdots>p_K.
$$

For loss VaR, the calibrated forecasts should satisfy

$$
\tilde q_t^{(p_1)}\le \tilde q_t^{(p_2)}\le\cdots\le \tilde q_t^{(p_K)}.
$$

If quantile crossing occurs, define the conservative monotone envelope

$$
\bar q_t^{(p_k)}=\max_{1\le j\le k}\tilde q_t^{(p_j)},
\quad k=1,\ldots,K.
$$

Then

$$
\bar q_t^{(p_1)}\le\bar q_t^{(p_2)}\le\cdots\le\bar q_t^{(p_K)}
$$

and

$$
\bar q_t^{(p_k)}\ge \tilde q_t^{(p_k)}
\quad\text{for every }k.
$$

Therefore,

$$
\Pr(L_t>\bar q_t^{(p_k)})
\le
\Pr(L_t>\tilde q_t^{(p_k)})
\le
p_k+\eta_t^{(p_k)}.
$$

### Proof Sketch

The envelope is monotone by construction. Since it never decreases any calibrated VaR forecast, it can only reduce the exceedance probability. Therefore any one-sided validity bound satisfied by $\tilde q_t^{(p_k)}$ is preserved by $\bar q_t^{(p_k)}$.

A least-squares isotonic projection is not automatically coverage-preserving, because it may lower some forecasts. If isotonic smoothing is used, it should be constrained so that the repaired forecast is never below the original calibrated forecast at any tail level.

---

## Key References for Proofs

1. Barber, R. F., Candès, E. J., Ramdas, A., and Tibshirani, R. J. (2023). *Conformal prediction beyond exchangeability*. Annals of Statistics, 51(2), 816--845.

2. Tibshirani, R. J., Barber, R. F., Candès, E. J., and Ramdas, A. (2019). *Conformal prediction under covariate shift*. NeurIPS 2019.

3. Massart, P. (1990). *The tight constant in the Dvoretzky--Kiefer--Wolfowitz inequality*. Annals of Probability, 18(3), 1269--1283.

4. Romano, Y., Patterson, E., and Candès, E. J. (2019). *Conformalized Quantile Regression*. NeurIPS 2019.

5. Vovk, V. (2012). *Conditional validity of inductive conformal predictors*. Proceedings of the Asian Conference on Machine Learning.

6. Vovk, V., Gammerman, A., and Shafer, G. (2005). *Algorithmic Learning in a Random World*. Springer.
