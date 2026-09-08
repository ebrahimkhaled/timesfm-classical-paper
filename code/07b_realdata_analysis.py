"""Analysis of the real-data (M4 Monthly) tier.

A note on the test used, and why Diebold-Mariano was DROPPED entirely
--------------------------------------------------------------------
PREREGISTRATION.md section 3.4 specified the Diebold-Mariano test with the
Harvey-Leybourne-Newbold correction for this tier, on the grounds that rolling-origin
evaluation produces an autocorrelated loss-differential sequence -- the setting DM is built for.

That reasoning was right in principle and wrong in this design, for two reasons.

First, the realised design has only THREE origins per series, so a per-series DM statistic has
2 degrees of freedom and essentially no power.

Second -- and this is why DM is now removed rather than merely de-emphasised -- an earlier
version of this script computed a "supplementary" DM statistic on the cross-section of 1,000
per-series mean MASE differences. That vector is indexed by M4 series id in lexicographic order,
not by time, so the HAC correction summed autocovariances across unrelated series over an
arbitrary ordering. The statistic was not order-invariant: it read -13.97 as computed and
between -18 and -23 under random permutations of the same numbers. A quantity that moves by 30
to 70 percent when an arbitrary index is reshuffled is not a test, and it has been deleted
rather than reported with a caveat.

What is well-powered and correct here is the comparison ACROSS series. The 1,000 M4 series are
distinct series, so averaging each one's MASE over its three origins gives 1,000 independent
units, and a paired Wilcoxon signed-rank test across them is both appropriate and powerful --
the same instrument used in the simulation tier, for the same reason.

Recorded as deviations D-05 and D-07.

Usage:  python code/07b_realdata_analysis.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"

_a = importlib.util.spec_from_file_location("an", ROOT / "code" / "04_analyse.py")
an = importlib.util.module_from_spec(_a); _a.loader.exec_module(an)

FOUNDATION = "TimesFM3"
OPPONENTS = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination"]
ORDER = OPPONENTS + [FOUNDATION]


def main() -> None:
    df = pd.read_csv(RES / "realdata_metrics.csv")
    print(f"{df.unique_id.nunique():,} series x {df.origin.nunique()} origins "
          f"x {df.method.nunique()} methods = {len(df):,} rows\n")

    # ---- descriptive ----
    summ = (df.groupby("method")
              .agg(mean_MASE=("MASE", "mean"), median_MASE=("MASE", "median"),
                   mean_sMAPE=("sMAPE", "mean"), mean_SPL=("SPL", "mean"),
                   cover60=("cover60", "mean"), cover80=("cover80", "mean"))
              .reindex(ORDER))
    print("=== M4 Monthly, h = 1..18, averaged over all windows ===")
    print(summ.round(4).to_string())
    summ.to_csv(RES / "realdata_summary.csv")

    # ---- primary: paired Wilcoxon across series (1,000 independent units) ----
    per_series = df.groupby(["unique_id", "method"])["MASE"].mean().unstack()
    rows = []
    for opp in OPPONENTS:
        pair = per_series[[FOUNDATION, opp]].dropna()
        d = (pair[FOUNDATION] - pair[opp]).to_numpy()
        p = float(stats.wilcoxon(d).pvalue)
        rows.append({
            "opponent": opp, "n_series": len(pair),
            "mean_MASE_timesfm": float(pair[FOUNDATION].mean()),
            "mean_MASE_opponent": float(pair[opp].mean()),
            "median_ratio": float(pair[FOUNDATION].median() / pair[opp].median()),
            "hodges_lehmann": an.hodges_lehmann(d),
            "p_wilcoxon": p,
            "timesfm_wins": bool(np.median(d) < 0),
            "pct_series_timesfm_better": float(100 * np.mean(d < 0)),
        })
    tests = pd.DataFrame(rows)
    tests["p_adj"] = an.benjamini_hochberg(tests["p_wilcoxon"].to_numpy())
    tests["significant"] = tests["p_adj"] < 0.05
    tests.to_csv(RES / "realdata_tests.csv", index=False)

    print("\n=== primary: paired Wilcoxon across series (TimesFM-3 vs each) ===")
    print(tests[["opponent", "mean_MASE_timesfm", "mean_MASE_opponent", "median_ratio",
                 "pct_series_timesfm_better", "p_adj", "significant"]].round(4).to_string(index=False))

    print("\nwrote realdata_summary.csv, realdata_tests.csv")


if __name__ == "__main__":
    main()
