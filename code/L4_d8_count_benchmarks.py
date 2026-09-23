"""Referee round 3: count-data probabilistic benchmarks for the intermittent process D8.

The referee asked for iETS / count-distribution Croston-type benchmarks in place of Gaussian
intervals. Three predictive distributions are scored on the same 4 x 200 D8 series as the paper
(context = first n, truth = last 12, series with a zero MASE denominator skipped):

  iETS     smooth::adam(y, "MNN", occurrence = "auto") in R (code/L4_d8_iets.R); deciles from
           10,000 simulated paths, point = conditional mean.
  NegBin   i.i.d. negative binomial fitted by maximum likelihood to the whole context (zeros
           included); the MLE of the mean is the sample mean and the size parameter is found by
           profile likelihood. Poisson is used when the context is not over-dispersed (counted).
           Deciles are the discrete NB quantiles, point = mean.
  TSBcomp  compound Bernoulli x empirical size: occurrence probability p from TSB's SES update
           of the demand indicator (alpha_p = 0.2, statsforecast's own _ses_forecast, so p is
           exactly statsforecast TSB's probability), sizes = empirical distribution of the
           non-zero context values. q-quantile = 0 if q <= 1 - p, else the empirical size
           quantile at (q - (1 - p)) / p (inverted-CDF). Point = p * mean(non-zero sizes).

For each method the point forecast is the predictive mean; MASE of the predictive median
(MASE_med) is reported alongside. Metrics come from code/02_metrics.py; sME and sPIS as in
code/N4_revision_analysis.py.

Outputs (results/round3/):
  d8_count_series.csv           context values handed to R
  d8_count_iets_forecasts.csv   iETS means and deciles (written by the R helper)
  d8_count_per_series.csv       per-series metrics for the three benchmarks
  d8_count_benchmarks.csv       n, method, MASE, RMSSE, sME, sPIS, SPL, failures (+ extras)
  d8_count_comparison.csv       the new benchmarks next to TimesFM-3 and the history benchmark
"""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import optimize, stats, special

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
dgp = importlib.import_module("01_dgp")
met = importlib.import_module("02_metrics")
from statsforecast.models import _probability, _ses_forecast  # noqa: E402

OUT = ROOT / "results" / "round3"
OUT.mkdir(parents=True, exist_ok=True)
NS = [24, 48, 96, 200]
REPS = 200
H = 12
LV = met.QUANTILE_LEVELS
RSCRIPT = os.environ.get("RSCRIPT", "Rscript")


# ------------------------------------------------------------------ data
def load_series():
    out = {}
    for n in NS:
        for r in range(REPS):
            y = dgp.simulate("D8", n, r, H)
            out[(n, r)] = (y[:n], y[n:n + H])
    return out


# ------------------------------------------------------------------ negative binomial
def nb_fit(x: np.ndarray):
    """ML negative binomial (size r, mean mu). Returns (dist, used_poisson)."""
    mu = float(x.mean())
    var = float(x.var(ddof=0))
    if var <= mu or mu <= 0:
        return stats.poisson(mu), True

    def nll(logr):
        r = np.exp(logr)
        return -np.sum(special.gammaln(x + r) - special.gammaln(r) - special.gammaln(x + 1)
                       + r * np.log(r / (r + mu)) + x * np.log(mu / (r + mu)))

    r0 = mu * mu / (var - mu)  # method-of-moments start
    res = optimize.minimize_scalar(nll, bounds=(np.log(r0) - 8, np.log(r0) + 8), method="bounded")
    r = float(np.exp(res.x))
    if r > 1e6:
        return stats.poisson(mu), True
    return stats.nbinom(r, r / (r + mu)), False


def nb_forecast(ctx):
    dist, pois = nb_fit(ctx)
    q = np.tile(dist.ppf(LV), (H, 1)).astype(float)
    return np.full(H, float(dist.mean())), q, np.full(H, float(dist.median())), pois


# ------------------------------------------------------------------ TSB compound
def tsb_compound_forecast(ctx, alpha_p=0.2):
    p, _ = _ses_forecast(_probability(ctx.astype(float)), alpha_p)
    p = float(np.clip(p, 0.0, 1.0))
    sizes = np.sort(ctx[ctx > 0].astype(float))
    qv = np.zeros(len(LV))
    for i, lv in enumerate(LV):
        if p > 0 and lv > 1 - p:
            u = (lv - (1 - p)) / p
            qv[i] = np.quantile(sizes, u, method="inverted_cdf")
    med = 0.0 if p <= 0.5 else float(np.quantile(sizes, (0.5 - (1 - p)) / p, method="inverted_cdf"))
    return np.full(H, p * sizes.mean()), np.tile(qv, (H, 1)), np.full(H, med)


# ------------------------------------------------------------------ iETS via R
def run_iets(series):
    rows = [{"n": n, "rep": r, "t": t + 1, "y": v}
            for (n, r), (ctx, _) in series.items() for t, v in enumerate(ctx)]
    pd.DataFrame(rows).to_csv(OUT / "d8_count_series.csv", index=False)
    t0 = time.time()
    subprocess.run([RSCRIPT, str(ROOT / "code" / "L4_d8_iets.R")], check=True)
    print(f"R iETS wall time: {time.time() - t0:.1f} s", flush=True)


def load_iets():
    f = pd.read_csv(OUT / "d8_count_iets_forecasts.csv", keep_default_na=False,
                    na_values=["NA"]).sort_values(["n", "rep", "h"])
    qcols = [f"q{int(round(100 * lv)):02d}" for lv in LV]
    out = {}
    for (n, r), g in f.groupby(["n", "rep"]):
        err = str(g["error"].iloc[0])
        out[(int(n), int(r))] = (g["mean"].to_numpy(float), g[qcols].to_numpy(float),
                                 g["q50"].to_numpy(float), err, str(g["occurrence"].iloc[0]))
    return out


# ------------------------------------------------------------------ scoring
def score(ctx, act, pt, q, med):
    den = met.mase_denominator(ctx, 1)
    den2 = met.rmsse_denominator(ctx, 1)
    cm = ctx.mean()
    q = np.maximum.accumulate(q, axis=1)  # guard against simulation noise in monotonicity
    return {"MASE": met.mase(act, pt, den), "RMSSE": met.rmsse(act, pt, den2),
            "sME": float(np.mean(pt - act) / den),
            "sPIS": float(-np.sum(np.cumsum(act - pt)) / cm) if cm > 0 else np.nan,
            "SPL": met.scaled_pinball_loss(act, q, den), "MASE_med": met.mase(act, med, den),
            "cover80": met.interval_coverage(act, q[:, 0], q[:, 8])}


def main():
    t_start = time.time()
    series = load_series()
    if os.environ.get("SKIP_R") != "1" or not (OUT / "d8_count_iets_forecasts.csv").exists():
        run_iets(series)
    iets = load_iets()

    rows = []
    for (n, r), (ctx, act) in series.items():
        if not np.isfinite(met.mase_denominator(ctx, 1)):
            continue
        base = {"n": n, "rep": r}
        pt, q, med, err, occ = iets[(n, r)]
        if err == "":
            rows.append({**base, "method": "iETS", "failed": 0, "fallback": 0, "occurrence": occ,
                         **score(ctx, act, pt, q, med)})
        else:
            rows.append({**base, "method": "iETS", "failed": 1, "fallback": 0, "error": err})
        pt, q, med, pois = nb_forecast(ctx)
        rows.append({**base, "method": "NegBin", "failed": 0, "fallback": int(pois),
                     **score(ctx, act, pt, q, med)})
        pt, q, med = tsb_compound_forecast(ctx)
        rows.append({**base, "method": "TSBcomp", "failed": 0, "fallback": 0,
                     **score(ctx, act, pt, q, med)})
    per = pd.DataFrame(rows)
    per.to_csv(OUT / "d8_count_per_series.csv", index=False)

    metrics = ["MASE", "RMSSE", "sME", "sPIS", "SPL"]
    agg = per.groupby(["n", "method"]).agg(
        **{m: (m, "mean") for m in metrics}, failures=("failed", "sum"),
        MASE_med=("MASE_med", "mean"), cover80=("cover80", "mean"),
        poisson_fallbacks=("fallback", "sum"), series=("rep", "size")).reset_index()
    agg.to_csv(OUT / "d8_count_benchmarks.csv", index=False)

    # comparison with the existing tables
    ref = pd.read_csv(ROOT / "results" / "revision" / "d8_table.csv")
    ref = ref[ref.method.isin(["TimesFM3", "TimesFM3mean", "AutoARIMA", "CrostonSBA", "TSB"])]
    hist = pd.read_csv(ROOT / "results" / "round2" / "d8_benchmarks.csv")
    hist = hist.assign(method=hist.method.replace({"EmpiricalMedian": "History(deciles,median)",
                                                   "ContextMean": "History(mean)"}))
    comp = pd.concat([ref, hist, agg[["n", "method", *metrics]]], ignore_index=True)
    comp.to_csv(OUT / "d8_count_comparison.csv", index=False)

    pd.set_option("display.width", 200)
    for m in ["SPL", "RMSSE", "MASE", "sME"]:
        print(f"\n{m} by length")
        print(comp.pivot(index="method", columns="n", values=m).round(4).to_string())
    print("\nnew benchmarks: failures / MASE of median / 80% coverage / Poisson fallbacks")
    print(agg[["n", "method", "series", "failures", "MASE_med", "cover80",
               "poisson_fallbacks"]].round(4).to_string(index=False))
    ok = per[(per.method == "iETS") & (per.failed == 0)]
    print("\niETS occurrence models chosen:", ok.occurrence.value_counts().to_dict())
    print(f"\ntotal wall time: {time.time() - t_start:.1f} s")


if __name__ == "__main__":
    main()
