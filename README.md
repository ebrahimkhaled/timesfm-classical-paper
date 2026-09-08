# TimesFM-3 versus Classical Time-Series Models

A contamination-free simulation comparison of Google's TimesFM-3 foundation model
(released 2026-08-31) against classical forecasting methods, with a real-data check on M4.

**Target venue:** Austrian Journal of Statistics (Scopus + WoS ESCI + DOAJ, no APC).
**Backup:** Pakistan Journal of Statistics and Operation Research (Scopus, free).

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
| `manuscript/` | AJS LaTeX (`ajs.cls`), `refs.bib`, generated tables |
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

Follows the same pattern as the EDGE / EDGES / DeepGOF-1 deposits: the script **never
publishes**. It leaves an unpublished draft for you to check and press Publish yourself,
because a published Zenodo DOI is permanent and can only be superseded, never withdrawn.

```bash
python code/98_build_release.py            # assemble release/timesfm-classical/ (~115 MB)
python code/99_deposit_zenodo.py --dry-run # list what would go up; touches nothing
python code/99_deposit_zenodo.py --sandbox # rehearse on sandbox.zenodo.org (needs its own token)
python code/99_deposit_zenodo.py           # create the draft on the real Zenodo
```

The token is read from `ZENODO_TOKEN` in the environment and is never echoed or passed on the
command line:

```bash
export ZENODO_TOKEN="<token>"
```

After publishing, put the **concept DOI** (the one resolving to all versions) into the
manuscript's data-availability statement, replacing `10.5281/zenodo.XXXXXXX`, and record it in
`ACADEMIC_TRACKER.md`. For a later revision use `--new-version --of <deposition id>`.

Excluded from the deposit on purpose: the 291 MB raw M4 download (re-fetched by the code), the
mis-ordered forecast arrays from the D-06 bug, and the journal's own LaTeX class.
