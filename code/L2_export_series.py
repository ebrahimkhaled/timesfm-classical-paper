"""Referee round 2, R cross-check, step 1: export the D4/D5 series for R's `forecast` package.

Writes results/round2/r_check_series.csv in long format
    dgp, n, rep, t, y, part    (part = context for t < n, truth for t >= n; t is 0-based)
for D4 and D5, n in {24, 48, 96, 200}, rep 0..199 (1,600 series). Values are written with
repr-precision (17 significant digits) so R reads back the identical doubles.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
dgp = importlib.import_module("01_dgp")
OUT = ROOT / "results" / "round2"
OUT.mkdir(exist_ok=True)
H = 12

rows = []
for d in ["D4", "D5"]:
    for n in [24, 48, 96, 200]:
        for rep in range(200):
            s = dgp.simulate(d, n, rep, horizon=H)
            t = np.arange(n + H)
            rows.append(pd.DataFrame({"dgp": d, "n": n, "rep": rep, "t": t, "y": s,
                                      "part": np.where(t < n, "context", "truth")}))
df = pd.concat(rows, ignore_index=True)
path = OUT / "r_check_series.csv"
df.to_csv(path, index=False, float_format="%.17g")
print(f"wrote {path} ({len(df):,} rows, {df.groupby(['dgp','n','rep']).ngroups} series)")
