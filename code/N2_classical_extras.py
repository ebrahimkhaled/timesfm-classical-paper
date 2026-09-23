"""Revision (JoF referee 1): stronger and standard classical benchmarks on the main design.

Adds, on the same 7,200 series (same seeds and contexts, h = 12):

  DOTM         Dynamic Optimised Theta (Fiorucci et al. 2016), statsforecast
               DynamicOptimizedTheta with the true seasonal period, as the other methods.
  M4Comb       the M4 "Comb" benchmark (Makridakis et al. 2020): arithmetic mean of SES, Holt
               and damped-trend exponential smoothing, fitted to data seasonally adjusted by
               classical multiplicative decomposition when the M4 90% autocorrelation test finds
               seasonality at lag 12 (applied when at least three cycles are observed). Point
               forecasts only, as in M4.
  CombEAD      equal-weight combination of AutoETS, AutoARIMA and DOTM (point mean, vincentized
               deciles), the combination with the weak Theta member replaced.
  Zero         the all-zero forecast, on the intermittent process D8 only (point only).
  AutoARIMA_cf, AutoETS_cf
               the same models with split-conformal prediction intervals (statsforecast
               ConformalIntervals, h = 12, two calibration windows) instead of the Gaussian
               analytic intervals; n in {96, 200} only, since two 12-step calibration windows
               need a long enough context.

Outputs: results/classical_extra/<DGP>_n<n>_r200.npz
Usage:  python code/N2_classical_extras.py --n-jobs 8
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "classical_extra"
OUT.mkdir(parents=True, exist_ok=True)
REPS, H = 200, 12
LEVELS = [20, 40, 60, 80]
_LO_HI = [("lo", 80), ("lo", 60), ("lo", 40), ("lo", 20), None,
          ("hi", 20), ("hi", 40), ("hi", 60), ("hi", 80)]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dgp = _load("dgp", "01_dgp.py")
rd = _load("robust_dgp", "R1_robust_dgp.py")


def _q(fc, model, k, with_levels=True):
    pt = fc[model].to_numpy(float).reshape(k, H)
    q = np.repeat(pt[:, :, None], 9, axis=2)
    if with_levels:
        for i, spec in enumerate(_LO_HI):
            if spec is not None:
                side, lvl = spec
                q[:, :, i] = fc[f"{model}-{side}-{lvl}"].to_numpy(float).reshape(k, H)
    return pt, np.sort(q, axis=2)


def _long(ctx):
    k, n = ctx.shape
    return pd.DataFrame({"unique_id": np.repeat(np.arange(k), n),
                         "ds": np.tile(np.arange(n), k), "y": ctx.ravel()})


def seasonal_indices(x, m=12):
    """Classical multiplicative decomposition indices (centred moving average)."""
    n = len(x)
    w = np.ones(m + 1) / m
    w[0] = w[-1] = 0.5 / m
    trend = np.convolve(x, w, mode="valid")
    off = m // 2
    ratio = np.full(n, np.nan)
    ratio[off:off + len(trend)] = x[off:off + len(trend)] / trend
    idx = np.array([np.nanmean(ratio[i::m]) for i in range(m)])
    return idx / idx.mean()


def m4comb(ctx, n_jobs):
    """SES/Holt/Damped on seasonally adjusted data, reseasonalised; point forecasts."""
    from statsforecast import StatsForecast
    from statsforecast.models import AutoETS
    k, n = ctx.shape
    adj = ctx.copy()
    sfac = np.ones((k, H))
    for i in range(k):
        x = ctx[i]
        if n >= 36 and np.all(x > 0) and rd.m4_seasonality_test(x, 12):
            si = seasonal_indices(x, 12)
            if np.all(np.isfinite(si)) and np.all(si > 0):
                adj[i] = x / si[np.arange(n) % 12]
                sfac[i] = si[np.arange(n, n + H) % 12]
    sf = StatsForecast(models=[AutoETS(model="ANN", alias="SES"),
                               AutoETS(model="AAN", damped=False, alias="Holt"),
                               AutoETS(model="AAN", damped=True, alias="Damped")],
                       freq=1, n_jobs=n_jobs)
    fc = sf.forecast(df=_long(adj), h=H).sort_values(["unique_id", "ds"])
    pts = [fc[a].to_numpy(float).reshape(k, H) for a in ("SES", "Holt", "Damped")]
    return np.mean(pts, axis=0) * sfac


def run_cell(d, n, n_jobs):
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA, AutoETS, DynamicOptimizedTheta
    from statsforecast.utils import ConformalIntervals
    m = dgp.SEASONAL_PERIOD[d]
    s = np.array([dgp.simulate(d, n, r, H) for r in range(REPS)])
    ctx = s[:, :n]
    store = {}
    sf = StatsForecast(models=[DynamicOptimizedTheta(season_length=m, alias="DOTM")],
                       freq=1, n_jobs=n_jobs)
    fc = sf.forecast(df=_long(ctx), h=H, level=LEVELS).sort_values(["unique_id", "ds"])
    store["DOTM_pt"], store["DOTM_q"] = _q(fc, "DOTM", REPS)
    pt = m4comb(ctx, n_jobs)
    store["M4Comb_pt"], store["M4Comb_q"] = pt, np.repeat(pt[:, :, None], 9, axis=2)
    base = np.load(ROOT / "results" / "forecasts" / f"classical_{d}_n{n}_r{REPS}.npz")
    parts_pt = [base["AutoETS_pt"], base["AutoARIMA_pt"], store["DOTM_pt"]]
    parts_q = [base["AutoETS_q"], base["AutoARIMA_q"], store["DOTM_q"]]
    store["CombEAD_pt"] = np.mean(parts_pt, axis=0)
    store["CombEAD_q"] = np.sort(np.mean(parts_q, axis=0), axis=2)
    if d == "D8":
        z = np.zeros((REPS, H))
        store["Zero_pt"], store["Zero_q"] = z, np.zeros((REPS, H, 9))
    if n >= 96:
        ci = ConformalIntervals(h=H, n_windows=2)
        sfc = StatsForecast(models=[AutoARIMA(season_length=m, alias="AutoARIMA_cf",
                                              prediction_intervals=ci),
                                    AutoETS(season_length=m, alias="AutoETS_cf",
                                            prediction_intervals=ci)],
                            freq=1, n_jobs=n_jobs)
        fcc = sfc.forecast(df=_long(ctx), h=H, level=LEVELS).sort_values(["unique_id", "ds"])
        for a in ("AutoARIMA_cf", "AutoETS_cf"):
            store[f"{a}_pt"], store[f"{a}_q"] = _q(fcc, a, REPS)
    return store


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-jobs", type=int, default=8)
    args = ap.parse_args()
    for d in dgp.DGP_IDS:
        for n in dgp.LENGTHS:
            f = OUT / f"{d}_n{n}_r{REPS}.npz"
            if f.exists():
                continue
            t0 = time.time()
            store = run_cell(d, n, args.n_jobs)
            np.savez_compressed(f, **store)
            print(f"{d} n={n}: {time.time() - t0:.0f}s  {sorted(k[:-3] for k in store if k.endswith('_pt'))}",
                  flush=True)


if __name__ == "__main__":
    main()
