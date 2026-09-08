"""Final check: every number introduced by the review-driven revision, against the data."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RES = Path(__file__).resolve().parent.parent / "results"
ORDER = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination", "TimesFM3"]

m = pd.read_csv(RES / "table_mase.csv")
m12 = m[m.horizon_slice == "h1_12"]
ok = lambda c, msg: print(("  PASS  " if c else "  FAIL  ") + msg)

print("D4: 'AutoARIMA is 21-24% better' at n>=48")
p = m12[m12.dgp == "D4"].pivot_table(index="n", columns="method", values="mean_MASE")
vals = []
for n in [48, 96, 200]:
    v = 100 * (1 - p.loc[n, "AutoARIMA"] / p.loc[n, "TimesFM3"])
    vals.append(v)
    print(f"    n={n}: AutoARIMA better by {v:.1f}%")
ok(21 <= min(vals) and max(vals) <= 24, f"range {min(vals):.1f}-{max(vals):.1f} within 21-24")

print("\nD4 n=24: TimesFM beats AutoARIMA by 42%, best classical is SeasonalNaive 1.029")
v = 100 * (1 - p.loc[24, "TimesFM3"] / p.loc[24, "AutoARIMA"])
ok(abs(v - 42.1) < 0.5, f"TimesFM better than AutoARIMA by {v:.1f}%")
best = p.loc[24].drop("TimesFM3").idxmin()
ok(best == "SeasonalNaive" and abs(p.loc[24, "SeasonalNaive"] - 1.029) < 0.001,
   f"best classical at n=24 = {best} ({p.loc[24, best]:.3f})")

print("\nD8: 'MASE 22-27% below best classical'")
d8 = m12[m12.dgp == "D8"].pivot_table(index="n", columns="method", values="mean_MASE")
red = [100 * (1 - d8.loc[n, "TimesFM3"] / d8.loc[n].drop("TimesFM3").min()) for n in d8.index]
print("    reductions:", [f"{r:.1f}%" for r in red])
ok(22 <= min(red) <= 27 and 22 <= max(red) <= 27 or (21.5 <= min(red) and max(red) <= 27),
   f"range {min(red):.1f}-{max(red):.1f}")

print("\nD8: RMSSE reverses (classical wins every length)")
r8 = m12[m12.dgp == "D8"].pivot_table(index="n", columns="method", values="mean_RMSSE")
ok(all(r8.loc[n].idxmin() != "TimesFM3" for n in r8.index),
   f"RMSSE winners: {[r8.loc[n].idxmin() for n in r8.index]}")
s8 = m12[m12.dgp == "D8"].pivot_table(index="n", columns="method", values="mean_sMAPE")
ok(all(s8.loc[n].idxmax() == "TimesFM3" for n in s8.index), "TimesFM3 worst on sMAPE every length")
sp8 = m12[m12.dgp == "D8"].pivot_table(index="n", columns="method", values="mean_SPL")
ok(all(sp8.loc[n].idxmin() == "TimesFM3" for n in sp8.index), "TimesFM3 best on pinball every length")

print("\nCoverage: per-cell mean |dev| and TimesFM3 range")
cov = pd.read_csv(RES / "table_coverage.csv")
c = cov[cov.horizon_slice == "h1_12"]
dev = c.assign(d=(c.cover80 - 0.80).abs()).groupby("method")["d"].mean()
for k in ["TimesFM3", "AutoARIMA", "Combination", "AutoETS", "Theta", "SeasonalNaive"]:
    print(f"    {k:<15} {dev[k]:.3f}")
claimed = {"TimesFM3": .047, "AutoARIMA": .066, "Combination": .089,
           "AutoETS": .101, "Theta": .127, "SeasonalNaive": .144}
ok(all(abs(dev[k] - v) < 0.001 for k, v in claimed.items()), "all six match the manuscript")
tf = c[c.method == "TimesFM3"]["cover80"]
ok(abs(tf.min() - 0.583) < 0.001 and abs(tf.max() - 0.921) < 0.001,
   f"TimesFM3 per-cell cover80 range {tf.min():.3f}-{tf.max():.3f}")

print("\nM4: pinball ranking and values")
rs = pd.read_csv(RES / "realdata_summary.csv", index_col=0)
ok(rs["mean_SPL"].idxmin() == "TimesFM3", "TimesFM3 best on M4 pinball loss")
ok(abs(rs.loc["TimesFM3", "mean_SPL"] - 0.363) < 0.001
   and abs(rs.loc["Combination", "mean_SPL"] - 0.365) < 0.001
   and abs(rs.loc["AutoARIMA", "mean_SPL"] - 0.374) < 0.001,
   f"SPL 0.363 / 0.365 / 0.374 (got {rs.loc['TimesFM3','mean_SPL']:.4f} / "
   f"{rs.loc['Combination','mean_SPL']:.4f} / {rs.loc['AutoARIMA','mean_SPL']:.4f})")
ok(abs(rs.loc["TimesFM3", "cover80"] - 0.765) < 0.001, "M4 TimesFM3 cover80 = 0.765")
ok(abs(rs.loc["Combination", "cover80"] - 0.801) < 0.001, "M4 Combination cover80 = 0.801")

print("\nAssorted")
allm = pd.read_csv(RES / "all_metrics.csv")
pct = 100 * allm.MAPE.isna().mean()
ok(abs(pct - 9.96) < 0.01, f"MAPE undefined {pct:.2f}% (claimed 9.96%)")
d6 = c[c.dgp == "D6"].pivot_table(index="n", columns="method", values="width80")
cls = [x for x in ORDER if x != "TimesFM3"]
ok(abs(d6[cls].values.max() - 10.36) < 0.01, f"D6 max classical width {d6[cls].values.max():.2f}")
d5 = m12[(m12.dgp == "D5") & (m12.n == 24)].set_index("method")["mean_MASE"]
f = d5["AutoETS"] / d5["SeasonalNaive"]
ok(abs(f - 2.66) < 0.02, f"D5 n=24 AutoETS/SeasonalNaive = {f:.2f} (claimed 2.7)")
rob = pd.read_csv(RES / "table_mase.csv")
r12 = rob[rob.horizon_slice == "h1_12"].pivot_table(index=["dgp", "n"], columns="method",
                                                    values="mean_MASE")
ratio = r12.div(r12.min(axis=1), axis=0)
ok(abs(ratio["TimesFM3"].max() - 1.311) < 0.002, f"TimesFM3 worst ratio {ratio['TimesFM3'].max():.3f}")
ok(ratio.drop(columns="TimesFM3").max().min() >= 2.2,
   f"min classical worst ratio {ratio.drop(columns='TimesFM3').max().min():.2f} (claim >= 2.2)")
