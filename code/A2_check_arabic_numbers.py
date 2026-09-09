"""Check the numbers quoted in SHARH_ARABIC.md against the result files.

The Arabic companion restates every headline figure from the paper. If it drifts from the
data it becomes a second, contradictory account of the same study, so it gets the same
verification the manuscript gets.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
DOC = (ROOT / "SHARH_ARABIC.md").read_text(encoding="utf-8")

ok, bad = 0, []


def check(label: str, needle: str, truth: bool) -> None:
    global ok
    present = needle in DOC
    if present and truth:
        print(f"  PASS  {label}: '{needle}'")
        ok += 1
    elif not present:
        bad.append(f"{label}: '{needle}' NOT FOUND in the document")
    else:
        bad.append(f"{label}: '{needle}' present but WRONG against the data")


m = pd.read_csv(RES / "table_mase.csv")
m12 = m[m.horizon_slice == "h1_12"]
dec = pd.read_csv(RES / "table_decision.csv")
tests = pd.read_csv(RES / "table_tests.csv")
t12 = tests[tests.horizon_slice == "h1_12"]
allm = pd.read_csv(RES / "all_metrics.csv")
rs = pd.read_csv(RES / "realdata_summary.csv", index_col=0)
rt = pd.read_csv(RES / "realdata_tests.csv")
tim = pd.read_csv(RES / "table_timing.csv").set_index("method")
cro = pd.read_csv(RES / "croston_d8_tests.csv")

# --- cell winners
w = dec.winner.value_counts()
check("TimesFM cell wins", "| `TimesFM3` | **16** |", int(w.get("TimesFM3", 0)) == 16)
check("AutoARIMA cell wins", "| `AutoARIMA` | 10 |", int(w.get("AutoARIMA", 0)) == 10)

# --- pairwise
check("pairwise significant", "**132 معنوية**", int(t12.significant.sum()) == 132)
check("favour TimesFM", "**113 لصالح TimesFM-3**",
      int((t12.significant & t12.timesfm_wins).sum()) == 113)

# --- vs best classical
sig = dec[dec.significant]
check("vs-best significant", "**18 من 36 فرق**", len(sig) == 18)
check("vs-best TimesFM", "**7 لصالح TimesFM-3**", int((sig.winner == "TimesFM3").sum()) == 7)

# --- by opponent (AutoARIMA 11-9)
aa = t12[(t12.opponent == "AutoARIMA") & t12.significant]
check("AutoARIMA 11-9", "| `AutoARIMA` | 20 | **11** | **9** |",
      len(aa) == 20 and int(aa.timesfm_wins.sum()) == 11)

# --- D5 n=24 estimability
d5 = m12[(m12.dgp == "D5") & (m12.n == 24)].set_index("method")["mean_MASE"]
check("AutoETS D5 n=24", "| `AutoETS` | **3.025** ", round(float(d5["AutoETS"]), 3) == 3.025)
check("SeasonalNaive D5 n=24", "| `SeasonalNaive` | **1.139** ",
      round(float(d5["SeasonalNaive"]), 3) == 1.139)
check("factor 2.7", "**2.7 مرة**", 2.6 < float(d5["AutoETS"]) / float(d5["SeasonalNaive"]) < 2.75)

# --- robustness ratios
piv = m12.pivot_table(index=["dgp", "n"], columns="method", values="mean_MASE")
ratio = piv.div(piv.min(axis=1), axis=0)
check("TimesFM worst ratio", "| **1.31** |", round(float(ratio["TimesFM3"].max()), 2) == 1.31)
check("TimesFM median ratio", "**1.008**", round(float(ratio["TimesFM3"].median()), 3) == 1.008)
check("AutoARIMA worst ratio", "| 2.22 |", round(float(ratio["AutoARIMA"].max()), 2) == 2.22)

# --- MAPE undefined
pct = 100 * allm.MAPE.isna().mean()
check("MAPE undefined count", "12,906 من 129,600**", int(allm.MAPE.isna().sum()) == 12906)
check("MAPE undefined pct", "**9.96%**", abs(pct - 9.96) < 0.01)

# --- M4
check("M4 Combination MASE", "| `Combination` | **0.9027** |",
      round(float(rs.loc["Combination", "mean_MASE"]), 4) == 0.9027)
check("M4 TimesFM MASE", "| `TimesFM3` | 0.9114 |",
      round(float(rs.loc["TimesFM3", "mean_MASE"]), 4) == 0.9114)
check("M4 TimesFM coverage", "**0.765**", abs(float(rs.loc["TimesFM3", "cover80"]) - 0.7655) < 1e-3)
sn = rt[rt.opponent == "SeasonalNaive"].iloc[0]
check("M4 vs SeasonalNaive", "**80.1%**", abs(float(sn.pct_series_timesfm_better) - 80.1) < 0.05)

# --- timing
check("AutoARIMA ms", "**2382.7 ms**",
      abs(float(tim.loc["AutoARIMA", "secs_per_series"]) * 1000 - 2382.7) < 1)
check("TimesFM ms", "**23.2 ms**",
      abs(float(tim.loc["TimesFM3", "secs_per_series"]) * 1000 - 23.2) < 0.5)

# --- croston
check("Croston 24/24", "24 من 24 مقارنة معنوية**",
      int(cro.significant.sum()) == 24 and int(cro[cro.significant].timesfm_wins.sum()) == 24)

print("\n" + "=" * 64)
print(f"{ok} PASS, {len(bad)} FAIL")
for b in bad:
    print("  ! " + b)
