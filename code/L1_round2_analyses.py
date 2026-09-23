"""Second referee round: reanalyses of existing results plus two small new computations.

Writes results/round2/:
  worst_ratio_variants.csv   worst / 90th-percentile ratio to the cell-best, with and without the two
                             cells where m = 12 is imposed on two cycles (D4, D5 at n = 24)
  worst_ratio_boot.csv       paired bootstrap (B = 2000) of TimesFM-3's worst ratio and of its
                             difference from AutoARIMA's; cross-fitted (split-half) estimate
  bh_pooled.csv              BH over all 180 (h = 1..12) tests pooled, and over all 540
  paired_mcse.csv            Monte Carlo SE of the paired MASE difference TimesFM-3 - AutoARIMA per cell
  interval_score.csv         80% interval score (scaled, as MSIS) per method and process
  d8_benchmarks.csv          D8: empirical-quantile and context-mean benchmarks on the same series
  model_selection.csv        forms chosen by AutoETS / AutoARIMA on D4 and D5 at n = 24 and 48
"""

from __future__ import annotations

import importlib
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
dgp = importlib.import_module("01_dgp")
met = importlib.import_module("02_metrics")
OUT = ROOT / "results" / "round2"
OUT.mkdir(exist_ok=True)
METHODS = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination", "TimesFM3"]
DGPS = [f"D{i}" for i in range(1, 10)]
NS = [24, 48, 96, 200]
H = 12
RNG = np.random.default_rng(20260923)


def bh(p):
    p = np.asarray(p, float)
    n = len(p)
    o = np.argsort(p)
    q = np.minimum.accumulate((p[o] * n / np.arange(1, n + 1))[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.minimum(q, 1)
    return out


def per_series():
    d = pd.read_csv(ROOT / "results" / "all_metrics.csv",
                    usecols=["dgp", "n", "rep", "method", "horizon_slice", "MASE"])
    d = d[(d.horizon_slice == "h1_12") & d.method.isin(METHODS)]
    return d.pivot_table(index=["dgp", "n", "rep"], columns="method", values="MASE")


def worst_ratios(ps):
    cm = ps.groupby(level=["dgp", "n"]).mean()
    r = cm.div(cm.min(axis=1), axis=0)
    two = [("D4", 24), ("D5", 24)]
    keep = r.drop(index=two)
    rows = []
    for m in METHODS:
        rows.append({"method": m, "worst_all": r[m].max(), "cell_all": str(r[m].idxmax()),
                     "p90_all": r[m].quantile(0.9), "median_all": r[m].median(),
                     "geo_mean_all": float(np.exp(np.log(r[m]).mean())),
                     "worst_excl_two_cycle": keep[m].max(), "cell_excl": str(keep[m].idxmax()),
                     "p90_excl_two_cycle": keep[m].quantile(0.9)})
    pd.DataFrame(rows).to_csv(OUT / "worst_ratio_variants.csv", index=False)
    print(pd.DataFrame(rows).round(3).to_string())


def boot_worst(ps, B=2000):
    """Resample replications within each cell (paired across methods)."""
    cells = {k: g.to_numpy() for k, g in ps.groupby(level=["dgp", "n"])}
    cols = list(ps.columns)
    it, ia = cols.index("TimesFM3"), cols.index("AutoARIMA")
    tf, ar, diff = [], [], []
    for _ in range(B):
        means = np.array([x[RNG.integers(0, len(x), len(x))].mean(axis=0) for x in cells.values()])
        ratio = means / means.min(axis=1, keepdims=True)
        tf.append(ratio[:, it].max())
        ar.append(ratio[:, ia].max())
        diff.append(ratio[:, ia].max() - ratio[:, it].max())
    # Cross-fitting: pick the cell-best method on one half, estimate the ratio on the other.
    cf = []
    for _ in range(200):
        vals = []
        for x in cells.values():
            idx = RNG.permutation(len(x))
            a, b = x[idx[: len(x) // 2]].mean(axis=0), x[idx[len(x) // 2:]].mean(axis=0)
            vals.append(b[it] / b[np.argmin(a)])
        cf.append(max(vals))
    q = lambda v: np.quantile(v, [0.025, 0.975])
    res = pd.DataFrame([
        {"quantity": "TimesFM3 worst ratio", "lo": q(tf)[0], "hi": q(tf)[1], "boot_se": np.std(tf)},
        {"quantity": "AutoARIMA worst ratio", "lo": q(ar)[0], "hi": q(ar)[1], "boot_se": np.std(ar)},
        {"quantity": "AutoARIMA minus TimesFM3 worst ratio", "lo": q(diff)[0], "hi": q(diff)[1],
         "boot_se": np.std(diff)},
        {"quantity": "TimesFM3 worst ratio, cross-fitted (median of 200 splits)",
         "lo": np.quantile(cf, 0.025), "hi": np.quantile(cf, 0.975), "boot_se": np.median(cf)}])
    res.to_csv(OUT / "worst_ratio_boot.csv", index=False)
    print(res.round(3).to_string())


def pooled_bh():
    t = pd.read_csv(ROOT / "results" / "table_tests.csv")
    rows = []
    for name, sub in [("h1_12, 180 pooled", t[t.horizon_slice == "h1_12"].copy()),
                      ("all slices, 540 pooled", t.copy())]:
        sub["q"] = bh(sub.p_wilcoxon)
        s = sub[sub.q < 0.05]
        s12 = s[s.horizon_slice == "h1_12"]
        rows.append({"family": name, "significant_h1_12": len(s12),
                     "tfm_wins_h1_12": int(s12.timesfm_wins.sum()),
                     "arima_sig": int((s12.opponent == "AutoARIMA").sum()),
                     "arima_tfm_wins": int(s12[s12.opponent == "AutoARIMA"].timesfm_wins.sum())})
    # the published family: per opponent over 108 tests
    t12 = t[t.horizon_slice == "h1_12"]
    rows.append({"family": "per opponent over 108 (published)", "significant_h1_12": int(t12.significant.sum()),
                 "tfm_wins_h1_12": int((t12.significant & t12.timesfm_wins).sum()),
                 "arima_sig": int(t12[t12.opponent == "AutoARIMA"].significant.sum()),
                 "arima_tfm_wins": int((t12.significant & t12.timesfm_wins & (t12.opponent == "AutoARIMA")).sum())})
    pd.DataFrame(rows).to_csv(OUT / "bh_pooled.csv", index=False)
    print(pd.DataFrame(rows).to_string())


def paired_mcse(ps):
    rows = []
    for (d, n), g in ps.groupby(level=["dgp", "n"]):
        x = (g["TimesFM3"] - g["AutoARIMA"]).to_numpy()
        se = x.std(ddof=1) / np.sqrt(len(x))
        rows.append({"dgp": d, "n": n, "mean_diff": x.mean(), "mcse": se,
                     "mcse_pct_of_arima": 100 * se / g["AutoARIMA"].mean(),
                     "mdd_pct": 100 * 2.8 * se / g["AutoARIMA"].mean()})
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "paired_mcse.csv", index=False)
    print("paired MCSE as pct of AutoARIMA mean: median %.2f range %.2f-%.2f; MDD median %.2f"
          % (r.mcse_pct_of_arima.median(), r.mcse_pct_of_arima.min(), r.mcse_pct_of_arima.max(),
             r.mdd_pct.median()))


def interval_score():
    """Scaled 80% interval score [q0.1, q0.9], alpha = 0.2, divided by the MASE denominator."""
    rows = []
    for d in DGPS:
        for n in NS:
            c = np.load(ROOT / "results" / "forecasts" / f"classical_{d}_n{n}_r200.npz")
            t = np.load(ROOT / "results" / "forecasts" / f"timesfm_{d}_n{n}_r200.npz")
            m = 12 if d in ("D4", "D5") else 1
            ys = [dgp.simulate(d, n, r) for r in range(200)]
            den = np.array([met.mase_denominator(y[:n], m) for y in ys])
            act = np.array([y[n:n + H] for y in ys])
            for meth in METHODS:
                q = (t if meth == "TimesFM3" else c)[f"{meth}_q"]
                lo, hi = q[:, :, 0], q[:, :, 8]
                s = (hi - lo) + (2 / 0.2) * ((lo - act) * (act < lo) + (act - hi) * (act > hi))
                ok = den > 0
                rows.append({"dgp": d, "n": n, "method": meth,
                             "IS80": float(np.mean(s[ok].mean(axis=1) / den[ok]))})
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "interval_score.csv", index=False)
    w = r.pivot_table(index=["dgp", "n"], columns="method", values="IS80")
    print("IS80 cell wins:", w.idxmin(axis=1).value_counts().to_dict())
    print(w.loc["D6"].round(2).to_string())
    print(w.groupby(level="dgp").mean().round(2).to_string())


def d8_benchmarks():
    rows = []
    for n in NS:
        for r in range(200):
            y = dgp.simulate("D8", n, r)
            ctx, act = y[:n], y[n:n + H]
            den = met.mase_denominator(ctx, 1)
            den2 = met.rmsse_denominator(ctx, 1)
            if den <= 0:
                continue
            qs = np.tile(np.quantile(ctx, met.QUANTILE_LEVELS), (H, 1))
            for name, pt in [("EmpiricalMedian", np.full(H, np.median(ctx))),
                             ("ContextMean", np.full(H, ctx.mean()))]:
                cm = ctx.mean()
                rows.append({"n": n, "rep": r, "method": name,
                             "MASE": met.mase(act, pt, den), "RMSSE": met.rmsse(act, pt, den2),
                             "sME": float(np.mean(pt - act) / den),
                             "sPIS": float(-np.sum(np.cumsum(act - pt)) / cm) if cm > 0 else np.nan,
                             "SPL": met.scaled_pinball_loss(act, qs, den)
                             if name == "EmpiricalMedian" else np.nan})
    r = (pd.DataFrame(rows).groupby(["n", "method"])[["MASE", "RMSSE", "sME", "sPIS", "SPL"]].mean()
         .reset_index())
    r.to_csv(OUT / "d8_benchmarks.csv", index=False)
    print(r.round(3).to_string())


def model_selection():
    from statsforecast.models import AutoARIMA, AutoETS
    rows = []
    for d in ["D4", "D5"]:
        for n in [24, 48]:
            for r in range(200):
                y = dgp.simulate(d, n, r)[:n]
                e = AutoETS(season_length=12).fit(y)
                a = AutoARIMA(season_length=12).fit(y)
                p, q, P, Q, m, dd, D = a.model_["arma"]
                rows.append({"dgp": d, "n": n, "rep": r, "ets": e.model_["method"],
                             "arima": f"({p},{dd},{q})({P},{D},{Q})[{m}]",
                             "ets_seasonal": not e.model_["method"].endswith("N)"),
                             "arima_seasonal": (P + D + Q) > 0})
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "model_selection.csv", index=False)
    print(r.groupby(["dgp", "n"])[["ets_seasonal", "arima_seasonal"]].mean().round(3).to_string())
    for (d, n), g in r.groupby(["dgp", "n"]):
        print(d, n, g.ets.value_counts().head(3).to_dict(), g.arima.value_counts().head(3).to_dict())


if __name__ == "__main__":
    ps = per_series()
    worst_ratios(ps)
    pooled_bh()
    paired_mcse(ps)
    boot_worst(ps)
    interval_score()
    d8_benchmarks()
    model_selection()
