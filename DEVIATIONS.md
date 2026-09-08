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
