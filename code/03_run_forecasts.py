"""P3: run every method over every simulated series and write per-series metrics.

Structure
---------
The run is split into three phases, executed in this order inside one process:

  Phase A  classical forecasts, with statsforecast's process pool at full width.
  Phase B  TimesFM-3 forecasts.
  Phase C  metrics, merging the two.

The ordering is not cosmetic. On Windows the statsforecast pool uses *spawn*, so every
worker re-imports this module. If the 330M-parameter TimesFM-3 model is already resident
in the parent when the pool starts, 24 workers exhaust memory (WinError 8, observed).
Importing `timesfm` only in Phase B -- after all pooled work is finished -- keeps the
workers lightweight and lets Phase A run in parallel.

Each phase caches to disk per (DGP, length) cell, so the run is resumable and any phase can
be re-run alone.

Usage
-----
    python code/03_run_forecasts.py                 # full run
    python code/03_run_forecasts.py --reps 5        # quick pilot
    python code/03_run_forecasts.py --phase C       # recompute metrics only
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
FC_DIR = ROOT / "results" / "forecasts"
CELL_DIR = ROOT / "results" / "cells"
for _d in (FC_DIR, CELL_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dgp = _load("dgp", "01_dgp.py")
mx = _load("metrics", "02_metrics.py")

# Interval level L yields lo/hi at quantiles (1-L/100)/2 and 1-(1-L/100)/2, so
# 80 -> 0.10/0.90, 60 -> 0.20/0.80, 40 -> 0.30/0.70, 20 -> 0.40/0.60.
LEVELS = [20, 40, 60, 80]
_LO_HI = [("lo", 80), ("lo", 60), ("lo", 40), ("lo", 20),
          None,  # q0.5 is the point forecast
          ("hi", 20), ("hi", 40), ("hi", 60), ("hi", 80)]

CLASSICAL = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA"]
COMBO_PARTS = ["Theta", "AutoETS", "AutoARIMA"]
ALL_METHODS = CLASSICAL + ["Combination", "TimesFM3"]
HORIZON_SLICES = {"h1": slice(0, 1), "h1_6": slice(0, 6), "h1_12": slice(0, 12)}


def cell_series(dgp_id: str, n: int, reps: int, horizon: int):
    """Regenerate a cell's series. Deterministic, so every phase sees identical data."""
    series = np.array([dgp.simulate(dgp_id, n, r, horizon) for r in range(reps)])
    return series[:, :n], series[:, n:]


def _classical_quantiles(fc: pd.DataFrame, model: str, n_series: int, h: int):
    point = fc[model].to_numpy(dtype=float).reshape(n_series, h)
    qs = np.empty((n_series, h, 9), dtype=float)
    for i, spec in enumerate(_LO_HI):
        if spec is None:
            qs[:, :, i] = point
        else:
            side, lvl = spec
            qs[:, :, i] = fc[f"{model}-{side}-{lvl}"].to_numpy(dtype=float).reshape(n_series, h)
    # Intervals can cross when a model is fitted on a very short series.
    return point, np.sort(qs, axis=2)


# ------------------------------------------------------------------ Phase A
def phase_a(dgp_id: str, n: int, reps: int, horizon: int, n_jobs: int) -> float:
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA, AutoETS, Theta, SeasonalNaive

    m = dgp.SEASONAL_PERIOD[dgp_id]
    contexts, _ = cell_series(dgp_id, n, reps, horizon)
    long = pd.DataFrame({
        "unique_id": np.repeat(np.arange(reps), n),
        "ds": np.tile(np.arange(n), reps),
        "y": contexts.ravel(),
    })
    sf = StatsForecast(
        models=[SeasonalNaive(season_length=m), Theta(season_length=m),
                AutoETS(season_length=m), AutoARIMA(season_length=m)],
        freq=1, n_jobs=n_jobs,
    )
    t0 = time.time()
    fc = sf.forecast(df=long, h=horizon, level=LEVELS).sort_values(["unique_id", "ds"])
    secs = time.time() - t0

    store = {}
    for model in CLASSICAL:
        pt, qs = _classical_quantiles(fc, model, reps, horizon)
        store[f"{model}_pt"], store[f"{model}_q"] = pt, qs
    # Combination: equal-weight mean of point forecasts; the predictive distribution is the
    # average of the component quantile functions (vincentization).
    store["Combination_pt"] = np.mean([store[f"{k}_pt"] for k in COMBO_PARTS], axis=0)
    store["Combination_q"] = np.sort(
        np.mean([store[f"{k}_q"] for k in COMBO_PARTS], axis=0), axis=2)

    np.savez_compressed(FC_DIR / f"classical_{dgp_id}_n{n}_r{reps}.npz",
                        secs=np.array([secs]), **store)
    return secs


# ------------------------------------------------------------------ Phase B
def phase_b(dgp_id: str, n: int, reps: int, horizon: int, forecaster) -> float:
    contexts, _ = cell_series(dgp_id, n, reps, horizon)
    t0 = time.time()
    outs = list(forecaster.predict_batch(
        contexts=[c.astype(np.float32) for c in contexts],
        horizon=horizon, return_quantiles=True,
    ))
    secs = time.time() - t0
    pt = np.array([np.asarray(o.forecast, dtype=float).ravel()[:horizon] for o in outs])
    qs = np.sort(np.array([np.asarray(o.quantiles, dtype=float)[:horizon, :9] for o in outs]),
                 axis=2)
    np.savez_compressed(FC_DIR / f"timesfm_{dgp_id}_n{n}_r{reps}.npz",
                        TimesFM3_pt=pt, TimesFM3_q=qs, secs=np.array([secs]))
    return secs


# ------------------------------------------------------------------ Phase C
def phase_c(dgp_id: str, n: int, reps: int, horizon: int) -> pd.DataFrame:
    m = dgp.SEASONAL_PERIOD[dgp_id]
    contexts, truths = cell_series(dgp_id, n, reps, horizon)
    cl = np.load(FC_DIR / f"classical_{dgp_id}_n{n}_r{reps}.npz")
    tf = np.load(FC_DIR / f"timesfm_{dgp_id}_n{n}_r{reps}.npz")

    preds = {k: (cl[f"{k}_pt"], cl[f"{k}_q"]) for k in CLASSICAL + ["Combination"]}
    preds["TimesFM3"] = (tf["TimesFM3_pt"], tf["TimesFM3_q"])
    secs = {"classical_cell_secs": float(cl["secs"][0]),
            "timesfm_cell_secs": float(tf["secs"][0])}

    rows = []
    for method, (pt, qs) in preds.items():
        for r in range(reps):
            for slice_name, sl in HORIZON_SLICES.items():
                res = mx.evaluate(truths[r][sl], pt[r][sl], qs[r][sl], contexts[r], m)
                rows.append({
                    "dgp": dgp_id, "n": n, "rep": r, "method": method,
                    "horizon_slice": slice_name, "m": m,
                    "correct_model": dgp.CORRECT_MODEL[dgp_id],
                    **secs, **res,
                })
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--dgps", type=str, default=",".join(dgp.DGP_IDS))
    ap.add_argument("--lengths", type=str, default=",".join(map(str, dgp.LENGTHS)))
    ap.add_argument("--horizon", type=int, default=dgp.HORIZON)
    ap.add_argument("--tag", type=str, default="main")
    ap.add_argument("--phase", type=str, default="ABC", help="subset of ABC to run")
    ap.add_argument("--n-jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    dgp_ids = args.dgps.split(",")
    lengths = [int(x) for x in args.lengths.split(",")]
    cells = [(d, n) for d in dgp_ids for n in lengths]
    reps, H = args.reps, args.horizon
    grand0 = time.time()

    # ---- Phase A: classical (parallel; torch is NOT imported yet) ----
    if "A" in args.phase:
        print(f"PHASE A - classical forecasts (n_jobs={args.n_jobs})", flush=True)
        for i, (d, n) in enumerate(cells, 1):
            f = FC_DIR / f"classical_{d}_n{n}_r{reps}.npz"
            if f.exists() and not args.force:
                print(f"  [{i}/{len(cells)}] {d} n={n}: cached", flush=True)
                continue
            secs = phase_a(d, n, reps, H, args.n_jobs)
            print(f"  [{i}/{len(cells)}] {d} n={n}: {secs:.1f}s", flush=True)

    # ---- Phase B: TimesFM-3 (torch loaded only now) ----
    if "B" in args.phase:
        import timesfm
        print("PHASE B - TimesFM-3; loading model ...", flush=True)
        t0 = time.time()
        forecaster = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
        print(f"  loaded in {time.time() - t0:.1f}s", flush=True)
        for i, (d, n) in enumerate(cells, 1):
            f = FC_DIR / f"timesfm_{d}_n{n}_r{reps}.npz"
            if f.exists() and not args.force:
                print(f"  [{i}/{len(cells)}] {d} n={n}: cached", flush=True)
                continue
            secs = phase_b(d, n, reps, H, forecaster)
            print(f"  [{i}/{len(cells)}] {d} n={n}: {secs:.1f}s", flush=True)

    # ---- Phase C: metrics ----
    if "C" in args.phase:
        print("PHASE C - metrics", flush=True)
        frames = []
        for i, (d, n) in enumerate(cells, 1):
            out = CELL_DIR / f"{args.tag}_{d}_n{n}_r{reps}.csv"
            if out.exists() and not args.force:
                frames.append(pd.read_csv(out))
                continue
            df = phase_c(d, n, reps, H)
            df.to_csv(out, index=False)
            frames.append(df)
            print(f"  [{i}/{len(cells)}] {d} n={n}: {len(df):,} rows", flush=True)
        allm = pd.concat(frames, ignore_index=True)
        allm.to_csv(ROOT / "results" / "all_metrics.csv", index=False)
        print(f"  wrote results/all_metrics.csv ({len(allm):,} rows)", flush=True)

    print(f"\ndone in {(time.time() - grand0) / 60:.1f} min")


if __name__ == "__main__":
    main()
