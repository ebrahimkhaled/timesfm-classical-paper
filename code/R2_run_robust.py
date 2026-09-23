"""Robustness study, part 2: run every method on the randomised-parameter series.

Same three-phase structure as 03_run_forecasts.py (classical in a process pool, then TimesFM-3,
then metrics), with the variant as an extra cell index. Metrics are computed over the full
horizon h = 1..12 only.

  est_period  classical methods are refitted with the estimated period; TimesFM-3 reuses the
              clean forecasts, since the series are identical and it never receives a period.
  D8          CrostonSBA, TSB and ADIDA are added, as in the main study's intermittent section.

Usage:
    python code/R2_run_robust.py --reps 100            # full run
    python code/R2_run_robust.py --reps 5 --tag pilot  # pilot
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
FC_DIR = ROOT / "results" / "robust" / "forecasts"
OUT_DIR = ROOT / "results" / "robust"
FC_DIR.mkdir(parents=True, exist_ok=True)


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rd = _load("robust_dgp", "R1_robust_dgp.py")
mx = _load("metrics", "02_metrics.py")

LEVELS = [20, 40, 60, 80]
_LO_HI = [("lo", 80), ("lo", 60), ("lo", 40), ("lo", 20), None,
          ("hi", 20), ("hi", 40), ("hi", 60), ("hi", 80)]
CLASSICAL = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA"]
COMBO_PARTS = ["Theta", "AutoETS", "AutoARIMA"]
CROSTON = ["CrostonSBA", "TSB", "ADIDA"]


def cell(dgp_id: str, n: int, reps: int, variant: str):
    gen_variant = "clean" if variant == "est_period" else variant
    out = [rd.simulate(dgp_id, n, r, gen_variant) for r in range(reps)]
    series = np.array([o[0] for o in out])
    return series[:, :n], series[:, n:], [o[1] for o in out]


def _quantiles(fc: pd.DataFrame, model: str, k: int, h: int, with_levels: bool):
    point = fc[model].to_numpy(dtype=float).reshape(k, h)
    qs = np.repeat(point[:, :, None], 9, axis=2)
    if with_levels:
        for i, spec in enumerate(_LO_HI):
            if spec is not None:
                side, lvl = spec
                qs[:, :, i] = fc[f"{model}-{side}-{lvl}"].to_numpy(dtype=float).reshape(k, h)
    return point, np.sort(qs, axis=2)


def _run_sf(contexts: np.ndarray, m: int, h: int, n_jobs: int, intermittent: bool):
    from statsforecast import StatsForecast
    from statsforecast.models import (ADIDA, TSB, AutoARIMA, AutoETS, CrostonSBA,
                                      SeasonalNaive, Theta)
    k, n = contexts.shape
    long = pd.DataFrame({"unique_id": np.repeat(np.arange(k), n),
                         "ds": np.tile(np.arange(n), k), "y": contexts.ravel()})
    models = [SeasonalNaive(season_length=m), Theta(season_length=m),
              AutoETS(season_length=m), AutoARIMA(season_length=m)]
    sf = StatsForecast(models=models, freq=1, n_jobs=n_jobs)
    fc = sf.forecast(df=long, h=h, level=LEVELS).sort_values(["unique_id", "ds"])
    store = {}
    for model in CLASSICAL:
        store[model] = _quantiles(fc, model, k, h, True)
    if intermittent:
        sf2 = StatsForecast(models=[CrostonSBA(), TSB(alpha_d=0.2, alpha_p=0.2), ADIDA()],
                            freq=1, n_jobs=n_jobs)
        fc2 = sf2.forecast(df=long, h=h).sort_values(["unique_id", "ds"])
        for model in CROSTON:
            store[model] = _quantiles(fc2, model, k, h, False)
    return store


def phase_a(dgp_id, n, reps, variant, h, n_jobs):
    contexts, _, _ = cell(dgp_id, n, reps, variant)
    periods = np.array([rd.period_for(dgp_id, c, variant) for c in contexts])
    intermittent = dgp_id == "D8"
    names = CLASSICAL + (CROSTON if intermittent else [])
    pts = {k: np.full((reps, h), np.nan) for k in names}
    qss = {k: np.full((reps, h, 9), np.nan) for k in names}
    t0 = time.time()
    for m in np.unique(periods):
        idx = np.where(periods == m)[0]
        store = _run_sf(contexts[idx], int(m), h, n_jobs, intermittent)
        for k, (pt, qs) in store.items():
            pts[k][idx], qss[k][idx] = pt, qs
    save = {}
    for k in names:
        save[f"{k}_pt"], save[f"{k}_q"] = pts[k], qss[k]
    save["Combination_pt"] = np.mean([pts[k] for k in COMBO_PARTS], axis=0)
    save["Combination_q"] = np.sort(np.mean([qss[k] for k in COMBO_PARTS], axis=0), axis=2)
    np.savez_compressed(FC_DIR / f"classical_{variant}_{dgp_id}_n{n}_r{reps}.npz",
                        periods=periods, secs=np.array([time.time() - t0]), **save)


def phase_b(dgp_id, n, reps, variant, h, forecaster):
    contexts, _, _ = cell(dgp_id, n, reps, variant)
    outs = list(forecaster.predict_batch(contexts=[c.astype(np.float32) for c in contexts],
                                         horizon=h, return_quantiles=True))
    pt = np.array([np.asarray(o.forecast, dtype=float).ravel()[:h] for o in outs])
    qs = np.sort(np.array([np.asarray(o.quantiles, dtype=float)[:h, :9] for o in outs]), axis=2)
    np.savez_compressed(FC_DIR / f"timesfm_{variant}_{dgp_id}_n{n}_r{reps}.npz",
                        TimesFM3_pt=pt, TimesFM3_q=qs)


def phase_c(dgp_id, n, reps, variant, h) -> pd.DataFrame:
    m_true = rd.TRUE_PERIOD[dgp_id]
    contexts, truths, params = cell(dgp_id, n, reps, variant)
    cl = np.load(FC_DIR / f"classical_{variant}_{dgp_id}_n{n}_r{reps}.npz")
    tf_variant = "clean" if variant == "est_period" else variant
    tf = np.load(FC_DIR / f"timesfm_{tf_variant}_{dgp_id}_n{n}_r{reps}.npz")
    names = [k[:-3] for k in cl.files if k.endswith("_pt")]
    preds = {k: (cl[f"{k}_pt"], cl[f"{k}_q"]) for k in names}
    preds["TimesFM3"] = (tf["TimesFM3_pt"], tf["TimesFM3_q"])
    rows = []
    for method, (pt, qs) in preds.items():
        for r in range(reps):
            res = mx.evaluate(truths[r], pt[r], qs[r], contexts[r], m_true)
            rows.append({"variant": variant, "dgp": dgp_id, "n": n, "rep": r, "method": method,
                         "period_used": int(cl["periods"][r]),
                         **{f"par_{k}": v for k, v in params[r].items()}, **res})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--dgps", default=",".join(rd.DGP_IDS))
    ap.add_argument("--lengths", default=",".join(map(str, rd.LENGTHS)))
    ap.add_argument("--variants", default=",".join(rd.VARIANTS))
    ap.add_argument("--phase", default="ABC")
    ap.add_argument("--tag", default="robust")
    ap.add_argument("--n-jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    args = ap.parse_args()
    cells = [(v, d, int(n)) for v in args.variants.split(",") for d in args.dgps.split(",")
             for n in args.lengths.split(",")]
    reps, h = args.reps, rd.HORIZON
    t0 = time.time()

    if "A" in args.phase:
        for i, (v, d, n) in enumerate(cells, 1):
            f = FC_DIR / f"classical_{v}_{d}_n{n}_r{reps}.npz"
            if f.exists():
                continue
            s = time.time()
            phase_a(d, n, reps, v, h, args.n_jobs)
            print(f"A [{i}/{len(cells)}] {v} {d} n={n}: {time.time() - s:.0f}s", flush=True)

    if "B" in args.phase:
        import timesfm
        fc = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
        for i, (v, d, n) in enumerate(cells, 1):
            if v == "est_period":
                continue
            f = FC_DIR / f"timesfm_{v}_{d}_n{n}_r{reps}.npz"
            if f.exists():
                continue
            phase_b(d, n, reps, v, h, fc)
            print(f"B [{i}/{len(cells)}] {v} {d} n={n}", flush=True)

    if "C" in args.phase:
        frames = [phase_c(d, n, reps, v, h) for v, d, n in cells]
        allm = pd.concat(frames, ignore_index=True)
        allm.to_csv(OUT_DIR / f"{args.tag}_metrics.csv", index=False)
        print(f"C wrote {args.tag}_metrics.csv ({len(allm):,} rows)", flush=True)
    print(f"done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
