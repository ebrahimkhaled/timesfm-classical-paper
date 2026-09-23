"""Second referee round (R3-M2, R3-M3): newer foundation models and a matched configuration.

Adds, zero-shot, on the 7,200 series of the main design (same seeds, contexts, h = 12) and on the
1,000 M4 Monthly series (official test period, full and truncated contexts, h = 18):

  Chronos2        Chronos-2 (amazon/chronos-2, 119.5M parameters, Apache-2.0), package defaults
  TiRex           TiRex (NX-AI/TiRex, 35.3M parameters, xLSTM), package defaults
  TimesFM25raw    TimesFM-2.5 with flip invariance and positivity switched OFF, matching the
                  package defaults of TimesFM-3's predict_batch used in the main study (the other
                  TimesFM-2.5 run uses the evaluator-style settings and is matched with TimesFM3eval)

Each model emits the nine deciles; the point forecast is the median decile (sorted), as for the
other foundation models of N1.

Outputs: results/fm/<model>_<DGP>_n<n>_r200.npz and results/m4_official/forecasts_fm2_<context>.npz
Usage:   python code/N8_more_foundation_models.py [--models Chronos2,TiRex,TimesFM25raw] [--m4]
"""

from __future__ import annotations

import argparse
import importlib.util
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
LEVELS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Chronos2:
    name = "Chronos2"

    def __init__(self):
        import torch
        from chronos import Chronos2Pipeline
        self.torch = torch
        self.p = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cuda")

    def run(self, ctx, h):
        q, _ = self.p.predict_quantiles([self.torch.tensor(c, dtype=self.torch.float32) for c in ctx],
                                        prediction_length=h, quantile_levels=LEVELS)
        q = np.array([x[0].cpu().numpy().astype(float) for x in q])    # (series, h, 9)
        return np.sort(q, axis=2)


class TiRex:
    name = "TiRex"

    def __init__(self):
        from tirex import load_model
        import torch
        self.torch = torch
        self.m = load_model("NX-AI/TiRex")

    def run(self, ctx, h):
        q, _ = self.m.forecast(context=[self.torch.tensor(c, dtype=self.torch.float32) for c in ctx],
                               prediction_length=h)
        return np.sort(np.asarray(q.cpu().numpy(), dtype=float), axis=2)


class TFM25raw:
    name = "TimesFM25raw"

    def __init__(self, max_context: int = 512):
        import timesfm
        self.m = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
        self.m.compile(timesfm.ForecastConfig(
            max_context=max_context, max_horizon=128, per_core_batch_size=32, normalize_inputs=True,
            use_continuous_quantile_head=True, force_flip_invariance=False,
            infer_is_positive=False, fix_quantile_crossing=False))

    def run(self, ctx, h):
        _, q = self.m.forecast(horizon=h, inputs=[c.astype(np.float32) for c in ctx])
        return np.sort(np.asarray(q, dtype=float)[:, :h, 1:10], axis=2)


CTOR = {"Chronos2": Chronos2, "TiRex": TiRex, "TimesFM25raw": TFM25raw}


def simulation(names):
    fm = _load("fm", "N1_foundation_models.py")
    dgp, out, reps, h = fm.dgp, fm.OUT, fm.REPS, fm.H
    for name in names:
        model = CTOR[name]()
        for d in dgp.DGP_IDS:
            for n in dgp.LENGTHS:
                f = out / f"{name}_{d}_n{n}_r{reps}.npz"
                if f.exists():
                    continue
                ctx = fm.contexts_for(d, n)
                t0 = time.time()
                q = np.concatenate([model.run(ctx[i:i + 100], h) for i in range(0, len(ctx), 100)])
                secs = time.time() - t0
                assert q.shape == (reps, h, 9), q.shape
                np.savez_compressed(f, **{f"{name}_pt": q[:, :, 4], f"{name}_q": q}, secs=np.array([secs]))
                print(f"{name} {d} n={n}: {secs:.1f}s", flush=True)
        del model


def m4(names):
    n3 = _load("n3", "N3_m4_official.py")
    ids, train, _, _ = n3.load_series()
    models = {}
    for name in names:
        models[name] = TFM25raw(max_context=1024) if name == "TimesFM25raw" else CTOR[name]()
    for key in n3.CONTEXTS:
        f = n3.OUT / f"forecasts_fm2_{key}.npz"
        if f.exists():
            continue
        ctxs = n3.ctx_list(ids, train, key)
        store = {}
        for name, model in models.items():
            q = np.concatenate([model.run(ctxs[i:i + 100], n3.H) for i in range(0, len(ctxs), 100)])
            assert q.shape == (len(ids), n3.H, 9), q.shape
            store[f"{name}_pt"], store[f"{name}_q"] = q[:, :, 4], q
        np.savez_compressed(f, **store)
        print(f"M4 {key}: done", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="Chronos2,TiRex,TimesFM25raw")
    ap.add_argument("--m4", action="store_true")
    a = ap.parse_args()
    names = a.models.split(",")
    simulation(names)
    if a.m4:
        m4(names)


if __name__ == "__main__":
    main()
