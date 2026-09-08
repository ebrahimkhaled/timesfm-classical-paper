"""P5: the real-data tier -- M4 Monthly, rolling-origin evaluation.

Why M4 Monthly
--------------
AJS rule C1.application warns against toy data. M4 Monthly supplies 48,000 real series of
substantial length from a documented, refereed competition \\citep{makridakis2020m4}, so
published results exist against which our classical baselines can be sanity-checked. We draw
a seeded random sample of 1,000 series and use M4's own monthly horizon, h = 18.

Contamination warning
---------------------
M4 is almost certainly inside TimesFM-3's pre-training corpus: Meyer et al. (2025) found only
~6% of the 401 datasets used across 22 foundation models had never appeared in any model's
pre-training. This tier is therefore reported as SECONDARY evidence and is explicitly labelled
contamination-suspect. It exists to show which simulated regime real series resemble, not to
establish which method is better -- that claim rests on the simulation tier, where
contamination is impossible by construction.

Why Diebold-Mariano is used HERE but not in the simulation
----------------------------------------------------------
Rolling-origin evaluation produces, for each series, a sequence of loss differentials indexed
by origin. That sequence is autocorrelated, which is exactly the setting Diebold-Mariano was
designed for, and the Harvey-Leybourne-Newbold correction handles the small number of origins.
In the simulation tier the replications are independent, so a paired rank test is correct
there instead.

Usage:
    python code/07_realdata.py --phase A     # classical (parallel, no torch loaded)
    python code/07_realdata.py --phase BC    # TimesFM-3, then metrics
"""

from __future__ import annotations

import argparse
import importlib.util
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RES = ROOT / "results"
for _d in (DATA, RES):
    _d.mkdir(parents=True, exist_ok=True)

mx_spec = importlib.util.spec_from_file_location("metrics", ROOT / "code" / "02_metrics.py")
mx = importlib.util.module_from_spec(mx_spec)
mx_spec.loader.exec_module(mx)

HORIZON = 18          # M4's official monthly horizon
SEASON = 12
N_SERIES = 1000
N_ORIGINS = 3         # rolling origins per series
ORIGIN_STEP = 12      # months between successive origins
MIN_LEN = 120         # need enough history to roll back N_ORIGINS
SEED = 20260908

LEVELS = [20, 40, 60, 80]
_LO_HI = [("lo", 80), ("lo", 60), ("lo", 40), ("lo", 20), None,
          ("hi", 20), ("hi", 40), ("hi", 60), ("hi", 80)]
CLASSICAL = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA"]
COMBO_PARTS = ["Theta", "AutoETS", "AutoARIMA"]


def load_m4_sample() -> pd.DataFrame:
    """Load M4 Monthly and take a seeded sample of long-enough series."""
    cache = DATA / f"m4_monthly_sample_{N_SERIES}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)

    from datasetsforecast.m4 import M4
    print("downloading M4 Monthly ...", flush=True)
    train, _, _ = M4.load(directory=str(DATA / "m4_raw"), group="Monthly")
    train = train.rename(columns={"unique_id": "unique_id", "ds": "ds", "y": "y"})

    lens = train.groupby("unique_id").size()
    eligible = lens[lens >= MIN_LEN + HORIZON].index.to_numpy()
    rng = np.random.default_rng(SEED)
    keep = rng.choice(eligible, size=min(N_SERIES, len(eligible)), replace=False)
    sample = train[train.unique_id.isin(keep)].copy()
    sample.to_parquet(cache, index=False)
    print(f"  {len(keep):,} series of {len(eligible):,} eligible "
          f"(of {lens.size:,} total); cached", flush=True)
    return sample


def build_windows(sample: pd.DataFrame):
    """Slice each series into N_ORIGINS (context, truth) pairs."""
    windows = []
    for uid, g in sample.groupby("unique_id", sort=True):
        y = g.sort_values("ds")["y"].to_numpy(dtype=float)
        for k in range(N_ORIGINS):
            end = len(y) - k * ORIGIN_STEP
            ctx_end = end - HORIZON
            if ctx_end < MIN_LEN:
                continue
            windows.append({"unique_id": uid, "origin": k,
                            "context": y[:ctx_end], "truth": y[ctx_end:end]})
    return windows


def _classical_quantiles(fc: pd.DataFrame, model: str, n_w: int, h: int):
    point = fc[model].to_numpy(dtype=float).reshape(n_w, h)
    qs = np.empty((n_w, h, 9))
    for i, spec in enumerate(_LO_HI):
        if spec is None:
            qs[:, :, i] = point
        else:
            side, lvl = spec
            qs[:, :, i] = fc[f"{model}-{side}-{lvl}"].to_numpy(dtype=float).reshape(n_w, h)
    return point, np.sort(qs, axis=2)


def phase_a(windows, n_jobs: int) -> None:
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA, AutoETS, Theta, SeasonalNaive

    rows = []
    for i, w in enumerate(windows):
        c = w["context"]
        # ZERO-PADDED ids are essential. statsforecast returns rows sorted lexicographically by
        # unique_id, so plain str(i) orders them "0","1","10","100","1000",... and any reshape
        # that assumes numeric order silently matches forecasts to the WRONG series. Padding to
        # a fixed width makes lexicographic order identical to numeric order.
        rows.append(pd.DataFrame({"unique_id": f"{i:07d}", "ds": np.arange(len(c)), "y": c}))
    long = pd.concat(rows, ignore_index=True)
    order = list(range(len(windows)))  # identity, guaranteed by the zero padding above

    sf = StatsForecast(
        models=[SeasonalNaive(season_length=SEASON), Theta(season_length=SEASON),
                AutoETS(season_length=SEASON), AutoARIMA(season_length=SEASON)],
        freq=1, n_jobs=n_jobs,
    )
    print(f"fitting {len(windows):,} windows x 4 models (n_jobs={n_jobs}) ...", flush=True)
    t0 = time.time()
    fc = sf.forecast(df=long, h=HORIZON, level=LEVELS)
    print(f"  done in {(time.time() - t0) / 60:.1f} min", flush=True)
    fc["_k"] = fc["unique_id"].astype(str)
    fc = fc.sort_values(["_k", "ds"])

    store = {}
    for model in CLASSICAL:
        pt, qs = _classical_quantiles(fc, model, len(windows), HORIZON)
        store[f"{model}_pt"], store[f"{model}_q"] = pt, qs
    store["Combination_pt"] = np.mean([store[f"{k}_pt"] for k in COMBO_PARTS], axis=0)
    store["Combination_q"] = np.sort(
        np.mean([store[f"{k}_q"] for k in COMBO_PARTS], axis=0), axis=2)
    store["_order"] = np.array(order)
    np.savez_compressed(RES / "realdata_classical.npz", **store)
    print(f"  wrote results/realdata_classical.npz", flush=True)


def phase_b(windows) -> None:
    import timesfm
    print("loading TimesFM-3 ...", flush=True)
    fc = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    ctxs = [w["context"].astype(np.float32) for w in windows]
    t0 = time.time()
    outs = list(fc.predict_batch(contexts=ctxs, horizon=HORIZON, return_quantiles=True))
    print(f"  forecast {len(ctxs):,} windows in {time.time() - t0:.1f}s", flush=True)
    pt = np.array([np.asarray(o.forecast, float).ravel()[:HORIZON] for o in outs])
    qs = np.sort(np.array([np.asarray(o.quantiles, float)[:HORIZON, :9] for o in outs]), axis=2)
    np.savez_compressed(RES / "realdata_timesfm.npz", TimesFM3_pt=pt, TimesFM3_q=qs)
    print("  wrote results/realdata_timesfm.npz", flush=True)


def phase_c(windows) -> None:
    cl = np.load(RES / "realdata_classical.npz")
    tf = np.load(RES / "realdata_timesfm.npz")
    preds = {k: (cl[f"{k}_pt"], cl[f"{k}_q"]) for k in CLASSICAL + ["Combination"]}
    preds["TimesFM3"] = (tf["TimesFM3_pt"], tf["TimesFM3_q"])

    rows = []
    for j, w in enumerate(windows):
        for method, (pt, qs) in preds.items():
            res = mx.evaluate(w["truth"], pt[j], qs[j], w["context"], SEASON)
            rows.append({"unique_id": w["unique_id"], "origin": w["origin"],
                         "method": method, **res})
    df = pd.DataFrame(rows)
    df.to_csv(RES / "realdata_metrics.csv", index=False)
    print(f"  wrote results/realdata_metrics.csv ({len(df):,} rows)", flush=True)

    summ = (df.groupby("method")
              .agg(mean_MASE=("MASE", "mean"), median_MASE=("MASE", "median"),
                   mean_sMAPE=("sMAPE", "mean"), mean_SPL=("SPL", "mean"),
                   cover60=("cover60", "mean"), cover80=("cover80", "mean"))
              .sort_values("mean_MASE"))
    summ.to_csv(RES / "realdata_summary.csv")
    print(summ.round(4).to_string())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="ABC")
    ap.add_argument("--n-jobs", type=int, default=10)
    args = ap.parse_args()

    sample = load_m4_sample()
    windows = build_windows(sample)
    print(f"{sample.unique_id.nunique():,} series -> {len(windows):,} rolling windows "
          f"(h={HORIZON}, {N_ORIGINS} origins)", flush=True)

    if "A" in args.phase:
        phase_a(windows, args.n_jobs)
    if "B" in args.phase:
        phase_b(windows)
    if "C" in args.phase:
        phase_c(windows)


if __name__ == "__main__":
    main()
