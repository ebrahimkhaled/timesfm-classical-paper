# PRE-REGISTRATION — TimesFM-3 vs Classical Time-Series Models

**Frozen:** 2026-09-08, before any simulation result was generated or inspected.
**Author:** Ebrahim, E. K. — Alexandria University.
**Rule:** this file is not edited after the first result is produced. Any later deviation is
recorded in a `DEVIATIONS.md`, dated, with the reason. If the classical models win most cells,
that is the finding and it is reported as such (project Rule D-HONEST).

---

## 1. Research questions

- **RQ1.** When a classical model is *correctly specified by construction*, how much accuracy does
  zero-shot TimesFM-3 give up relative to it?
- **RQ2.** When no classical model is correctly specified (breaks, nonlinearity, intermittency,
  volatility), how much does TimesFM-3 gain?
- **RQ3.** How does the answer to RQ1–RQ2 change with series length n and horizon h?
- **RQ4.** Are the two families' *interval* forecasts equally reliable (empirical coverage vs nominal)?
- **RQ5.** What are the operational costs (time, memory, licence) of each choice?

## 2. Hypotheses (stated before seeing results)

- **H1.** On D1–D5 (classical correctly specified), AutoARIMA / AutoETS attain lower MASE than
  TimesFM-3, with the gap *largest at short n* (n = 24) where the foundation model's context is
  thinnest and the parametric model's parsimony pays.
- **H2.** On D6–D8 (break, nonlinear, intermittent), TimesFM-3 attains lower MASE than every
  classical baseline.
- **H3.** On D9 (volatility), the two families are indistinguishable in the mean, but the classical
  intervals under-cover.
- **H4.** The simple combination beats every individual classical model on average, and is the
  hardest baseline for TimesFM-3 to beat.
- **H5.** Empirical coverage of the nominal 80% interval is below 80% for both families, worse for
  TimesFM-3 at longer horizons.

Hypotheses are recorded to be tested, not defended. Any that fail are reported as failing.

## 3. Design

### 3.1 Data-generating processes

Nine DGPs. Every series is generated at length `n + H` where `H = 12`; the first `n` points are the
context given to every method, and the final 12 are the held-out truth.

| ID | DGP | Parameters | Correctly specified by |
|---|---|---|---|
| D1 | AR(1) | phi = 0.7, sigma = 2, level = 100 | ARIMA |
| D2 | ARMA(1,1) | phi = 0.6, theta = 0.4, sigma = 2, level = 100 | ARIMA |
| D3 | ARIMA(1,1,1) with drift | phi = 0.5, theta = 0.3, drift = 0.3, sigma = 2 | ARIMA |
| D4 | SARIMA(1,0,0)(1,1,0)[12] | phi = 0.6, Phi = 0.5, sigma = 2 | ARIMA |
| D5 | ETS(A,A,A) | alpha = .3, beta = .1, gamma = .2, s = 12 | ETS |
| D6 | Local level with structural break | break at 0.7n, jump = 10 sigma | neither |
| D7 | Logistic growth with noise | K = 200, r = 0.08, sigma = 3 | neither |
| D8 | Intermittent demand | P(demand) = 0.3, size ~ 1 + Poisson(4) | neither |
| D9 | AR(1) with GARCH(1,1) innovations | phi = .6, omega = .1, a = .1, b = .85 | ARIMA in mean only |

- **Lengths:** n in {24, 48, 96, 200}.
- **Seasonal period:** m = 12 for D4 and D5; m = 1 otherwise.
- **Replications:** 200 per (DGP x length) cell. Total 9 x 4 x 200 = **7,200 series**.
- **Seeding:** `seed = 1_000_000 * dgp_index + 1_000 * length_index + replication`. Reproducible and
  invariant to core count and execution order.

### 3.2 Methods compared

Zero tuning is applied by hand to any method; all classical models use their automatic
order/parameter selection, which is the fair comparison.

| Key | Method | Source |
|---|---|---|
| `TimesFM3` | TimesFM-3 zero-shot, univariate | `timesfm` 3.0.1, `google/timesfm-3.0-pytorch` |
| `SeasonalNaive` | seasonal naive | `statsforecast` |
| `Theta` | standard Theta | `statsforecast` |
| `AutoETS` | automatic ETS | `statsforecast` |
| `AutoARIMA` | automatic ARIMA (Hyndman-Khandakar) | `statsforecast` |
| `Combination` | equal-weight mean of Theta, AutoETS, AutoARIMA | derived |

`Combination` is included because benchmarking a foundation model only against *de-ensembled*
classical methods is the single most-cited flaw of this literature.

### 3.3 Evaluation

**Horizon slices.** Metrics are computed over h = 1 (first step), h = 1..6, and h = 1..12.

**Point accuracy.**
- **MASE (primary).** Denominator = in-sample mean absolute error of the seasonal naive method
  on the context, with period m. Series whose denominator is 0 are dropped and the count reported.
- **RMSSE (secondary).** Squared analogue, as in the M5 competition.
- **sMAPE (secondary).**
- **MAPE (appendix only).** Reported because readers expect it, and accompanied by an explicit
  statement that it is undefined at zero, asymmetric, and unusable on D8.

**Probabilistic accuracy.**
- **Mean quantile (pinball) loss** averaged over the nine deciles q = 0.1, ..., 0.9. Both families
  supply exactly these deciles, so the comparison is like-for-like. This is a proper scoring rule
  and is reported as the quantile loss, not relabelled as CRPS.
- **Empirical coverage and mean width** of the nominal **60%** interval [q0.2, q0.8] and the
  nominal **80%** interval [q0.1, q0.9].
  *Note: 90% intervals are deliberately NOT used — TimesFM-3 emits only deciles q0.1..q0.9, so a
  90% interval is unavailable from it and any such comparison would be unequal.*

**Classical quantiles** are obtained from `statsforecast` prediction intervals at
`level = [20, 40, 60, 80]`, which map exactly onto the deciles q0.1, q0.2, q0.3, q0.4, q0.6, q0.7,
q0.8, q0.9; q0.5 is taken as the point forecast.

**Operational.** Wall-clock fit+predict seconds per series (classical) and per batch (TimesFM-3),
peak memory, and the licence status of each method.

### 3.4 Inference

- **Simulation tier.** Within each (DGP x length x horizon-slice) cell, TimesFM-3 is compared to
  each classical method by a **paired Wilcoxon signed-rank test** on the per-replication MASE
  differences, with the median difference and a Hodges-Lehmann estimate reported.
  A paired *t*-test is reported alongside as a sensitivity check.
  *Diebold-Mariano is deliberately NOT used here: replications are independent draws, not an
  autocorrelated loss-differential sequence from one series, which is what DM assumes.*
- **Real-data tier.** Rolling-origin evaluation on each series, compared with the
  **Diebold-Mariano test using the Harvey-Leybourne-Newbold small-sample correction** — the
  setting DM was designed for.
- **Multiplicity.** Benjamini-Hochberg control at FDR = 0.05 across all cells within each
  comparison family. Raw and adjusted p-values are both reported.
- **Effect size.** Every significant result is accompanied by the median MASE ratio, so that
  statistically detectable but practically irrelevant differences are visible as such.

## 4. Stopping and exclusion rules

- The replication count (200 per cell) is fixed in advance and is **not** increased after looking
  at p-values.
- Series are excluded only for a zero MASE denominator (a degenerate constant context). The number
  excluded is reported per cell.
- If a method fails to fit on a series, its failure is recorded and the series is excluded from
  that method's comparisons only, with the count reported. Failures are not silently imputed.

## 5. What would falsify the paper's framing

If TimesFM-3 matches or beats the correctly-specified classical models on D1-D5 at **all** lengths,
then the "specification advantage" framing is wrong, and the paper reports that a 330M-parameter
zero-shot model is competitive even on its opponent's home ground. That result would be reported
with the same prominence as the opposite one.
