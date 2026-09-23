"""Revision (JoF referees): more foundation models, a configuration check, and an output audit.

Adds, on the 7,200 series of the main design (same seeds, same contexts, h = 12):

  TimesFM3eval   TimesFM-3 with the settings of the developers' own benchmark evaluator
                 (timesfm3/evaluator.py: use_symmetric_averaging=True, make_positive=True).
                 The main study used the package defaults of predict_batch (both False).
  TimesFM25      TimesFM-2.5 (google/timesfm-2.5-200m-pytorch, Apache-2.0), with the
                 configuration recommended in its model card.
  ChronosBolt    Chronos-Bolt base (amazon/chronos-bolt-base, Apache-2.0).

All three are zero-shot and receive only the raw context, like TimesFM-3. Each emits the nine
deciles; its point forecast is the median decile, as for TimesFM-3.

Output audit of TimesFM-3 (referee 3, comment M2), written to results/fm/timesfm3_audit.csv:
  * quantile array shape returned by predict_batch;
  * max |forecast - q0.5| (is the point forecast the median?);
  * share of (series, step) pairs with crossing quantiles when sort_quantiles=False.

Outputs: results/fm/<model>_<DGP>_n<n>_r200.npz with <model>_pt, <model>_q, secs.
Usage:  python code/N1_foundation_models.py [--models TimesFM3eval,TimesFM25,ChronosBolt]
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
OUT = ROOT / "results" / "fm"
OUT.mkdir(parents=True, exist_ok=True)
REPS, H = 200, 12
LEVELS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dgp = _load("dgp", "01_dgp.py")


def contexts_for(d, n):
    s = np.array([dgp.simulate(d, n, r, H) for r in range(REPS)])
    return s[:, :n]


class TFM3Eval:
    name = "TimesFM3eval"

    def __init__(self):
        import timesfm3
        self.m = timesfm3.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")

    def run(self, ctx):
        outs = list(self.m.predict_batch(contexts=[c.astype(np.float32) for c in ctx], horizon=H,
                                         return_quantiles=True, use_symmetric_averaging=True,
                                         make_positive=True))
        q = np.array([np.asarray(o.quantiles, dtype=float)[:H, :9] for o in outs])
        return np.sort(q, axis=2)


class TFM25:
    name = "TimesFM25"

    def __init__(self, max_context: int = 512):
        # max_context 512 covers every simulated context (n <= 200) and fits a 6 GB GPU; the M4
        # tier passes 1024. Longer contexts are truncated to their most recent values.
        import timesfm
        self.m = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
        self.m.compile(timesfm.ForecastConfig(
            max_context=max_context, max_horizon=128, per_core_batch_size=32, normalize_inputs=True,
            use_continuous_quantile_head=True, force_flip_invariance=True,
            infer_is_positive=True, fix_quantile_crossing=True))

    def run(self, ctx):
        _, q = self.m.forecast(horizon=H, inputs=[c.astype(np.float32) for c in ctx])
        q = np.asarray(q, dtype=float)[:, :H, 1:10]       # column 0 is the mean
        return np.sort(q, axis=2)


class Chronos:
    name = "ChronosBolt"

    def __init__(self):
        import torch
        from chronos import BaseChronosPipeline
        self.torch = torch
        self.p = BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-base",
                                                     device_map="cuda", torch_dtype=torch.float32)

    def run(self, ctx):
        q, _ = self.p.predict_quantiles([self.torch.tensor(c, dtype=self.torch.float32) for c in ctx],
                                        prediction_length=H, quantile_levels=LEVELS)
        return np.sort(q.cpu().numpy().astype(float), axis=2)


def audit_timesfm3() -> None:
    import timesfm3
    m = timesfm3.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    rows = []
    for d in dgp.DGP_IDS:
        for n in dgp.LENGTHS:
            ctx = contexts_for(d, n)[:50]
            outs = list(m.predict_batch(contexts=[c.astype(np.float32) for c in ctx], horizon=H,
                                        return_quantiles=True, sort_quantiles=False))
            raw = [np.asarray(o.quantiles, dtype=float) for o in outs]
            q = np.array([r[:H, :9] for r in raw])
            f = np.array([np.asarray(o.forecast, dtype=float).ravel()[:H] for o in outs])
            cross = np.mean(np.any(np.diff(q, axis=2) < -1e-9, axis=2))
            rows.append({"dgp": d, "n": n, "quantile_shape": str(raw[0].shape),
                         "max_abs_forecast_minus_q50": float(np.max(np.abs(f - q[:, :, 4]))),
                         "crossing_share": float(cross)})
    pd.DataFrame(rows).to_csv(OUT / "timesfm3_audit.csv", index=False)
    print(pd.DataFrame(rows).describe(include="all").T[["top", "max", "mean"]].to_string())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="TimesFM3eval,TimesFM25,ChronosBolt")
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()
    if args.audit:
        audit_timesfm3()
        return
    ctor = {"TimesFM3eval": TFM3Eval, "TimesFM25": TFM25, "ChronosBolt": Chronos}
    for name in args.models.split(","):
        model = ctor[name]()
        for d in dgp.DGP_IDS:
            for n in dgp.LENGTHS:
                f = OUT / f"{name}_{d}_n{n}_r{REPS}.npz"
                if f.exists():
                    continue
                ctx = contexts_for(d, n)
                t0 = time.time()
                q = model.run(ctx)
                secs = time.time() - t0
                assert q.shape == (REPS, H, 9), q.shape
                np.savez_compressed(f, **{f"{name}_pt": q[:, :, 4], f"{name}_q": q},
                                    secs=np.array([secs]))
                print(f"{name} {d} n={n}: {secs:.1f}s", flush=True)
        del model


if __name__ == "__main__":
    main()
