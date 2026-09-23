"""Second referee round (R3-m7): a longer horizon, H = 48 (post hoc).

Calibration of foundation models is reported to degrade with the horizon (Adler et al. 2026), and the
main design stops at H = 12. The nine processes are regenerated with the same seeds at length n + 48
(so contexts can differ from the main design where a process depends on its total length, e.g. D7's
inflection at 0.6(n + H)); all methods forecast 48 steps:

  the six pre-registered methods (as 03_run_forecasts.py, same settings),
  TimesFM-2.5 (N1 settings) and Chronos-2 (N8 defaults).

Scored by horizon block (1-12, 13-24, 25-48, 1-48): mean MASE (denominator from the context),
80% coverage and the scaled 80% interval score.

Outputs: results/h48/forecasts/*.npz, results/h48/per_series.csv.gz, results/h48/summary.csv
Usage:   python code/N9_horizon48.py [--phase ABC] [--n-jobs 10]
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
OUT = ROOT / "results" / "h48"
FC = OUT / "forecasts"
FC.mkdir(parents=True, exist_ok=True)
H, REPS = 48, 200
BLOCKS = {"h1_12": slice(0, 12), "h13_24": slice(12, 24), "h25_48": slice(24, 48), "h1_48": slice(0, 48)}


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run = _load("run", "03_run_forecasts.py")
run.FC_DIR = FC                      # redirect every phase's cache to results/h48/forecasts
dgp, mx = run.dgp, run.mx


def phase_a(n_jobs):
    for d in dgp.DGP_IDS:
        for n in dgp.LENGTHS:
            if (FC / f"classical_{d}_n{n}_r{REPS}.npz").exists():
                continue
            secs = run.phase_a(d, n, REPS, H, n_jobs)
            print(f"A {d} n={n}: {secs:.1f}s", flush=True)


def phase_b():
    import timesfm3
    tf3 = timesfm3.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    fm = _load("fm", "N1_foundation_models.py")
    fm.H = H
    n8 = _load("n8", "N8_more_foundation_models.py")
    t25, c2 = fm.TFM25(max_context=512), n8.Chronos2()
    for d in dgp.DGP_IDS:
        for n in dgp.LENGTHS:
            if not (FC / f"timesfm_{d}_n{n}_r{REPS}.npz").exists():
                run.phase_b(d, n, REPS, H, tf3)
            f = FC / f"fm_{d}_n{n}_r{REPS}.npz"
            if f.exists():
                continue
            ctx, _ = run.cell_series(d, n, REPS, H)
            q25 = np.concatenate([t25.run(ctx[i:i + 100]) for i in range(0, REPS, 100)])
            qc2 = np.concatenate([c2.run(ctx[i:i + 100], H) for i in range(0, REPS, 100)])
            np.savez_compressed(f, TimesFM25_pt=q25[:, :, 4], TimesFM25_q=q25,
                                Chronos2_pt=qc2[:, :, 4], Chronos2_q=qc2)
            print(f"B {d} n={n}", flush=True)


def phase_c():
    rows = []
    for d in dgp.DGP_IDS:
        m = dgp.SEASONAL_PERIOD[d]
        for n in dgp.LENGTHS:
            ctx, truth = run.cell_series(d, n, REPS, H)
            preds = {}
            for z in (np.load(FC / f"classical_{d}_n{n}_r{REPS}.npz"),
                      np.load(FC / f"timesfm_{d}_n{n}_r{REPS}.npz"),
                      np.load(FC / f"fm_{d}_n{n}_r{REPS}.npz")):
                for k in z.files:
                    if k.endswith("_pt"):
                        preds[k[:-3]] = (z[k], z[k[:-3] + "_q"])
            den = np.array([mx.mase_denominator(c, m) for c in ctx])
            ok = den > 0
            for meth, (pt, q) in preds.items():
                ae = np.abs(truth - pt) / np.where(ok, den, np.nan)[:, None]
                lo, hi = q[:, :, 0], q[:, :, 8]
                inside = (truth >= lo) & (truth <= hi)
                isc = ((hi - lo) + 10 * ((lo - truth) * (truth < lo) + (truth - hi) * (truth > hi))) \
                    / np.where(ok, den, np.nan)[:, None]
                for b, sl in BLOCKS.items():
                    rows.append(pd.DataFrame({"dgp": d, "n": n, "rep": np.arange(REPS), "method": meth,
                                              "block": b, "MASE": np.nanmean(ae[:, sl], axis=1),
                                              "cover80": inside[:, sl].mean(axis=1),
                                              "IS80": np.nanmean(isc[:, sl], axis=1)}))
    df = pd.concat(rows, ignore_index=True)
    df.to_csv(OUT / "per_series.csv.gz", index=False)
    cm = df.groupby(["block", "dgp", "n", "method"])[["MASE", "cover80", "IS80"]].mean().reset_index()
    cm.to_csv(OUT / "cell_means.csv", index=False)
    out = []
    for b, g in cm.groupby("block"):
        w = g.pivot_table(index=["dgp", "n"], columns="method", values="MASE")
        r = w.div(w.min(axis=1), axis=0)
        cov = g.groupby("method").cover80.mean()
        dev = g.assign(dev=(g.cover80 - 0.8).abs()).groupby("method").dev.mean()
        wins = w.idxmin(axis=1).value_counts()
        for meth in w.columns:
            out.append({"block": b, "method": meth, "worst_ratio": r[meth].max(),
                        "worst_cell": str(r[meth].idxmax()), "median_ratio": r[meth].median(),
                        "cells_won": int(wins.get(meth, 0)), "cover80": cov[meth],
                        "abs_cov_dev": dev[meth]})
    s = pd.DataFrame(out)
    s.to_csv(OUT / "summary.csv", index=False)
    print(s.pivot(index="method", columns="block", values=["worst_ratio", "cover80"]).round(3).to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="ABC")
    ap.add_argument("--n-jobs", type=int, default=10)
    a = ap.parse_args()
    t0 = time.time()
    if "A" in a.phase:
        phase_a(a.n_jobs)
    if "B" in a.phase:
        phase_b()
    if "C" in a.phase:
        phase_c()
    print(f"done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
