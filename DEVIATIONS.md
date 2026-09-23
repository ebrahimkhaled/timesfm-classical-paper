# DEVIATIONS FROM THE PRE-REGISTRATION

`PREREGISTRATION.md` is never edited after freezing. Every departure is recorded here with its
date and reason, per the rule stated in that file.

**Status — read this before the entries.** The deviations fall into two groups, and conflating
them would misrepresent the study.

**D-01 to D-03 were made BEFORE any forecast was produced.** They were triggered by inspecting the
*marginal distributions of the simulated data*, never by inspecting which method won. No accuracy
result existed at the time of those changes.

**D-04 to D-08 were made AFTER results existed**, and each says so in its own entry. D-04 is a
post-hoc robustness check. D-05 changed a test on statistical grounds (degrees of freedom), not
on the basis of which answer it gave. D-06 repaired a row-alignment bug caught by an impossible
value. D-07 removed an invalid statistic. D-08 corrected the bibliography verification. None
changed a pre-registered hypothesis, an outcome measure, or a reported comparison in a direction
favourable to any method, but they are post-result and are labelled as such rather than presented
alongside the pre-result group.

*(This header originally claimed all deviations were pre-result. That was true when D-01 to D-03
were the only entries and became false as later ones were appended; it is corrected here rather
than quietly rewritten.)*

---

## D-01 — D5 (ETS(A,A,A)): trend smoothing beta changed from 0.10 to 0.01

**Date:** 2026-09-08
**Changed:** `code/01_dgp.py`, `_d5`.

**Reason.** In ETS(A,A,A) the trend follows a random walk, `b_t = b_{t-1} + beta * e_t`, and the
level integrates it. With `beta = 0.10` and `sigma = 2`, the trend accumulates a standard deviation
of about `0.10 * 2 * sqrt(212) ≈ 2.9` over the longest series, and the doubly-integrated level
wanders far from its starting value. A diagnostic over 50 replications at n = 200 found:

- median series mean **76.9** against a nominal starting level of 100;
- median within-series SD **85.7**;
- **24.7% of all observations negative**.

Negative values make sMAPE and MAPE undefined or meaningless, and a series that swings from +137 to
−35 does not represent any measured quantity a forecaster would encounter. Published ETS fits
typically estimate beta in the range 0.001–0.05; 0.10 was an unrealistic choice on my part.

**Effect of the change.** At `beta = 0.01`: median mean 114.6, median SD 12.8, minimum 88.7,
**0% negative**. D5 remains a genuine ETS(A,A,A) process with AutoETS correctly specified — only
the trend-smoothing parameter moved, into its realistic range.

**Bearing on the result.** Neutral between the two families. Both TimesFM-3 and the classical
models see exactly the same series; nothing about the change favours either. If anything it makes
D5 *easier* for the classical models by making the trend more stable, i.e. it works against the
paper's H2 rather than for it.

---

## D-02 — D7 (logistic growth): a baseline of 20 added beneath the curve

**Date:** 2026-09-08
**Changed:** `code/01_dgp.py`, `_d7`. Now `y = 20 + 180 / (1 + exp(-r(t - t0))) + noise`
(previously `y = 200 / (1 + exp(-r(t - t0))) + noise`).

**Reason.** The logistic curve's lower asymptote was 0, so additive noise with `sigma = 3` drove the
early portion of every series below zero: **16.1% of observations were negative** across 50
replications at n = 200. The upper asymptote is unchanged at 200; only the floor moved from 0 to 20.

**Effect of the change.** 0% negative, range 13.4–205.0.

**Bearing on the result.** Neutral. The curve's shape, growth rate, inflection point and
noise level are untouched; only its vertical offset changed.

---

## D-03 — Burn-in removed from the two non-stationary generators

**Date:** 2026-09-08
**Changed:** `code/01_dgp.py`, `_d4` and `_d5`.

**Reason.** A burn-in period is only meaningful for a *stationary* process, where it lets transients
decay into the stationary regime. D4 is seasonally integrated and D5 is non-stationary in level and
trend, so applying a 300-step burn-in to the observed series merely let the level wander for 300
steps before observation began, making the nominal starting level of 100 meaningless (D5's mean
reached 2 209). This was a coding error, not a design choice.

**Fix.** In D4 the stationary component `z` is still burnt in, but the integrated series `y` is
built over exactly `n + H` steps from its seasonal seed. In D5 there is no burn-in at all; the
series starts from its stated initial state. The stationary generators (D1, D2, D9) and D3's
stationary difference process keep their burn-in, which is correct for them.

**Bearing on the result.** Neutral between families; it fixes the simulated level for both.

---

## D-04 — A median combination added as a POST-HOC robustness check

**Date:** 2026-09-08
**Added:** `code/08_robust_combination.py`, `results/table_robust_combination.csv`.

**Status: POST HOC.** Unlike D-01 to D-03, this analysis was added *after* the main results
were seen. It is reported in the paper as a robustness check and never as a pre-registered
result.

**Reason.** The pre-registered combination is the equal-weight *mean* of Theta, AutoETS and
AutoARIMA. The main results show TimesFM-3 beating it in 27 of 30 significant comparisons, and
inspection shows a plausible artefact: Theta fails catastrophically in some cells (mean MASE
4.16 on D4 at n = 200, against 0.89 for AutoARIMA), and a mean is not robust to one broken
member. A referee would reasonably object that the combination baseline was a straw man.

**What was done.** The comparison was repeated against a *median* combination of the same three
methods, which is robust to a single failing member.

**Result — the objection does not hold.** The median combination is slightly *worse* than the
mean combination (mean MASE 1.712 versus 1.656; TimesFM-3 1.439), and TimesFM-3 still wins 25
of 29 significant comparisons against it. TimesFM-3's advantage over the classical combination
is therefore not an artefact of how the combination was formed.

**Bearing on the result.** Strengthens the paper against an obvious criticism. It does not
change any pre-registered conclusion.

---

## D-05 — Real-data tier: paired Wilcoxon across series replaces per-series Diebold-Mariano

**Date:** 2026-09-08
**Changed:** `code/07b_realdata_analysis.py`.

**Reason.** `PREREGISTRATION.md` section 3.4 specified the Diebold-Mariano test with the
Harvey-Leybourne-Newbold correction for the real-data tier, reasoning that rolling-origin
evaluation yields an autocorrelated loss-differential sequence -- the setting DM is designed
for. That reasoning is correct in principle but does not fit the realised design: it uses only
**three origins per series**, so a per-series DM statistic carries 2 degrees of freedom and has
essentially no power. Reporting it as the primary test would be reporting noise.

**What is used instead.** The 1,000 M4 series are distinct series. Averaging each one's MASE
over its three origins gives 1,000 independent units, and a paired Wilcoxon signed-rank test
across them is both appropriate and well powered -- the same instrument, for the same reason, as
the simulation tier.

**Both are reported.** The paired test across series is the primary analysis; DM is reported as
a supplementary diagnostic and explicitly labelled underpowered. Nothing is hidden.

**Bearing on the result.** This changes the instrument, not the hypothesis. It was chosen on
statistical grounds (degrees of freedom) before the real-data results were computed, not by
inspecting which test gave a preferred answer.

---

## D-06 — Real-data classical forecasts were repaired after a row-alignment bug

**Date:** 2026-09-08
**Affected:** `results/realdata_classical.npz`; fix in `code/07_realdata.py`, repair in
`code/07c_repair_alignment.py`. The uncorrected arrays are retained as
`results/realdata_classical_misordered.npz`.

**What happened.** The real-data tier originally labelled its rolling windows
`unique_id = str(i)`. `statsforecast` returns rows sorted lexicographically by `unique_id`
-- "0", "1", "10", "100", "1000", ... -- while the reshape assumed numeric order. Every
classical forecast was therefore paired with the wrong window. The bug is silent: no error is
raised and the output is well formed.

**How it was caught.** The seasonal naive method came out at a mean MASE of 28.9. Seasonal naive
is essentially the MASE denominator, so its score must lie near 1 by construction; 28.9 is not a
surprising result but an impossible one. TimesFM-3 was unaffected, because `predict_batch`
preserves input order.

**The fix.** Window ids are now zero-padded (`f"{i:07d}"`), so lexicographic and numeric order
coincide. The already-computed forecasts were correct but permuted, and the permutation was known
exactly, so they were repaired by inverting it rather than refitting.

**Bearing on the result.** The corrected figures are the ones reported throughout. The
misordered arrays are kept so the correction can be audited. This is recorded here rather than
silently fixed because the pre-registration commits to logging every departure, and a reader
comparing intermediate files would otherwise find two versions with no explanation.

---

## D-07 — Diebold-Mariano dropped entirely from the real-data tier

**Date:** 2026-09-09
**Changed:** `code/07b_realdata_analysis.py` (function `dm_hln` and its call site deleted);
`results/realdata_dm.csv` removed; manuscript sections 2.3 and 5.1 rewritten.

**Supersedes part of D-05.** D-05 said DM would be "reported as a supplementary diagnostic and
explicitly labelled underpowered". That is no longer accurate and the statistic itself was wrong.

**What was wrong.** The implementation applied the Harvey-Leybourne-Newbold correction to the
cross-section of 1,000 per-series mean MASE differences. That vector is indexed by M4 series
identifier in lexicographic order, not by time, so the correction summed autocovariances across
unrelated series over an arbitrary ordering. The statistic was therefore not order-invariant: it
read -13.97 as computed, and between -18 and -23 under random permutations of the same numbers,
against -21.05 for a plain paired t-statistic. A quantity that moves by 30 to 70 percent when an
arbitrary index is reshuffled is not a test.

**Also inconsistent.** The script's docstring described a DM "over the 18 horizon steps" and its
printed heading said "UNDERPOWERED, 3 origins", while the code actually computed a well-powered
statistic at T = 1000. Three descriptions, none matching the others.

**Resolution.** The statistic is deleted rather than corrected, because there is no version of it
this design supports: three origins per series give two degrees of freedom, and across series
there is no time ordering to correct for. The manuscript now states plainly that DM is used in
neither tier and why.

**Bearing on the result.** None. No DM number ever appeared in the manuscript, and every
real-data verdict rests on the paired Wilcoxon test across the 1,000 independent series, which
was independently checked and is correct. The defect was in the reproducibility bundle and in two
sentences describing an analysis that had not been performed.

---

## D-08 — Bibliography verification rewritten; citations upgraded to versions of record

**Date:** 2026-09-09
**Changed:** `code/90_verify_refs.py` rewritten; `code/97_upgrade_citations.py` added;
`manuscript/refs.bib` updated; the reproducibility section corrected.

**What was wrong.** The manuscript claimed every DOI had been "validated directly against the
Crossref API". The checker in fact validated a hand-maintained list of DOIs held in parallel with
`refs.bib`, and the two had drifted: six DOIs actually present in the bibliography were never
checked at all. All six were arXiv DOIs, which `api.crossref.org` does not serve, so the design
could not have covered them -- including `meyer2025leakage`, the source of the 6% contamination
figure quoted in the abstract.

**Fix.** The checker now parses `refs.bib` itself, so it cannot miss an entry, and resolves each
DOI through `doi.org` content negotiation, which answers for Crossref and DataCite alike. All 30
DOIs now resolve; the five entries without one are a blog post, a code repository, a software
package, a textbook and a language manual, none of which has a DOI to cite.

**Citations upgraded at the same time.** Six works cited as preprints have appeared in venues of
record and are now cited as such: TimesFM and Moirai (ICML 2024, PMLR 235), Chronos (TMLR 2024),
GIFT-Eval (NeurIPS 2024 workshop), the calibration study (ICLR 2026) and PyTorch (NeurIPS 32).
These venues mint no DOI, so each carries a proceedings URL with the preprint identifier in a
note; putting the arXiv DOI in the `doi` field would identify the preprint rather than the
version cited. `meyer2025leakage` has no published version and remains labelled a preprint.

**Bearing on the result.** No numerical result changes. The claim about verification is now true
rather than approximately true.

---

## D-09 — Croston-family intermittent-demand baselines added (POST HOC)

**Date:** 2026-09-09
**Added:** `code/10_croston_d8.py`, `results/croston_d8_metrics.csv`,
`results/croston_d8_tests.csv`, `manuscript/tab_croston.tex`.

**Status: POST HOC.** Added after the main results were seen, in response to a gap identified in
review. Reported as a supplementary analysis; it does not alter the pre-registered 36-cell
comparison, whose method set is unchanged.

**Reason.** The pre-registered comparison set was chosen for the general-purpose case and
contains no method designed for intermittent demand. Since D8 carried the paper's largest
advantage for TimesFM-3, that omission left the strongest claim resting on a comparison against
methods none of which was built for the data -- a fair objection, and one the manuscript had
conceded rather than closed.

**What was added.** Six intermittent-demand methods from `statsforecast`: CrostonClassic,
CrostonOptimized, CrostonSBA (Syntetos-Boylan), ADIDA, IMAPA and TSB, run on D8 at all four
lengths with the same 200 replications and the same seeds as the main study.

**Result -- it sharpens the finding in both directions.** On MASE, TimesFM-3 beats all six at all
four lengths: 24 of 24 comparisons significant after Benjamini-Hochberg correction, median ratios
0.70-0.82. On RMSSE it loses to ADIDA and Croston-SBA at every length. Adding the correct
baselines therefore strengthens the MASE claim and confirms the metric-dependence rather than
resolving it -- Croston methods target the mean demand rate, the functional squared error rewards.

**Intervals.** Croston-family methods are point forecasters. `statsforecast` can attach conformal
intervals but these require additional held-out windows that the shorter series here cannot
supply, so these baselines are scored on point metrics only. This is stated rather than worked
around, and it means the pinball-loss comparison still rests on the original method set.

**Bearing on the result.** Answers the most likely referee objection. No pre-registered result
changes.

---

## D-10 — Representativeness and robustness study added (POST HOC, after the AJS decision)

**Date:** 2026-09-23
**Added:** `code/R1_robust_dgp.py`, `code/R2_run_robust.py`, `code/R3_instance_space.py`,
`code/R4_analyse_robust.py`; outputs in `results/robust/`, `figures/fig11_instance_space.pdf`,
`figures/fig12_parameter_response.pdf`, `manuscript/tab_robust_design.tex`.

**Trigger.** The Austrian Journal of Statistics declined the paper without review. The editor
wrote that the conclusions depend heavily on the chosen settings, and that it was unclear how
representative the settings are and how robust the results are to departures from the
assumptions. This addition answers that objection directly; it was designed after every main
result was known and is labelled post hoc in the manuscript.

**What was added.**
1. *Instance space* (Kang, Hyndman and Smith-Miles 2017): four features (spectral entropy, STL trend
   and seasonal strength, ACF1 of differences) for the simulated series at n = 96 and the 1,000 M4
   Monthly series (last 96 observations). Coverage of M4: fixed design 56%, randomised design 81%.
2. *Randomised parameters*: every series draws its own parameters from wide uniform ranges that
   contain the fixed values; 100 replications per (DGP, length); seeds 7e8 + ..., disjoint from the
   main study.
3. *Departures*: Student-t(3) innovations (negative-binomial sizes for D8); 3% additive outliers in
   the context only; seasonal period estimated by the M4 90% ACF test (applied when n >= 3m) for
   the classical methods. The four versions share parameter draws and innovations (paired).

**Result.** Four of the five headline conclusions hold in every version (AutoARIMA's seasonal
advantage weakens to 2 of 3 lengths and 6% with outliers). TimesFM-3's worst ratio to the
cell-best rises from 1.31 to 1.45-1.51 (worst cells on D7); the smallest worst ratio of any
classical method is 2.16-2.29 (1.60 with an estimated period). The two-cycle collapse of AutoETS
shrinks to 1.96-2.14x seasonal naive and vanishes (1.00) when the period is estimated, because no
seasonal model is fitted below three cycles.

**Operational note.** The first run crashed (BrokenProcessPool, "paging file is too small") with 22
workers; it resumed from its cache with `--n-jobs 12` and completed in 42 minutes.

**Bearing on the result.** No pre-registered result changes. The manuscript's statement that the
results are conditional on the fixed parameter values is replaced by this evidence.

---

## D-11 — Oracle ARIMA baseline (POST HOC, logged retrospectively)

**Date of analysis:** 2026-09-14 (results file); **logged and made reproducible:** 2026-09-23.
**Script:** `code/N6_oracle_arima.py`; output `results/oracle_arima_results.csv` (the 2026-09-14 file
is kept as `oracle_arima_results_2026-09-14.csv`).

**What it is.** For the ARIMA-family processes D1-D4, an ARIMA model with the TRUE orders is fitted
by Gaussian maximum likelihood (statsmodels `ARIMA`, default settings; D3 fitted as ARMA(1,1) with
a constant on the first differences and integrated back), so only the parameters are estimated. It
isolates the cost of AutoARIMA's order selection.

**Why it is logged here.** The analysis was added after results existed, while the manuscript was
being revised for the Austrian Journal of Statistics, and its script was not kept in `code/`. A
simulated referee report for the Journal of Forecasting found the gap. The new script reproduces
the 2026-09-14 table exactly in all 16 cells. At D4, n = 24 (two seasonal cycles), the optimiser
reports non-convergence in 156 of 200 fits; the fits are used as returned and the count is reported.

**Bearing on the result.** Post hoc and descriptive; no pre-registered result changes.

---

## D-12 — Analyses added in response to referee reports for the Journal of Forecasting (POST HOC)

**Date:** 2026-09-23. All designed after every earlier result was known; all labelled post hoc.

1. More foundation models (`N1`): TimesFM-2.5 and Chronos-Bolt-base, zero-shot; and TimesFM-3 with
   the settings of the developers' benchmark evaluator (symmetric averaging, positivity), which
   differ from the `predict_batch` defaults used in the main study. Output audit of TimesFM-3:
   quantile array (h, 9), point forecast = median decile exactly, crossing share reported.
2. More classical benchmarks (`N2`): Dynamic Optimised Theta, the M4 Comb benchmark, an
   AutoETS/AutoARIMA/DOTM combination, the all-zero forecast on D8, and split-conformal intervals
   for AutoARIMA and AutoETS (n >= 96).
3. M4 official test period (`N3`): OWA against the official Naive2, Friedman-Nemenyi/MCB, and a
   context-truncation experiment (last 24/48/96 observations).
4. Extended evaluation of the main design (`N4`): Monte Carlo standard errors, bootstrap intervals
   for the cell-level summaries, paired median ratios, per-regime Nemenyi ranks, cluster-bootstrap
   coverage MCSE, bias and PIS on D8, mean-of-deciles point forecasts for TimesFM-3.
5. Seasonal covariates for TimesFM-3 on D4/D5 (`N5 --cov`).
6. Robustness study (D-10) revised: 200 replications per cell (was 100); heavy-tailed innovations
   built from the same normal draws as the Gaussian version (common random numbers; previously an
   independent stream, so that version was paired in parameters only); BH family per (version,
   opponent) as in the main design; bootstrap intervals and a response-surface regression (`R5`).
7. Instance space (D-10) corrected: M4 series now cut from their TRAINING period only (the first
   version's last-96 window included the official 18-month test period), and standardisation
   uses the M4 series only. Coverage changed from 56%/81% to 48.5%/75.8% (fixed/randomised design).
   Sensitivity to threshold, length, feature set and sample size added (`R6`).

**Bearing on the result.** None of these changes a pre-registered hypothesis or outcome measure.
The two corrections in items 6 and 7 fix defects found in the post-hoc D-10 analysis itself.

---

## D-13 — Second referee round: diagnostics, corrected interpretations, one analysis withdrawn (POST HOC)

**Date:** 2026-09-23. Four fresh simulated reviewers (forecasting methods, simulation design, foundation
models, numbers audit) read the shortened JoF manuscript. Everything below is post hoc and labelled so.

1. **History benchmarks on D8** (`L1_round2_analyses.py`): the mean of the context as point forecast and its
   empirical deciles as predictive distribution. They match or beat TimesFM-3 on RMSSE and on the pinball
   loss at every length (SPL 0.282-0.314 vs 0.288-0.325). The earlier statement that TimesFM-3's
   distribution is "about 15% better" held only against the classical methods' Gaussian quantiles; the
   abstract, Section 5.4, discussion and conclusion now say that TimesFM-3 shows no advantage over simple
   history-based benchmarks on D8.
2. **Worst-ratio diagnostics**: without the two-cycle cells (D4, D5 at n = 24) TimesFM-3 1.31, AutoARIMA
   1.62; paired bootstrap (B = 2000) of the difference [0.75, 1.05]; split-half cross-fitted estimate
   1.32 (little winner's-curse bias).
3. **Model forms chosen at n = 24 given m = 12**: AutoETS seasonal in 8.5% (D4) and 0% (D5) of series,
   AutoARIMA never. The earlier wording that the classical failures came from "imposing a seasonal model
   on two cycles" was wrong and is replaced: the methods fall back to non-seasonal models.
4. **Tested-seasonality version reinterpreted** (no new runs): the classical worst ratio falls to 1.58
   because seasonal naive loses the true period at n = 24 and TimesFM-3 becomes the cell-best; AutoARIMA's
   MASE in its worst cell is unchanged (2.30). The version is renamed "tested seasonality".
5. **Interval score** (80%, scaled as MSIS) for the six methods of the main design: TimesFM-3 best in 22 of
   36 cells.
6. **Pooled BH** sensitivity (180 and 540 tests in one family): 134/115 and 132/113 significant/won.
7. **Paired-difference MCSE** TimesFM-3 vs AutoARIMA: 0.8-4.8% of the mean (median 2.1%).
8. **Response-surface SEs** now clustered by parameter draw (`R5`), replacing HC3, because the four
   versions share draws; 25 instead of 29 of 78 terms significant, no quoted effect changes.
9. **Withdrawn:** the split-conformal comparison (two calibration windows cannot give a valid 80%
   interval); removed from the paper and the Supporting Information.
10. **Theta on D4 diagnosed**: additive decomposition fails the same way (60 replications), so the
    failure is fixed seasonal indices against drifting stochastic seasonality.
11. **Timing script**: numba warm-up added before timing the classical methods; the timing and the CPU
    timing of TimesFM-3 are to be rerun when the machine is idle.

**Bearing on the result.** No pre-registered hypothesis or outcome measure changes. Items 1, 3 and 4
correct interpretations in the post-hoc material and in the abstract.

---

## D-14 — Second referee round, part 2: the remaining referee requests (POST HOC)

**Date:** 2026-09-24. Author's instruction: carry out every open referee request. All post hoc.

1. **More foundation models** (`N8`): Chronos-2 (amazon/chronos-2, 119.5M, revision 29ec376) and TiRex
   (NX-AI/TiRex, 35.3M, tirex-ts 1.4.2, revision 63c7409), package defaults; and TimesFM-2.5 with flip
   invariance and positivity OFF ("settings off"), matching the defaults of the main TimesFM-3 runs. Worst
   ratio to the best of fifteen methods: TimesFM-3 1.31, TimesFM-2.5 2.18 (settings off 2.26), TiRex 2.24,
   Chronos-2 2.75, Chronos-Bolt 3.06, AutoARIMA 2.22. `N4` now also computes an "extended fifteen" pool; the
   "original six" and "extended twelve" results reproduce exactly.
2. **Published M4 submissions** (`L3`): point forecasts of the top ten M4 entries from
   github.com/Mcompetitions/M4-methods, validated against the published M4 monthly sMAPE/MASE/OWA on all
   48,000 series. On the 1,000-series sample FFORMA 0.831, Jaganathan 0.841, Smyl 0.848, Pawlikowski 0.849
   are ahead of TimesFM-3 0.862. The MCB/Nemenyi ranking now uses one configuration per model and leaves out
   Naive2 (`N3`); ten methods are tied with the best.
3. **R `forecast` cross-check** (`L2`, forecast 9.0.2): reproduces every classical failure on D4/D5; finds one
   StatsForecast optimisation failure (AutoETS on D4 at n = 96: 2.41 vs 1.04 in R).
4. **Forest plot** (`B9`) of the per-cell pairwise effects (main-text Figure 3).
5. **Longer horizon, H = 48** (`N9`, `B10`): processes regenerated with the same seeds at length n + 48 (D7's
   inflection moves into the context at n = 200). Without D7, TimesFM-3's worst ratio is 1.31 over steps
   1-12 but 1.80 over 25-48, against AutoARIMA's 1.41; on D7 at n = 200 all foundation models forecast a
   decline from a plateau (mean MASE TimesFM-3 8.37, TimesFM-2.5 12.22, Chronos-2 5.30; seasonal naive 1.11).
   The abstract, discussion and conclusion now state that the robustness finding holds for short horizons.

**Bearing on the result.** No pre-registered outcome changes; items 2 and 5 qualify the post-hoc and
headline interpretation (the M4 standing and the horizon dependence of the robustness finding).
