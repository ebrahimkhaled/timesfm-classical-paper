"""Post-hoc robustness check: a MEDIAN combination of the classical methods.

Motivation
----------
The pre-registered combination is the equal-weight MEAN of Theta, AutoETS and AutoARIMA.
The main results show TimesFM-3 beating that combination in 27 of 30 significant comparisons
-- but inspection shows why: Theta fails catastrophically on some cells (mean MASE 4.16 on D4
at n = 200, against 0.89 for AutoARIMA), and a mean is not robust to a member that breaks.
A referee would rightly object that the combination baseline was therefore weak.

This script recomputes the comparison against a MEDIAN combination, which is robust to one
bad member, so the paper reports the strongest classical baseline rather than a convenient one.

Status: POST HOC. This analysis was added after the main results were seen and is reported as
a robustness check, never as a pre-registered result. Recorded in DEVIATIONS.md as D-04.

Usage:  python code/08_robust_combination.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
FC = ROOT / "results" / "forecasts"
RES = ROOT / "results"

_s = importlib.util.spec_from_file_location("dgp", ROOT / "code" / "01_dgp.py")
dgp = importlib.util.module_from_spec(_s); _s.loader.exec_module(dgp)
_m = importlib.util.spec_from_file_location("metrics", ROOT / "code" / "02_metrics.py")
mx = importlib.util.module_from_spec(_m); _m.loader.exec_module(mx)

PARTS = ["Theta", "AutoETS", "AutoARIMA"]
REPS = 200
SLICE = slice(0, 12)


def main() -> None:
    rows = []
    for d in dgp.DGP_IDS:
        m = dgp.SEASONAL_PERIOD[d]
        for n in dgp.LENGTHS:
            series = np.array([dgp.simulate(d, n, r, dgp.HORIZON) for r in range(REPS)])
            contexts, truths = series[:, :n], series[:, n:]
            cl = np.load(FC / f"classical_{d}_n{n}_r{REPS}.npz")
            tf = np.load(FC / f"timesfm_{d}_n{n}_r{REPS}.npz")

            med_pt = np.median([cl[f"{k}_pt"] for k in PARTS], axis=0)
            med_q = np.sort(np.median([cl[f"{k}_q"] for k in PARTS], axis=0), axis=2)

            cand = {"MedianCombination": (med_pt, med_q),
                    "MeanCombination": (cl["Combination_pt"], cl["Combination_q"]),
                    "TimesFM3": (tf["TimesFM3_pt"], tf["TimesFM3_q"])}
            per = {k: [] for k in cand}
            for method, (pt, qs) in cand.items():
                for r in range(REPS):
                    per[method].append(
                        mx.evaluate(truths[r][SLICE], pt[r][SLICE], qs[r][SLICE],
                                    contexts[r], m)["MASE"])

            tfm = np.array(per["TimesFM3"], dtype=float)
            for opp in ["MeanCombination", "MedianCombination"]:
                o = np.array(per[opp], dtype=float)
                ok = np.isfinite(tfm) & np.isfinite(o)
                diff = tfm[ok] - o[ok]
                p = 1.0 if np.allclose(diff, 0) else float(
                    stats.wilcoxon(diff, zero_method="wilcox").pvalue)
                rows.append({
                    "dgp": d, "correct_model": dgp.CORRECT_MODEL[d], "n": n, "opponent": opp,
                    "mean_MASE_timesfm": float(np.mean(tfm[ok])),
                    "mean_MASE_opponent": float(np.mean(o)),
                    "median_ratio": float(np.median(tfm[ok]) / np.median(o[ok])),
                    "p_wilcoxon": p, "timesfm_wins": bool(np.median(diff) < 0),
                })

    df = pd.DataFrame(rows)
    # BH within each opponent family, matching the main analysis.
    from importlib import util as _u
    _a = _u.spec_from_file_location("an", ROOT / "code" / "04_analyse.py")
    an = _u.module_from_spec(_a); _a.loader.exec_module(an)
    df["p_adj"] = np.nan
    for opp, idx in df.groupby("opponent").groups.items():
        df.loc[idx, "p_adj"] = an.benjamini_hochberg(df.loc[idx, "p_wilcoxon"].to_numpy())
    df["significant"] = df["p_adj"] < 0.05
    df.to_csv(RES / "table_robust_combination.csv", index=False)

    print("Post-hoc: TimesFM-3 against two classical combinations (h = 1..12, 36 cells each)\n")
    for opp, g in df.groupby("opponent"):
        s = g[g.significant]
        print(f"{opp:<20} mean MASE {g.mean_MASE_opponent.mean():.3f}  |  "
              f"significant {len(s):2d}/36  "
              f"TimesFM-3 wins {int((s.timesfm_wins).sum()):2d}, "
              f"loses {int((~s.timesfm_wins).sum()):2d}")
    print(f"\n{'':<20} TimesFM-3 mean MASE {df.mean_MASE_timesfm.mean():.3f}")
    print("\nwrote results/table_robust_combination.csv")


if __name__ == "__main__":
    main()
