"""Check the reviewers' most severe claims against the data before acting on them."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
RES = Path(__file__).resolve().parent.parent / "results"

m = pd.read_csv(RES / "table_mase.csv")
m12 = m[m.horizon_slice == "h1_12"]
ORDER = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination", "TimesFM3"]

print("=" * 74)
print("A. Does RMSSE reverse the D8 (intermittent) recommendation?")
print("=" * 74)
for metric in ["mean_MASE", "mean_RMSSE", "mean_sMAPE", "mean_SPL"]:
    p = m12[m12.dgp == "D8"].pivot_table(index="n", columns="method", values=metric)[ORDER]
    print(f"\n-- D8, {metric} --")
    print(p.round(3).to_string())
    print("   winner per row:", list(p.idxmin(axis=1)))

print("\n" + "=" * 74)
print("B. D4: is 'AutoARIMA is 27-31% better' right? And who is best at n=24?")
print("=" * 74)
p = m12[m12.dgp == "D4"].pivot_table(index="n", columns="method", values="mean_MASE")[ORDER]
print(p.round(3).to_string())
for n in p.index:
    tf = p.loc[n, "TimesFM3"]
    best = p.loc[n].drop("TimesFM3").idxmin()
    bv = p.loc[n].drop("TimesFM3").min()
    aa = p.loc[n, "AutoARIMA"]
    print(f"  n={n:<4} best classical = {best:<14} {bv:.3f} | TimesFM3 {tf:.3f} | "
          f"TimesFM worse by {100*(tf/bv-1):.1f}%  -> best is better by {100*(1-bv/tf):.1f}%")
    print(f"         vs AutoARIMA specifically: {aa:.3f}, TimesFM {'worse' if tf>aa else 'BETTER'} "
          f"by {abs(100*(tf/aa-1)):.1f}%")

print("\n" + "=" * 74)
print("C. M4: how does the pre-registered pinball loss (SPL) rank the methods?")
print("=" * 74)
rs = pd.read_csv(RES / "realdata_summary.csv", index_col=0)
print(rs.round(4).to_string())
print("\n  ranking by mean_SPL (lower better):", list(rs["mean_SPL"].sort_values().index))
print("  ranking by mean_MASE           :", list(rs["mean_MASE"].sort_values().index))

print("\n" + "=" * 74)
print("D. Coverage deviation: |mean(cov)-0.80| vs mean(|cov-0.80|) per cell")
print("=" * 74)
cov = pd.read_csv(RES / "table_coverage.csv")
c = cov[cov.horizon_slice == "h1_12"]
byn = c.pivot_table(index="n", columns="method", values="cover80")[ORDER]
as_written = (byn - 0.80).abs().mean()
per_cell = c.assign(dev=(c.cover80 - 0.80).abs()).groupby("method")["dev"].mean().reindex(ORDER)
out = pd.DataFrame({"as_reported(avg first)": as_written, "honest(per-cell)": per_cell})
print(out.round(4).to_string())
print("\n  ranking as reported:", list(as_written.sort_values().index))
print("  ranking per-cell   :", list(per_cell.sort_values().index))
tf = c[c.method == "TimesFM3"]["cover80"]
print(f"  TimesFM3 per-cell cover80 range: {tf.min():.3f} to {tf.max():.3f}")

print("\n" + "=" * 74)
print("E. Assorted numeric checks")
print("=" * 74)
allm = pd.read_csv(RES / "all_metrics.csv")
n_na, n_tot = int(allm.MAPE.isna().sum()), len(allm)
print(f"  MAPE undefined: {n_na:,}/{n_tot:,} = {100*n_na/n_tot:.4f}%")
d6 = c[c.dgp == "D6"]
cls = [x for x in ORDER if x != "TimesFM3"]
w = d6.pivot_table(index="n", columns="method", values="width80")
print(f"  D6 classical width range: {w[cls].values.min():.2f} to {w[cls].values.max():.2f}")
d5 = m12[(m12.dgp == "D5") & (m12.n == 24)].set_index("method")["mean_MASE"]
print(f"  D5 n=24: AutoETS {d5['AutoETS']:.3f} / SeasonalNaive {d5['SeasonalNaive']:.3f} "
      f"= factor {d5['AutoETS']/d5['SeasonalNaive']:.2f}")
rt = pd.read_csv(RES / "realdata_tests.csv")
print(f"  M4 TimesFM3 cover80: {rs.loc['TimesFM3','cover80']:.4f}")
d8 = m12[m12.dgp == "D8"].pivot_table(index="n", columns="method", values="mean_MASE")[ORDER]
for n in d8.index:
    tf = d8.loc[n, "TimesFM3"]; bv = d8.loc[n].drop("TimesFM3").min()
    print(f"  D8 n={n:<4} TimesFM reduction vs best classical: {100*(1-tf/bv):.1f}%")
