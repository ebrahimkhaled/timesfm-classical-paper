"""Revision (JoF referee 3, M7 and M8): seasonal covariates for TimesFM-3, and CPU timing.

M8  The classical methods receive the true seasonal period; TimesFM-3 receives nothing. Here
    TimesFM-3 is given the same information in the form it accepts: two past-and-future
    covariates, sin(2 pi t / 12) and cos(2 pi t / 12), which encode the month of the year, on the
    seasonal processes D4 and D5 (all four lengths, 200 replications).
    Output: results/fm/TimesFM3cov_<DGP>_n<n>_r200.npz

M7  TimesFM-3 inference time on the CPU (no GPU), for the same 200 series used in the main timing
    benchmark (D4, n = 96), plus AutoARIMA on a non-seasonal cell (D1, n = 96), single process.
    Output: results/table_timing_cpu.csv
"""

from __future__ import annotations

import importlib.util
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
REPS, H = 200, 12


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dgp = _load("dgp", "01_dgp.py")


def covariates(n):
    t = np.arange(n + H)
    return np.vstack([np.sin(2 * np.pi * t / 12), np.cos(2 * np.pi * t / 12)]).astype(np.float32)


def run_cov():
    import timesfm3
    m = timesfm3.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    for d in ("D4", "D5"):
        for n in dgp.LENGTHS:
            f = ROOT / "results" / "fm" / f"TimesFM3cov_{d}_n{n}_r{REPS}.npz"
            if f.exists():
                continue
            s = np.array([dgp.simulate(d, n, r, H) for r in range(REPS)])
            ctx = [c.astype(np.float32) for c in s[:, :n]]
            cov = [covariates(n) for _ in range(REPS)]
            outs = list(m.predict_batch(contexts=ctx, horizon=H, past_future_covariates=cov,
                                        return_quantiles=True))
            q = np.sort(np.array([np.asarray(o.quantiles, float)[:H, :9] for o in outs]), axis=2)
            np.savez_compressed(f, TimesFM3cov_pt=q[:, :, 4], TimesFM3cov_q=q)
            print(f"cov {d} n={n}", flush=True)


def run_cpu_timing():
    import torch
    import timesfm3
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA
    rows = []
    s = np.array([dgp.simulate("D4", 96, r, H) for r in range(REPS)])[:, :96]
    # Run with CUDA_VISIBLE_DEVICES="" so that torch sees no GPU and the model loads on the CPU.
    assert not torch.cuda.is_available(), "set CUDA_VISIBLE_DEVICES='' for the CPU timing"
    m = timesfm3.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    with torch.no_grad():
        list(m.predict_batch(contexts=[c.astype(np.float32) for c in s[:10]], horizon=H,
                             return_quantiles=True))
        t0 = time.perf_counter()
        list(m.predict_batch(contexts=[c.astype(np.float32) for c in s], horizon=H,
                             return_quantiles=True))
        secs = time.perf_counter() - t0
    rows.append({"method": "TimesFM3", "cell": "D4 n=96", "device": "cpu",
                 "secs_total": secs, "secs_per_series": secs / REPS,
                 "torch_threads": torch.get_num_threads()})
    x = np.array([dgp.simulate("D1", 96, r, H) for r in range(REPS)])[:, :96]
    long = pd.DataFrame({"unique_id": np.repeat(np.arange(REPS), 96), "ds": np.tile(np.arange(96), REPS),
                         "y": x.ravel()})
    sf = StatsForecast(models=[AutoARIMA(season_length=1)], freq=1, n_jobs=1)
    sf.forecast(df=long[long.unique_id < 5], h=H)            # JIT warm-up excluded from timing
    t0 = time.perf_counter()
    sf.forecast(df=long, h=H)
    secs = time.perf_counter() - t0
    rows.append({"method": "AutoARIMA", "cell": "D1 n=96", "device": "cpu (1 process)",
                 "secs_total": secs, "secs_per_series": secs / REPS, "torch_threads": np.nan})
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "results" / "table_timing_cpu.csv", index=False)
    print(df.to_string())


if __name__ == "__main__":
    import sys
    if "--cov" in sys.argv:
        run_cov()
    if "--cpu" in sys.argv:
        run_cpu_timing()
