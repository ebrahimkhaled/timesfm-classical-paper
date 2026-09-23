"""Revision (JoF referee 2): uncertainty, response surface and details for the robustness study.

Reads results/robust/robust_metrics.csv (R2, 200 replications per cell) and writes

  robust_boot.csv          per variant: TimesFM-3 cell wins, worst and mean-log ratio to the
                           cell-best, share of cells within 10% of the best, and the smallest worst
                           ratio among the classical methods -- each with a 95% bootstrap interval
                           (replications resampled within cells, 500 draws)       [R2-M2]
  robust_response.csv      response surface: OLS of the per-series log(MASE_TimesFM3 /
                           MASE_AutoARIMA) on the standardised drawn parameters, log n and the
                           variant, one regression per process, HC3 standard errors  [R2-M4a]
  robust_estperiod.csv     D5 and D4 at n = 24 under the estimated period: AutoETS (m = 1) against
                           seasonal naive with the TRUE period and against TimesFM-3  [R2-M6c]
  robust_excluded.csv      series excluded because the MASE denominator is zero, per cell [R2-M7]
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results" / "robust"
GENERAL = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination"]
ALL = GENERAL + ["TimesFM3"]
RNG = np.random.default_rng(20260925)
B = 500


def boot(df):
    rows = []
    for v, gv in df.groupby("variant"):
        piv = {k: g.pivot(index="rep", columns="method", values="MASE")[ALL].to_numpy()
               for k, g in gv[gv.method.isin(ALL)].groupby(["dgp", "n"])}
        keys = sorted(piv)

        def summ(means):
            ratio = means / means.min(axis=1, keepdims=True)
            t = ALL.index("TimesFM3")
            return {"tfm_wins": float((ratio[:, t] == 1).sum()),
                    "tfm_worst": float(ratio[:, t].max()),
                    "tfm_meanratio": float(np.exp(np.log(ratio[:, t]).mean())),
                    "tfm_within10": float((ratio[:, t] <= 1.10).mean()),
                    "classical_worst_min": float(ratio[:, :t].max(axis=0).min())}

        point = summ(np.array([np.nanmean(piv[k], axis=0) for k in keys]))
        draws = []
        for _ in range(B):
            draws.append(summ(np.array([np.nanmean(piv[k][RNG.integers(0, len(piv[k]), len(piv[k]))], axis=0)
                                        for k in keys])))
        d = pd.DataFrame(draws)
        for s, val in point.items():
            rows.append({"variant": v, "stat": s, "value": val,
                         "lo": d[s].quantile(0.025), "hi": d[s].quantile(0.975)})
    return pd.DataFrame(rows)


def response(df):
    out = []
    clean = df[df.method.isin(["TimesFM3", "AutoARIMA"])]
    for d, g in clean.groupby("dgp"):
        par = [c for c in g.columns if c.startswith("par_") and g[c].notna().any()]
        w = g.pivot_table(index=["variant", "n", "rep"], columns="method", values="MASE").dropna()
        pv = g[g.method == "TimesFM3"].set_index(["variant", "n", "rep"])[par]
        w = w.join(pv)
        w = w[(w.TimesFM3 > 0) & (w.AutoARIMA > 0)].reset_index()
        w["y"] = np.log2(w.TimesFM3 / w.AutoARIMA)
        w["logn"] = np.log2(w["n"])
        for c in par:
            w[c] = (w[c] - w[c].mean()) / w[c].std()
        f = "y ~ logn + C(variant, Treatment('clean')) + " + " + ".join(par)
        fit = smf.ols(f, data=w).fit(cov_type="HC3")
        ci = fit.conf_int()
        for term in fit.params.index:
            out.append({"dgp": d, "term": term, "coef": fit.params[term], "lo": ci.loc[term, 0],
                        "hi": ci.loc[term, 1], "p": fit.pvalues[term], "n_obs": int(fit.nobs),
                        "r2": fit.rsquared})
    return pd.DataFrame(out)


def estperiod(df):
    rows = []
    for d in ("D4", "D5"):
        e = df[(df.variant == "est_period") & (df.dgp == d) & (df.n == 24)]
        c = df[(df.variant == "clean") & (df.dgp == d) & (df.n == 24)]
        ets = e[e.method == "AutoETS"].MASE.mean()
        rows.append({"dgp": d, "AutoETS_estperiod": ets,
                     "naive_m1_estperiod": e[e.method == "SeasonalNaive"].MASE.mean(),
                     "SeasonalNaive_m12": c[c.method == "SeasonalNaive"].MASE.mean(),
                     "TimesFM3": c[c.method == "TimesFM3"].MASE.mean(),
                     "AutoETS_m12": c[c.method == "AutoETS"].MASE.mean()})
    return pd.DataFrame(rows)


def main():
    df = pd.read_csv(RES / "robust_metrics.csv")
    ex = (df[df.method == "TimesFM3"].assign(bad=lambda x: x.MASE.isna())
          .groupby(["variant", "dgp", "n"]).bad.sum().reset_index())
    ex[ex.bad > 0].to_csv(RES / "robust_excluded.csv", index=False)
    print("excluded:\n", ex[ex.bad > 0].to_string())
    b = boot(df)
    b.to_csv(RES / "robust_boot.csv", index=False)
    print(b.round(3).to_string())
    r = response(df)
    r.to_csv(RES / "robust_response.csv", index=False)
    print(r[~r.term.str.startswith("Intercept")].round(3).to_string())
    e = estperiod(df)
    e.to_csv(RES / "robust_estperiod.csv", index=False)
    print(e.round(3).to_string())


if __name__ == "__main__":
    main()
