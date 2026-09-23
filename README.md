# TimesFM-3 versus Classical Time-Series Models

A simulation-based comparison of Google's TimesFM-3 foundation model
(released 2026-08-31) against classical forecasting methods, with a real-data check on M4.

**Target venue:** Journal of Forecasting (Wiley). The manuscript for it is `manuscript_jof/`
(Wiley USG.cls); the Austrian Journal of Statistics version in `manuscript/` is kept as the record
of that earlier submission, which the journal declined on scope.

The study is exploratory: it describes how a black-box model behaves on data of known structure,
not why. All analyses added after the main results are labelled post hoc in `DEVIATIONS.md`
(D-04 to D-15).

## The idea in one paragraph

Public forecasting benchmarks cannot settle whether a foundation model beats ARIMA, because
only ~6% of the datasets used across 22 published foundation models were absent from every
model's pre-training corpus. This study generates its own data instead. Under a known DGP the
foundation model provably has not seen the series, AND the classical model is correctly
specified by construction -- so the comparison is fair in both directions at once.

## Files

| Path | What it is |
|---|---|
| `SPEC.md` | The design |
| `PREREGISTRATION.md` | Protocol frozen before any result was produced. Never edited. |
| `DEVIATIONS.md` | Every departure from the protocol, dated, with its reason |
| `manuscript_jof/` | Journal of Forecasting version (Wiley `USG.cls`): main text, supporting information, tables |
| `manuscript/` | Austrian Journal of Statistics version (`ajs.cls`), kept as submitted |
| `results/robust/` | Robustness study: randomised parameters, four departures, instance space |
| `results/revision/`, `results/fm/`, `results/classical_extra/`, `results/m4_official/` | Extended evaluation: Monte Carlo errors, further foundation models and classical benchmarks, M4 official test period |
| `code/` | Pipeline, numbered in execution order |
| `results/` | Metrics, tables, `summary.txt` |
| `figures/` | Vector PDF only (AJS rule C2.graphics) |
| `template/ajs-public/` | Upstream AJS class, unmodified |

## Pipeline

```
python code/00_smoke_test.py            # environment check
python code/01_dgp.py                   # DGP self-test
python code/02_metrics.py               # metrics self-test
python code/03_run_forecasts.py         # main run: 7,200 series x 6 methods (~11 min)
python code/04_analyse.py               # aggregation + Wilcoxon + BH
python code/05_timing_benchmark.py      # per-method operational costs
python code/06_figures.py               # vector PDF figures
python code/07_realdata.py              # M4 Monthly, rolling origin
python code/07b_realdata_analysis.py    # M4 tests
python code/07c_repair_alignment.py     # one-off repair (see trap 3); not needed on a fresh run
python code/08_robust_combination.py    # post-hoc: median combination
python code/09_make_tables.py           # LaTeX tables (enforces AJS caption placement)
python code/10_croston_d8.py            # post-hoc: Croston-family baselines on D8

# post hoc, robustness and representativeness (DEVIATIONS D-10, D-12)
python code/R2_run_robust.py --reps 200 # randomised parameters x four departures (R1 = generators)
python code/R3_instance_space.py        # instance-space coverage of M4 (Figure 11)
python code/R4_analyse_robust.py        # headline conclusions per version (Table 11, Figure 12)
python code/R5_robust_uncertainty.py    # bootstrap intervals, response surface
python code/R6_instance_sensitivity.py  # coverage sensitivity

# post hoc, extended evaluation for the Journal of Forecasting referees (D-11, D-12)
python code/N1_foundation_models.py     # TimesFM-2.5, Chronos-Bolt, TimesFM-3 evaluator settings
python code/N2_classical_extras.py      # DOTM, M4 Comb, second combination, zero forecast, conformal
python code/N3_m4_official.py           # M4 official test period, OWA, MCB, truncation
python code/N4_revision_analysis.py     # Monte Carlo errors, bootstrap, Nemenyi, D8, coverage
python code/N5_covariates_and_timing.py --cov   # seasonal covariates for TimesFM-3
python code/N6_oracle_arima.py          # Oracle ARIMA baseline (reproduces the 2026-09-14 table)
python code/N7_revision_tables.py       # LaTeX tables for manuscript_jof

# post hoc, second referee round (D-13, D-14)
python code/L1_round2_analyses.py       # worst-ratio diagnostics, pooled BH, interval score, D8 history benchmarks, model forms
python code/L2_export_series.py && Rscript code/L2_r_forecast_check.R && python code/L2_compare.py  # R forecast cross-check
python code/L3_m4_published.py          # published M4 submissions on the 1,000 series (downloads them)
python code/N8_more_foundation_models.py --m4   # Chronos-2, TiRex, TimesFM-2.5 with settings off
python code/N9_horizon48.py             # H = 48 check (Supporting Information S7)
python code/B9_forest_plot.py           # forest plot of the pairwise comparisons (Figure 3)
python code/B10_figure_h48.py           # Figure S3
python code/K8_prose_recommendations.py; python code/K9_round2_revisions.py; python code/K10_round2_extensions.py  # text revisions (already applied)

# post hoc, remaining referee requests (D-15)
python code/R2_run_robust.py --reps 200 --variants heavy_outliers --tag robust_combo   # then merge into robust_metrics.csv; R4, R5
python code/L4_d8_count_benchmarks.py   # iETS (R smooth), negative binomial, TSB compound on D8
python code/L5_post_cutoff_tier.py      # FRED-MD, 2025-01..2026-06 (download the vintage first; see results/post_cutoff/README.md)
python code/L6_remaining_analyses.py    # simultaneous intervals, familiarity, instance transfer, M4 reweighting, MASE scale
python code/K11_restructure.py; python code/K13_remaining_requests.py; python code/K12_terminology.py  # text (K12 last)
python code/S1_build_upload_bundle.py   # Journal of Forecasting upload bundle

# checks -- all of these should pass before submission
python code/90_verify_refs.py           # resolve EVERY DOI in refs.bib (Crossref + DataCite)
python code/92_check_ajs_style.py       # mechanical AJS compliance
python code/94_verify_review_claims.py  # reviewer claims vs the data
python code/95_final_number_check.py    # every headline number vs its CSV
python code/96_find_published_versions.py  # find versions of record for preprints
python code/97_upgrade_citations.py     # rewrite preprint entries to published versions
```

`03_run_forecasts.py` runs in three phases (classical, then TimesFM-3, then metrics) and each
phase caches per cell, so the run is resumable and any phase can be re-run alone.

## Three traps that cost time here

1. **Do not load the TimesFM model before statsforecast's process pool starts.** On Windows the
   pool uses spawn, so every worker re-imports the parent module; with the 330M-parameter model
   resident, 24 workers exhaust memory (`WinError 8`). Ordering the phases classical-then-model
   fixed it and made the run 12x faster (D4 at n=200: 656s -> 54s).
2. **Do not trust a Crossref title search for DOIs.** Queried by title it returns the NBER
   working paper for Diebold-Mariano, technical reports for both Gneiting papers, and a 2011
   reprint for Hodges-Lehmann 1963. `90_verify_refs.py` validates DOIs directly instead.

3. **Never label statsforecast series with unpadded integer strings.** `unique_id = str(i)`
   makes statsforecast return rows in LEXICOGRAPHIC order -- "0","1","10","100","1000",... --
   so any reshape assuming numeric order pairs every forecast with the WRONG series. It fails
   SILENTLY: no error, just nonsense. Here it put seasonal naive at MASE 28.9 when, being
   essentially the MASE denominator, it must score near 1. Use `f"{i:07d}"`. The tell is a
   sanity-check number that is impossible rather than merely surprising -- always have one.

## Build

```
cd manuscript
pdflatex timesfm_vs_classical && bibtex timesfm_vs_classical && pdflatex timesfm_vs_classical && pdflatex timesfm_vs_classical
```

`pdflatex`, not `xelatex` -- `ajs.cls` is a JSS derivative and the project's xelatex rule
applies to the Arabic study sheets, not to journal classes.

## Archiving to Zenodo

**The route used for this family: GitHub release -> Zenodo webhook.** No API calls, no token.

  Repository: https://github.com/ebrahimkhaled/timesfm-classical-paper

1. On https://zenodo.org/account/settings/github/ flip the switch ON for
   `timesfm-classical-paper`. This must be done BEFORE the release: the webhook only fires for
   releases created while the switch is on.
2. Cut a GitHub release (`v1.0.0`).
3. Zenodo archives the tagged snapshot and mints the DOI by itself.

`.zenodo.json` sits at the repository root, so Zenodo takes the title, author, ORCID, licence,
keywords and description from it rather than guessing from the repo name.

Then put the **concept DOI** (the one resolving to all versions) into the manuscript's
data-availability statement, replacing `10.5281/zenodo.22681072`, and record it in
`ACADEMIC_TRACKER.md`.

### Fallback: the REST API

`code/98_build_release.py` and `code/99_deposit_zenodo.py` do the same thing through Zenodo's
API, leaving an unpublished draft. They are the fallback for a deposit that is not backed by a
GitHub repository, or for content too large to want in git. The GitHub route above is simpler
and is what this paper uses.

Excluded from the archive on purpose: the 291 MB raw M4 download (re-fetched by the code; the
seeded 1,000-series sample IS included), the mis-ordered forecast arrays from the D-06 bug, and
the journal's LaTeX class.

## Preprint

The arXiv source bundle is built by `code/A0_build_arxiv.py` (flattens figure paths, ships
`ajs.cls` and the society logo, generates the `.bbl` from the build that ships) and verified by
the clean-room test in the `arxiv-latex-submission` skill. Form metadata:
`arxiv/SUBMISSION_METADATA.md`.
