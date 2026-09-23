"""Revision (JoF referees 1-3): the extended evaluation of the main simulation design.

Methods (all on the same 7,200 series, h = 1..12):
  main study   SeasonalNaive, Theta, AutoETS, AutoARIMA, Combination, TimesFM3
  N2           DOTM, M4Comb, CombEAD, Zero (D8), AutoARIMA_cf, AutoETS_cf (n >= 96)
  N1           TimesFM3eval, TimesFM25, ChronosBolt
  derived      TimesFM3mean = TimesFM-3 with the mean of its nine deciles as point forecast
  Croston      CrostonClassic, CrostonOptimized, CrostonSBA, ADIDA, IMAPA, TSB (D8 only, refitted
               here because 10_croston_d8.py stores metrics, not forecasts)

Outputs (results/revision/):
  sim_per_series.csv.gz     every method x series: MASE, RMSSE, SPL, cover80, width80, MSIS80,
                            sME (scaled mean error, bias), sPIS (D8)
  cell_means.csv            mean and Monte Carlo SE of MASE per cell and method
  robustness_ci.csv         worst ratio to cell-best, mean log ratio, cells within 10%, wins,
                            each with a 95% bootstrap interval (replications resampled in cells)
  pairwise.csv, pairwise_tally.csv
                            Wilcoxon of each foundation model vs each classical method,
                            Hodges-Lehmann, median of paired ratios, BH within each
                            (foundation model, opponent) family as in the main study
  nemenyi.csv               Friedman / Nemenyi mean ranks per regime with critical difference
  coverage.csv              80% coverage per method (and per DGP for the foundation models),
                            with a series-cluster bootstrap MCSE; Gaussian vs conformal
  d8_table.csv              intermittent demand: MASE, RMSSE, sME, sPIS, SPL incl. Zero, Croston
  mean_vs_median.csv        TimesFM-3 point = median vs mean of deciles
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
OUT = RES / "revision"
OUT.mkdir(parents=True, exist_ok=True)
REPS, H = 200, 12
RNG = np.random.default_rng(20260924)
B = 500

FM = ["TimesFM3", "TimesFM3eval", "TimesFM25", "ChronosBolt"]
CLASSICAL = ["SeasonalNaive", "Theta", "DOTM", "AutoETS", "AutoARIMA", "Combination", "M4Comb",
             "CombEAD"]
ORIGINAL = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination", "TimesFM3"]
EXTENDED = CLASSICAL + FM
# Second referee round (N8): newer foundation models and TimesFM-2.5 with flip/positivity off.
FM_NEW = ["Chronos2", "TiRex", "TimesFM25raw"]
EXTENDED15 = EXTENDED + FM_NEW
CROSTON = ["CrostonClassic", "CrostonOptimized", "CrostonSBA", "ADIDA", "IMAPA", "TSB"]
REGIMES = {"linear (D1-D3, D9)": ["D1", "D2", "D3", "D9"], "seasonal (D4-D5)": ["D4", "D5"],
           "break and saturation (D6-D7)": ["D6", "D7"], "intermittent (D8)": ["D8"]}


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dgp = _load("dgp", "01_dgp.py")
mx = _load("metrics", "02_metrics.py")


def croston_forecasts(ctx):
    from statsforecast import StatsForecast
    from statsforecast.models import (ADIDA, IMAPA, TSB, CrostonClassic, CrostonOptimized,
                                      CrostonSBA)
    k, n = ctx.shape
    long = pd.DataFrame({"unique_id": np.repeat(np.arange(k), n), "ds": np.tile(np.arange(n), k),
                         "y": ctx.ravel()})
    sf = StatsForecast(models=[CrostonClassic(), CrostonOptimized(), CrostonSBA(), ADIDA(), IMAPA(),
                               TSB(alpha_d=0.2, alpha_p=0.2)], freq=1, n_jobs=8)
    fc = sf.forecast(df=long, h=H).sort_values(["unique_id", "ds"])
    return {m: fc[m].to_numpy(float).reshape(k, H) for m in CROSTON}


def per_series() -> pd.DataFrame:
    rows = []
    for d in dgp.DGP_IDS:
        m = dgp.SEASONAL_PERIOD[d]
        for n in dgp.LENGTHS:
            s = np.array([dgp.simulate(d, n, r, H) for r in range(REPS)])
            ctx, truth = s[:, :n], s[:, n:]
            preds = {}
            cl = np.load(RES / "forecasts" / f"classical_{d}_n{n}_r{REPS}.npz")
            tf = np.load(RES / "forecasts" / f"timesfm_{d}_n{n}_r{REPS}.npz")
            ex = np.load(RES / "classical_extra" / f"{d}_n{n}_r{REPS}.npz")
            for z in (cl, tf, ex):
                for k in z.files:
                    if k.endswith("_pt"):
                        preds[k[:-3]] = (z[k], z[k[:-3] + "_q"])
            for f in ("TimesFM3eval", "TimesFM25", "ChronosBolt", *FM_NEW):
                z = np.load(RES / "fm" / f"{f}_{d}_n{n}_r{REPS}.npz")
                preds[f] = (z[f"{f}_pt"], z[f"{f}_q"])
            q3 = preds["TimesFM3"][1]
            preds["TimesFM3mean"] = (q3.mean(axis=2), q3)
            if d == "D8":
                for mname, pt in croston_forecasts(ctx).items():
                    preds[mname] = (pt, np.repeat(pt[:, :, None], 9, axis=2))
            for meth, (pt, q) in preds.items():
                point_only = np.allclose(q[:, :, 0], q[:, :, 8])
                for r in range(REPS):
                    res = mx.evaluate(truth[r], pt[r], q[r], ctx[r], m)
                    den = mx.mase_denominator(ctx[r], m)
                    lo, hi, y = q[r][:, 0], q[r][:, 8], truth[r]
                    msis = (np.mean(hi - lo + 10 * (lo - y) * (y < lo) + 10 * (y - hi) * (y > hi)) / den
                            if not point_only else np.nan)
                    err = pt[r] - y
                    row = {"dgp": d, "n": n, "rep": r, "method": meth, "MASE": res["MASE"],
                           "RMSSE": res["RMSSE"], "SPL": res["SPL"] if not point_only else np.nan,
                           "cover80": res["cover80"] if not point_only else np.nan,
                           "width80": res["width80"] if not point_only else np.nan,
                           "MSIS80": msis, "sME": float(np.mean(err) / den)}
                    if d == "D8":
                        cm = ctx[r].mean()
                        pis = -np.sum(np.cumsum(y - pt[r]))
                        row["sPIS"] = float(pis / cm) if cm > 0 else np.nan
                    rows.append(row)
            print(f"{d} n={n}", flush=True)
    return pd.DataFrame(rows)


def boot_cells(df, methods):
    """Bootstrap the cell-level summaries by resampling replications within each cell."""
    piv = {key: g.pivot(index="rep", columns="method", values="MASE")[methods].to_numpy()
           for key, g in df[df.method.isin(methods)].groupby(["dgp", "n"])}
    keys = sorted(piv)

    def summ(means):
        best = means.min(axis=1, keepdims=True)
        ratio = means / best
        return {"worst": ratio.max(axis=0), "meanlog": np.exp(np.log(ratio).mean(axis=0)),
                "within10": (ratio <= 1.10).mean(axis=0), "wins": (ratio == 1).sum(axis=0)}

    point = summ(np.array([np.nanmean(piv[k], axis=0) for k in keys]))
    draws = {s: [] for s in point}
    for _ in range(B):
        means = []
        for k in keys:
            a = piv[k]
            means.append(np.nanmean(a[RNG.integers(0, len(a), len(a))], axis=0))
        sb = summ(np.array(means))
        for s in draws:
            draws[s].append(sb[s])
    rows = []
    for j, meth in enumerate(methods):
        r = {"method": meth}
        for s in point:
            arr = np.array(draws[s])[:, j]
            r[s], r[f"{s}_lo"], r[f"{s}_hi"] = point[s][j], *np.quantile(arr, [0.025, 0.975])
        rows.append(r)
    return pd.DataFrame(rows)


def bh(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    r = p[o] * len(p) / np.arange(1, len(p) + 1)
    q = np.minimum.accumulate(r[::-1])[::-1]
    out = np.empty(len(p))
    out[o] = np.minimum(q, 1)
    return out


def hl(d):
    w = (d[:, None] + d[None, :]) / 2
    return float(np.median(w[np.triu_indices(len(d))]))


def main():
    f = OUT / "sim_per_series.csv.gz"
    if f.exists():
        df = pd.read_csv(f)
    else:
        df = per_series()
        df.to_csv(f, index=False)

    cm = (df.groupby(["dgp", "n", "method"])["MASE"]
          .agg(mean="mean", mcse=lambda x: x.std(ddof=1) / np.sqrt(x.count()), median="median")
          .reset_index())
    cm["mcse_pct"] = 100 * cm.mcse / cm["mean"]
    cm.to_csv(OUT / "cell_means.csv", index=False)
    print("MCSE % of mean, main methods:",
          cm[cm.method.isin(ORIGINAL)].mcse_pct.describe()[["50%", "min", "max"]].round(2).to_dict())

    rc = pd.concat([boot_cells(df, ORIGINAL).assign(set="original six"),
                    boot_cells(df, EXTENDED).assign(set="extended twelve"),
                    boot_cells(df, EXTENDED15).assign(set="extended fifteen")])
    rc.to_csv(OUT / "robustness_ci.csv", index=False)
    print(rc.round(3).to_string())

    rows = []
    for fm in FM + FM_NEW:
        for opp in CLASSICAL:
            for (d, n), g in df[df.method.isin([fm, opp])].groupby(["dgp", "n"]):
                w = g.pivot(index="rep", columns="method", values="MASE").dropna()
                x = (w[fm] - w[opp]).to_numpy()
                p = stats.wilcoxon(x).pvalue if np.any(x != 0) else 1.0
                rows.append({"fm": fm, "opponent": opp, "dgp": d, "n": n, "p": p,
                             "median_diff": float(np.median(x)), "hodges_lehmann": hl(x),
                             "median_paired_ratio": float(np.median(w[fm] / w[opp]))})
    pw = pd.DataFrame(rows)
    pw["p_adj"] = pw.groupby(["fm", "opponent"])["p"].transform(bh)
    pw["fm_wins"] = (pw.p_adj < .05) & (pw.hodges_lehmann < 0)
    pw["fm_loses"] = (pw.p_adj < .05) & (pw.hodges_lehmann > 0)
    pw.to_csv(OUT / "pairwise.csv", index=False)
    tally = pw.groupby(["fm", "opponent"])[["fm_wins", "fm_loses"]].sum().reset_index()
    tally.to_csv(OUT / "pairwise_tally.csv", index=False)
    print(tally.pivot(index="opponent", columns="fm", values=["fm_wins", "fm_loses"]).to_string())

    nem = []
    for reg, dg in REGIMES.items():
        sub = df[df.dgp.isin(dg) & df.method.isin(EXTENDED15)]
        wide = sub.pivot_table(index=["dgp", "n", "rep"], columns="method", values="MASE").dropna()
        ranks = wide.rank(axis=1)
        k, N = wide.shape[1], wide.shape[0]
        chi, p = stats.friedmanchisquare(*[wide[c] for c in wide.columns])
        cd = stats.studentized_range.ppf(0.95, k, np.inf) / np.sqrt(2) * np.sqrt(k * (k + 1) / (6 * N))
        mr = ranks.mean().sort_values()
        for meth, v in mr.items():
            nem.append({"regime": reg, "method": meth, "mean_rank": v, "cd": cd, "N": N,
                        "friedman_p": p, "tied_with_best": v - mr.iloc[0] <= cd})
    nem = pd.DataFrame(nem)
    nem.to_csv(OUT / "nemenyi.csv", index=False)
    print(nem.round(3).to_string())

    cov = []
    for meth, g in df[df.cover80.notna()].groupby("method"):
        per = g.groupby(["dgp", "n", "rep"]).cover80.mean().to_numpy()
        bs = [per[RNG.integers(0, len(per), len(per))].mean() for _ in range(B)]
        cov.append({"method": meth, "dgp": "all", "cover80": per.mean(), "mcse": float(np.std(bs)),
                    "cells": g.groupby(["dgp", "n"]).ngroups})
        if meth in FM + FM_NEW or meth.endswith("_cf") or meth in ("AutoARIMA", "AutoETS"):
            for d, gd in g.groupby("dgp"):
                per_d = gd.groupby(["n", "rep"]).cover80.mean().to_numpy()
                bs = [per_d[RNG.integers(0, len(per_d), len(per_d))].mean() for _ in range(B)]
                cov.append({"method": meth, "dgp": d, "cover80": per_d.mean(),
                            "mcse": float(np.std(bs)), "cells": gd.n.nunique()})
    cov = pd.DataFrame(cov)
    big = df[(df.n >= 96)]
    cf = (big[big.method.isin(["AutoARIMA", "AutoARIMA_cf", "AutoETS", "AutoETS_cf"])]
          .groupby(["method", "dgp"]).cover80.mean().unstack().round(3))
    cov.to_csv(OUT / "coverage.csv", index=False)
    cf.to_csv(OUT / "coverage_gaussian_vs_conformal.csv")
    print(cf.to_string())

    d8 = df[df.dgp == "D8"]
    t8 = d8.groupby(["n", "method"])[["MASE", "RMSSE", "sME", "sPIS", "SPL"]].mean().reset_index()
    t8.to_csv(OUT / "d8_table.csv", index=False)
    print(t8.pivot(index="method", columns="n", values="MASE").round(3).to_string())

    mm = df[df.method.isin(["TimesFM3", "TimesFM3mean"])].groupby(["dgp", "method"])[["MASE", "RMSSE"]].mean().unstack()
    mm.to_csv(OUT / "mean_vs_median.csv")
    print(mm.round(3).to_string())


if __name__ == "__main__":
    main()
