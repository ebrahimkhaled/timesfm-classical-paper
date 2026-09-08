# SPEC — TimesFM-3 vs Classical Time-Series Models

**Author:** Ebrahim, E. K. (Ebrahim Khaled Ebrahim) — ORCID 0009-0006-7839-8778
Teaching Assistant, Applied Statistics, Faculty of Business, Alexandria University, Egypt
Submission email: `ebrahimkhaled@alexu.edu.eg`

**Working title:** *TimesFM-3 versus Classical Time-Series Models: A Simulation-Based Comparative Study*

**Target venue:** Austrian Journal of Statistics (AJS) — Scopus + WoS ESCI + DOAJ, **no APC**,
~24 weeks submission-to-publication. Backup: PJSOR (Scopus, SJR Q3, free).

**Created:** 2026-09-08

---

## 1. Motivation and the one defensible idea

Google Research released **TimesFM-3** on **2026-08-31**: a 330M-parameter decoder-only
time-series foundation model (TSFM), the first in the family pretrained natively for
**multivariate** forecasting, with alternating causal-temporal / full-variate attention,
non-autoregressive decoding via Contiguous Patch Masking, 16k context, and 9 output
quantiles. It reports the top average rank among pretrained foundation models on GIFT-Eval,
FEV-Bench and TIME.

The obvious paper ("is it better than ARIMA?") is crowded and, more importantly, **compromised**:
across 22 published TSFM papers using 401 datasets, only about 6% of those datasets had never
appeared in some model's pretraining corpus (Meyer et al., reported by Hyndman). Public-benchmark
wins are therefore weak evidence of genuine out-of-sample skill.

**The idea that makes this study publishable without requiring methodological novelty:**
generate the data ourselves. Under a known data-generating process (DGP),

1. TimesFM-3 provably has never seen the series (no contamination, by construction); and
2. ARIMA / ETS are **correctly specified by construction** — the classical model is the oracle.

That is the fair fight the literature keeps failing to stage, and it turns "which is better?"
into the sharper, answerable question: **how much does a foundation model lose when the
classical model is exactly right, and how much does it gain when it is not?**

## 2. Contribution (what the paper claims)

- **C1.** A contamination-free simulation comparison of TimesFM-3 against well-tuned classical
  baselines across nine DGPs, four series lengths and three horizons.
- **C2.** A quantification of the *specification-advantage gap*: the accuracy cost of using a
  330M-parameter model where a three-parameter model is correct, and the reverse.
- **C3.** A substantive real-data study (not toy data — see AJS rule C1.application) confirming
  which simulation regime real series resemble.
- **C4.** An operational decision table — accuracy, runtime, memory, interpretability and
  **licensing** — including the fact that TimesFM-3's weights are released under
  `timesfm-non-commercial-license-v1.0` and may not be used commercially or in production,
  a break from TimesFM-2.5's Apache-2.0 weights.

No claim of a new estimator, test or theory is made. This is a comparative simulation study
and will be framed as one.

## 3. Experimental design

### 3.1 Simulation tier (primary evidence)

Nine DGPs, chosen so classical models span "exactly right" to "clearly wrong":

| ID | DGP | Correctly specified by |
|---|---|---|
| D1 | AR(1), phi = 0.7 | ARIMA |
| D2 | ARMA(1,1) | ARIMA |
| D3 | ARIMA(1,1,1) with drift | ARIMA |
| D4 | Seasonal SARIMA(1,0,0)(1,1,0)_s | ARIMA |
| D5 | ETS(A,A,A) — additive trend + season | ETS |
| D6 | Local level with a structural break in mean | neither (break) |
| D7 | Logistic (nonlinear) growth with noise | neither (nonlinear) |
| D8 | Intermittent / count demand | neither (Croston territory) |
| D9 | Stochastic volatility (GARCH-like innovations) | ARIMA in mean only |

- **Lengths:** n in {24, 48, 96, 200} (the short-series regime is where classical should win).
- **Seasonal period:** s = 12 for seasonal DGPs; s = 1 otherwise.
- **Replications:** 200 per (DGP x length) cell — 9 x 4 x 200 = **7,200 series**.
- **Horizons:** h in {1, 6, 12}, forecast from a fixed origin at the end of each series;
  the true future values are generated from the same DGP path.
- **Seeding:** one seed per replication (reproducible and core-count invariant), following the
  existing project harness convention.

### 3.2 Real-data tier (secondary evidence)

A substantive public dataset, not toy data. Requirements: many series, real covariates where
possible, and documented provenance. The selection is recorded in `data/DATA_PROVENANCE.md` and
every series is explicitly flagged as **contamination-suspect** (it is likely inside TimesFM-3's
pretraining corpus), which is precisely why the simulation tier carries the primary claim.

### 3.3 Competitors

| Family | Method | Implementation |
|---|---|---|
| Foundation | TimesFM-3 (zero-shot, univariate mode) | `timesfm` 3.0.1, `google/timesfm-3.0-pytorch` |
| Foundation | TimesFM-3 with covariates (real-data tier only) | same |
| Classical | Seasonal naive | `statsforecast` |
| Classical | Theta | `statsforecast` |
| Classical | AutoETS | `statsforecast` |
| Classical | AutoARIMA | `statsforecast` |
| Classical | Simple combination (mean of Theta, ETS, ARIMA) | derived |

The combination is **mandatory, not optional**: the standing criticism of TSFM papers is that they
benchmark against de-ensembled, under-tuned classical methods. Omitting it invites the rejection.

### 3.4 Metrics

- **Point (primary):** MASE. **Secondary:** RMSSE, sMAPE.
- **MAPE:** reported in an appendix only, with an explicit note that it is undefined at zero,
  asymmetric, and will misrank D8 (intermittent). It is included because readers expect it,
  not because it is trusted.
- **Probabilistic:** CRPS (via the nine quantiles), empirical coverage and mean width of the
  80% and 90% prediction intervals.
- **Inference:** Diebold-Mariano tests with the Harvey-Leybourne-Newbold small-sample
  correction, per cell; multiplicity across cells controlled by Benjamini-Hochberg.
  **No accuracy difference is claimed without a test.**
- **Operational:** wall-clock fit+predict time, peak memory, model size, interpretability,
  licence.

## 4. Deliverables

```
paper_timesfm_classical/
  SPEC.md                  <- this file
  PREREGISTRATION.md       <- frozen before results are inspected
  manuscript/              <- AJS LaTeX (ajs.cls), refs.bib, figures
  code/                    <- simulation, forecasting, evaluation, figures
  data/                    <- real-data cache + DATA_PROVENANCE.md
  results/                 <- per-series metrics (CSV), aggregated tables
  figures/                 <- vector PDF only (AJS rule C2.graphics)
  logs/
  template/ajs-public/     <- upstream AJS class, unmodified
```

## 5. House rules adopted from the project

- **AJS style is load-bearing:** the journal states that manuscripts ignoring the style file are
  usually declined without review. `\documentclass[article]{ajs}`, Title Case for the title and
  for every reference title, lower-case subsection headings, DOIs on citations,
  **vector PDF figures only** (never PNG, and never PNG converted to PDF), LaTeX tables.
- **Build:** `pdflatex` (verified working — the upstream template compiles here in 5 pp).
- **Figure style:** serif/Times with the Okabe-Ito palette, mirroring `_ek_theme.R`, emitted as PDF.
- **Honesty (Rule D-HONEST):** the protocol is frozen in `PREREGISTRATION.md` before results are
  inspected. If the classical models win most cells, that is the paper's finding and it is
  reported as such.
- **AI-use disclosure** goes in the Acknowledgements, per the project's standard boilerplate.
- **One journal at a time.**

## 6. Phased plan

| Phase | Output | Gate |
|---|---|---|
| P0 | Environment: `timesfm` 3.0.1 + `statsforecast` installed; TimesFM-3 loads and forecasts a test series | HF licence accepted by the author |
| P1 | `PREREGISTRATION.md` frozen and hashed | before any result is looked at |
| P2 | Simulation engine: 9 DGPs, 7,200 series generated and cached | reproducible from seed |
| P3 | Forecast run: all 7 methods over all series; per-series metrics to CSV | runtime logged |
| P4 | Evaluation: aggregate tables, DM tests + BH correction | tests before prose |
| P5 | Real-data tier | provenance documented |
| P6 | Figures (vector PDF) | AJS rule C2.graphics |
| P7 | Manuscript in `ajs.cls`, compiled | referee-style self-audit |
| P8 | Submission package + arXiv preprint | tracker updated |

## 7. Known risks

- **R1.** TimesFM-3 weights are licence-gated on Hugging Face; the author must accept
  `timesfm-non-commercial-license-v1.0` on the `google/timesfm-3.0-pytorch` model page.
  *Owner: Dr. Ebrahim.*
- **R2.** 7,200 series x 7 methods is the dominant compute cost. AutoARIMA is the slow one, not
  TimesFM-3 (which batches). Mitigation: batch the TimesFM-3 inference, parallelise the classical
  methods, and cache per-cell results so the run is resumable.
- **R3.** The results may not favour a clean narrative. Mitigated by P1 and Rule D-HONEST.
- **R4.** The real-data tier is contamination-suspect by construction. This is handled by framing,
  not by pretending otherwise.
