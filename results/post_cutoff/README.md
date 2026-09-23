# Post-cut-off real-data tier (FRED-MD)

This tier answers the referee request for evaluation data published after the foundation models' training cut-offs. It was built on 2026-09-23 by `code/L5_post_cutoff_tier.py`.

## Data
- **Source:** FRED-MD monthly database (McCracken and Ng 2016), Federal Reserve Bank of St. Louis. The file is the "current.csv" link on the official page https://www.stlouisfed.org/research/economists/mccracken/fred-databases. That link now resolves to `.../fred-md/monthly/2026-rev-08-md.csv`. The old `files.stlouisfed.org/.../current.csv` URL returns 403.
- **Vintage:** 2026-08 ("2026-rev-08"). The last month in the file is 2026-07. Saved copy: `data/fredmd/2026-rev-08-md.csv`, 668,731 bytes, SHA-256 `412b5451f32321b597c86b95603f5815ae0bd6e44eb7388e4c415156434ac0a4`.
- **Series:** the raw level series. The transformation-code row is skipped and the transformations are not applied. 126 series are in the file. 101 have complete data for 1990-01..2026-06 and are kept; 25 are dropped (see `meta.json`):
  - 21 miss only **2025-10**, the month lost to the October 2025 US federal shutdown: CPI components, the household-survey labour series, HWIURATIO and M2REAL.
  - ACOGNO starts after 1990-01.
  - CP3Mx and COMPAPFFx miss 2020-04.
  - The S&P PE ratio misses 2026-05..06.
- **Non-positive values:** 7 kept series have them (NONBORRES and the six rate spreads TB3SMFFM, TB6SMFFM, T1YFFM, T5YFFM, T10YFFM, AAAFFM). They are scored on MASE, coverage and SPL. They are excluded from the sMAPE average (`mean_sMAPE_pos`, 94 series).

## Design
- **Forecast origin:** 2024-12. The context is the last 240 months (2005-01..2024-12) and is the same length for every series.
- **Horizon:** h = 18. The **evaluation window is 2025-01..2026-06**, and all 18 months are observed.
- **MASE denominator:** the in-sample seasonal-naive MAE (m = 12) on the 240-month context. SPL uses the same scale over the nine deciles. Coverage is that of [q0.1, q0.9].

## Documented cut-offs relative to the window
| Model | Documented cut-off / release | Status of the 2025-01..2026-06 window |
|---|---|---|
| TimesFM-3, TimesFM-2.5 | real-world pre-training corpus to Nov 2023 (model card) | entirely after the documented corpus |
| Chronos-Bolt | released Nov 2024 | entirely after release |
| TiRex | released May 2025 | 2025-06..2026-06 after release |
| Chronos-2 | released Oct 2025 | 2025-11..2026-06 after release |

Caveats:
- TimesFM-3's synthetic and augmented training data are not documented. The public cut-off statement covers only the real-world corpus.
- Only the sub-window 2025-11..2026-06 (steps 11–18) post-dates every model's release. `mean_MASE_late` and `median_MASE_late` in `summary.csv` score that sub-window alone.
- The **context** (2005–2024) may well have been seen in pre-training. The claim is only that the **evaluated values** were not.

## Methods
- **Classical (statsforecast, m = 12):** SeasonalNaive, Theta, AutoETS and AutoARIMA. Quantiles come from the 20/40/60/80% intervals, as in `03_run_forecasts.py`. Combination is the mean of Theta, AutoETS and AutoARIMA, with vincentised quantiles.
- **Reference:** Naive (random walk). It gives a point forecast only and is excluded from the MCB.
- **Foundation models:** TimesFM-3 (predict_batch defaults), TimesFM-2.5 (N1 settings, max_context 1024), Chronos-Bolt base, Chronos-2 and TiRex (N8). The point forecast is the median decile. GPU batches have at most 100 series.

## Files
- `per_series.csv`: MASE, MASE_late, sMAPE, cover80, SPL and width80 per series and method.
- `summary.csv`: means and medians. `relMASE_vs_SNaive` is the ratio of mean MASE to SeasonalNaive's mean MASE. `gmean_ratio_vs_SNaive` is the geometric mean of the per-series ratios.
- `tests.csv`: paired Wilcoxon of TimesFM-3 against each method on per-series MASE, with Benjamini–Hochberg adjustment over the 10 comparisons.
- `mcb.csv`: Friedman test and Nemenyi CD on per-series MASE ranks, with one configuration per model (k = 10, N = 101).
- `series.csv`, `meta.json`, `timing.csv`, `log_*.txt`, `forecasts_*.npz`: supporting files.

OWA against the M4 Naive2 is not computed, because Naive2 needs a seasonality test and a decomposition that are not in this pipeline. Relative MASE to SeasonalNaive is reported instead.
