"""Timing re-run requested by the referees (round 2): classical methods with a warm-up, TimesFM-3 on GPU and CPU.

Same design as 05_timing_benchmark.py (D4, n = 96, 200 series, h = 12, one process), but
  * each classical method is warmed up on 2 series first, so the one-off numba compilation is excluded;
  * TimesFM-3 is timed on the GPU and on the CPU (model load and first batch reported separately).
The published results/table_timing.csv is NOT overwritten. Output: results/round3/timing_warmup.csv and
results/round3/timing_warmup_meta.json.
"""

import importlib.util
import json
import os
import platform
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "round3"

spec = importlib.util.spec_from_file_location("timing", ROOT / "code" / "05_timing_benchmark.py")
timing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timing)
timing.WARMUP = True
dgp = timing.dgp

REPS, N, DGP = 200, 96, "D4"


def time_timesfm(contexts, horizon, device):
    import timesfm
    t0 = time.perf_counter()
    fc = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch", device=device)
    load = time.perf_counter() - t0
    ctx = [c.astype(np.float32) for c in contexts]
    t0 = time.perf_counter()
    _ = list(fc.predict_batch(contexts=ctx, horizon=horizon, return_quantiles=True))
    cold = time.perf_counter() - t0
    t0 = time.perf_counter()
    _ = list(fc.predict_batch(contexts=ctx, horizon=horizon, return_quantiles=True))
    warm = time.perf_counter() - t0
    del fc
    return {"method": f"TimesFM3_{device}", "secs_total": warm, "secs_per_series": warm / len(contexts),
            "peak_mb": float("nan"), "note": f"inference only; model load {load:.1f}s; first batch {cold:.1f}s"}


def main():
    import torch
    horizon = dgp.HORIZON
    m = dgp.SEASONAL_PERIOD[DGP]
    series = np.array([dgp.simulate(DGP, N, r, horizon) for r in range(REPS)])
    contexts = series[:, :N]
    rows = []
    for name in ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA"]:
        r = timing.time_classical(name, contexts, m, horizon)
        r["note"] = "fit + predict, single process, after warm-up"
        rows.append(r)
        print(f"{name:<14} {1000 * r['secs_per_series']:9.2f} ms/series", flush=True)
    devices = (["cuda"] if torch.cuda.is_available() else []) + ["cpu"]
    for d in devices:
        r = time_timesfm(contexts, horizon, d)
        rows.append(r)
        print(f"{r['method']:<14} {1000 * r['secs_per_series']:9.2f} ms/series  ({r['note']})", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "timing_warmup.csv", index=False)
    meta = {"dgp": DGP, "n": N, "reps": REPS, "horizon": horizon, "warmup": True,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "cpu": platform.processor(), "cpu_threads": os.cpu_count(), "torch_threads": torch.get_num_threads()}
    (OUT / "timing_warmup_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("wrote results/round3/timing_warmup.csv")


if __name__ == "__main__":
    main()
