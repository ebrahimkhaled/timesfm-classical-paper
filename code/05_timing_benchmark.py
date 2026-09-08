"""P4b: honest per-method operational costs.

The main run fits the four classical models in one batched statsforecast call, which is the
efficient way to use the library but makes per-model timing impossible to attribute. This
script measures each method separately on the same series so the operational table in the
paper reports numbers that were actually observed rather than divided out of a total.

Measured per method: wall-clock seconds for the whole batch, seconds per series, and peak
additional memory. TimesFM-3 is timed twice -- cold (first call, including model load) and
warm -- because the cold cost is what a practitioner meets first and it is easy to hide.

Usage:  python code/05_timing_benchmark.py [--reps 200] [--n 96]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
import tracemalloc
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("dgp", ROOT / "code" / "01_dgp.py")
dgp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dgp)


def time_classical(model_name: str, contexts: np.ndarray, m: int, horizon: int) -> dict:
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA, AutoETS, Theta, SeasonalNaive

    factory = {"SeasonalNaive": SeasonalNaive, "Theta": Theta,
               "AutoETS": AutoETS, "AutoARIMA": AutoARIMA}[model_name]
    reps, n = contexts.shape
    long = pd.DataFrame({
        "unique_id": np.repeat(np.arange(reps), n),
        "ds": np.tile(np.arange(n), reps),
        "y": contexts.ravel(),
    })
    sf = StatsForecast(models=[factory(season_length=m)], freq=1, n_jobs=1)

    tracemalloc.start()
    t0 = time.perf_counter()
    sf.forecast(df=long, h=horizon, level=[20, 40, 60, 80])
    secs = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"method": model_name, "secs_total": secs, "secs_per_series": secs / reps,
            "peak_mb": peak / 1e6, "note": "fit + predict, single process"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--n", type=int, default=96)
    ap.add_argument("--dgp", type=str, default="D4")  # seasonal: the expensive case
    args = ap.parse_args()

    horizon = dgp.HORIZON
    m = dgp.SEASONAL_PERIOD[args.dgp]
    series = np.array([dgp.simulate(args.dgp, args.n, r, horizon) for r in range(args.reps)])
    contexts = series[:, :args.n]

    rows = []
    for name in ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA"]:
        r = time_classical(name, contexts, m, horizon)
        rows.append(r)
        print(f"{name:<16} {r['secs_total']:8.2f}s total  "
              f"{1000 * r['secs_per_series']:7.2f} ms/series  peak {r['peak_mb']:6.1f} MB")

    # TimesFM-3: cold (model load included) and warm.
    import timesfm
    import torch

    t0 = time.perf_counter()
    fc = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    load_secs = time.perf_counter() - t0

    ctx_list = [c.astype(np.float32) for c in contexts]
    t0 = time.perf_counter()
    _ = list(fc.predict_batch(contexts=ctx_list, horizon=horizon, return_quantiles=True))
    cold_secs = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = list(fc.predict_batch(contexts=ctx_list, horizon=horizon, return_quantiles=True))
    warm_secs = time.perf_counter() - t0

    n_params = sum(p.numel() for p in fc.model.parameters()) if hasattr(fc, "model") else None
    rows.append({"method": "TimesFM3", "secs_total": warm_secs,
                 "secs_per_series": warm_secs / args.reps,
                 "peak_mb": float("nan"),
                 "note": f"inference only; model load {load_secs:.1f}s; "
                         f"first batch {cold_secs:.1f}s"})
    print(f"{'TimesFM3':<16} {warm_secs:8.2f}s total  "
          f"{1000 * warm_secs / args.reps:7.2f} ms/series  "
          f"(load {load_secs:.1f}s, first batch {cold_secs:.1f}s)")

    meta = {
        "dgp": args.dgp, "n": args.n, "reps": args.reps, "horizon": horizon,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "timesfm_params": n_params,
        "timesfm_load_secs": load_secs,
        "timesfm_cold_batch_secs": cold_secs,
        "timesfm_warm_batch_secs": warm_secs,
    }
    out = ROOT / "results"
    pd.DataFrame(rows).to_csv(out / "table_timing.csv", index=False)
    (out / "timing_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"\nwrote results/table_timing.csv and results/timing_meta.json")
    print(f"device: {meta['device']}  {meta['gpu'] or ''}")


if __name__ == "__main__":
    main()
