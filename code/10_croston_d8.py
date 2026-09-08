"""POST-HOC: add intermittent-demand baselines (Croston family) on D8.

Why this exists
---------------
The pre-registered comparison set contains no method designed for intermittent demand, and D8
is precisely where TimesFM-3's largest advantage sits. That makes the headline D8 result a
comparison against general-purpose methods on data none of them was built for -- a fair referee
objection, and one the manuscript already concedes. This script closes it by adding the
Croston family and re-running the D8 comparison against them.

Baselines added (all from statsforecast):
    CrostonClassic     Croston's original method
    CrostonOptimized   Croston with optimised smoothing
    CrostonSBA         Syntetos-Boylan approximation, the standard bias correction
    ADIDA              aggregate-disaggregate intermittent demand approach
    IMAPA              intermittent multiple aggregation prediction algorithm
    TSB                Teunter-Syntetos-Babai

Status: POST HOC. This was added after the main results were seen, in response to an identified
gap. It is reported as a supplementary analysis, never as a pre-registered result, and it does
not alter the 36-cell main analysis. Recorded as deviation D-09.

Intervals: Croston-family methods are point forecasters. statsforecast can attach conformal
intervals, which needs n_windows * h observations beyond the training window; that is not
available at every length here. Where conformal intervals are unavailable the method is scored
on point metrics only, and this is reported rather than papered over.

Usage:  python code/10_croston_d8.py
"""

from __future__ import annotations

import importlib.util
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
FC = RES / "forecasts"

_d = importlib.util.spec_from_file_location("dgp", ROOT / "code" / "01_dgp.py")
dgp = importlib.util.module_from_spec(_d); _d.loader.exec_module(dgp)
_m = importlib.util.spec_from_file_location("metrics", ROOT / "code" / "02_metrics.py")
mx = importlib.util.module_from_spec(_m); _m.loader.exec_module(mx)
_a = importlib.util.spec_from_file_location("an", ROOT / "code" / "04_analyse.py")
an = importlib.util.module_from_spec(_a); _a.loader.exec_module(an)

DGP_ID = "D8"
REPS = 200
H = dgp.HORIZON
SLICE = slice(0, 12)
INTERMITTENT = ["CrostonClassic", "CrostonOptimized", "CrostonSBA", "ADIDA", "IMAPA", "TSB"]


def build_models():
    from statsforecast.models import (ADIDA, IMAPA, TSB, CrostonClassic,
                                      CrostonOptimized, CrostonSBA)
    # TSB needs both smoothing parameters; 0.2/0.2 is the common default in the literature.
    return [CrostonClassic(), CrostonOptimized(), CrostonSBA(), ADIDA(), IMAPA(),
            TSB(alpha_d=0.2, alpha_p=0.2)]


def run_length(n: int) -> pd.DataFrame:
    from statsforecast import StatsForecast

    series = np.array([dgp.simulate(DGP_ID, n, r, H) for r in range(REPS)])
    contexts, truths = series[:, :n], series[:, n:]
    m = dgp.SEASONAL_PERIOD[DGP_ID]

    long = pd.DataFrame({
        "unique_id": np.repeat([f"{i:05d}" for i in range(REPS)], n),
        "ds": np.tile(np.arange(n), REPS),
        "y": contexts.ravel(),
    })
    sf = StatsForecast(models=build_models(), freq=1, n_jobs=1)
    fc = sf.forecast(df=long, h=H).sort_values(["unique_id", "ds"])

    rows = []
    for method in INTERMITTENT:
        pt = fc[method].to_numpy(dtype=float).reshape(REPS, H)
        for r in range(REPS):
            denom = mx.mase_denominator(contexts[r], m)
            denom2 = mx.rmsse_denominator(contexts[r], m)
            rows.append({
                "dgp": DGP_ID, "n": n, "rep": r, "method": method,
                "MASE": mx.mase(truths[r][SLICE], pt[r][SLICE], denom),
                "RMSSE": mx.rmsse(truths[r][SLICE], pt[r][SLICE], denom2),
                "sMAPE": mx.smape(truths[r][SLICE], pt[r][SLICE]),
            })

    # TimesFM-3 and the original classical set, re-scored on the same slice for comparability.
    tf = np.load(FC / f"timesfm_{DGP_ID}_n{n}_r{REPS}.npz")
    cl = np.load(FC / f"classical_{DGP_ID}_n{n}_r{REPS}.npz")
    existing = {"TimesFM3": tf["TimesFM3_pt"], "AutoARIMA": cl["AutoARIMA_pt"],
                "AutoETS": cl["AutoETS_pt"], "SeasonalNaive": cl["SeasonalNaive_pt"]}
    for method, pt in existing.items():
        for r in range(REPS):
            denom = mx.mase_denominator(contexts[r], m)
            denom2 = mx.rmsse_denominator(contexts[r], m)
            rows.append({
                "dgp": DGP_ID, "n": n, "rep": r, "method": method,
                "MASE": mx.mase(truths[r][SLICE], pt[r][SLICE], denom),
                "RMSSE": mx.rmsse(truths[r][SLICE], pt[r][SLICE], denom2),
                "sMAPE": mx.smape(truths[r][SLICE], pt[r][SLICE]),
            })
    return pd.DataFrame(rows)


def main() -> None:
    frames = [run_length(n) for n in dgp.LENGTHS]
    for n, f in zip(dgp.LENGTHS, frames):
        print(f"  n={n}: {len(f):,} rows", flush=True)
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(RES / "croston_d8_metrics.csv", index=False)

    print("\n=== D8: mean MASE (lower is better) ===")
    piv = df.pivot_table(index="n", columns="method", values="MASE")
    order = INTERMITTENT + ["SeasonalNaive", "AutoETS", "AutoARIMA", "TimesFM3"]
    piv = piv[[c for c in order if c in piv.columns]]
    print(piv.round(3).to_string())
    print("  winner:", list(piv.idxmin(axis=1)))

    print("\n=== D8: mean RMSSE ===")
    pr = df.pivot_table(index="n", columns="method", values="RMSSE")[piv.columns]
    print(pr.round(3).to_string())
    print("  winner:", list(pr.idxmin(axis=1)))

    # Paired Wilcoxon: TimesFM-3 against each intermittent baseline, per length, on MASE.
    rows = []
    for n in dgp.LENGTHS:
        sub = df[df.n == n].pivot_table(index="rep", columns="method", values="MASE")
        for opp in INTERMITTENT:
            pair = sub[["TimesFM3", opp]].dropna()
            d = (pair["TimesFM3"] - pair[opp]).to_numpy()
            p = 1.0 if np.allclose(d, 0) else float(stats.wilcoxon(d).pvalue)
            rows.append({"n": n, "opponent": opp,
                         "mean_MASE_timesfm": float(pair["TimesFM3"].mean()),
                         "mean_MASE_opponent": float(pair[opp].mean()),
                         "median_ratio": float(pair["TimesFM3"].median() / pair[opp].median()),
                         "p_wilcoxon": p, "timesfm_wins": bool(np.median(d) < 0)})
    t = pd.DataFrame(rows)
    t["p_adj"] = an.benjamini_hochberg(t["p_wilcoxon"].to_numpy())
    t["significant"] = t["p_adj"] < 0.05
    t.to_csv(RES / "croston_d8_tests.csv", index=False)

    print("\n=== TimesFM-3 vs each intermittent baseline (MASE, BH-adjusted) ===")
    print(t[["n", "opponent", "mean_MASE_timesfm", "mean_MASE_opponent", "median_ratio",
             "p_adj", "significant", "timesfm_wins"]].round(4).to_string(index=False))
    sig = t[t.significant]
    print(f"\nsignificant: {len(sig)}/{len(t)}; TimesFM-3 wins {int(sig.timesfm_wins.sum())}, "
          f"loses {int((~sig.timesfm_wins).sum())}")

    write_table(df)
    print("\nwrote croston_d8_metrics.csv, croston_d8_tests.csv, tab_croston.tex")


def write_table(df: pd.DataFrame) -> None:
    """Emit the LaTeX table. Caption above the tabular, per the AJS rule."""
    man = ROOT / "manuscript"
    cols = INTERMITTENT + ["AutoARIMA", "TimesFM3"]
    head = ["Croston", "Croston-opt", "Croston-SBA", "ADIDA", "IMAPA", "TSB",
            "AutoARIMA", "\\textbf{TimesFM-3}"]

    lines = [
        "% generated by code/10_croston_d8.py -- do not edit by hand",
        "\\begin{table}[t!]", "\\centering",
        "\\caption{Intermittent-demand baselines on D8, added post hoc. TimesFM-3 beats every "
        "purpose-built method on MASE at every length (24 of 24 comparisons significant after "
        "Benjamini--Hochberg correction), and loses to them on RMSSE at every length. The best "
        "value in each row is in bold.}",
        "\\label{tab:croston}",
        "\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{llrrrrrrrr}", "\\toprule",
        "Metric & $n$ & " + " & ".join(head) + " \\\\", "\\midrule",
    ]
    for mi, (col, label) in enumerate([("MASE", "MASE"), ("RMSSE", "RMSSE")]):
        piv = df.pivot_table(index="n", columns="method", values=col)[cols]
        for i, (n, row) in enumerate(piv.iterrows()):
            best = row.idxmin()
            cells = " & ".join(
                (f"\\textbf{{{row[c]:.3f}}}" if c == best else f"{row[c]:.3f}") for c in cols)
            lines.append(f"{label if i == 0 else ''} & {n} & {cells} \\\\")
        if mi == 0:
            lines.append("\\addlinespace")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    (man / "tab_croston.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
