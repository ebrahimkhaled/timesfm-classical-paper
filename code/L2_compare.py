"""Referee round 2, R cross-check, step 3: compare R `forecast` with StatsForecast on D4/D5.

Reads results/round2/r_check_series.csv and r_forecast_check_forecasts.csv (L2_export_series.py,
L2_r_forecast_check.R), results/all_metrics.csv (StatsForecast/TimesFM-3 per-series MASE,
h = 1..12) and results/round2/model_selection.csv (StatsForecast forms at n = 24, 48).

Writes:
  results/round2/r_forecast_check_per_series.csv   per-series MASE of the R and Python methods
  results/round2/r_forecast_check_summary.csv      per (dgp, n): mean MASE, seasonal-form shares,
                                                   R failures, paired Wilcoxon p (R vs StatsForecast)
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
dgp = importlib.import_module("01_dgp")
met = importlib.import_module("02_metrics")
R2 = ROOT / "results" / "round2"
H, M = 12, 12
KEY = ["dgp", "n", "rep"]
PY = ["AutoARIMA", "AutoETS", "Theta", "SeasonalNaive", "TimesFM3"]
PAIRS = [("R_auto.arima", "AutoARIMA"), ("R_ets", "AutoETS"), ("R_thetaf", "Theta")]

# --- R forecasts -> MASE, using the series as R saw them (exported CSV) -------------------
ser = pd.read_csv(R2 / "r_check_series.csv", float_precision="round_trip")  # exact doubles
fc = pd.read_csv(R2 / "r_forecast_check_forecasts.csv")
fcols = [f"f{h}" for h in range(1, H + 1)]
series = {k: g.sort_values("t") for k, g in ser.groupby(KEY)}
mase = []
for r in fc.itertuples(index=False):
    g = series[(r.dgp, r.n, r.rep)]
    ctx = g.loc[g.part == "context", "y"].to_numpy()
    tru = g.loc[g.part == "truth", "y"].to_numpy()
    den = met.mase_denominator(ctx, M)
    pt = np.array([getattr(r, c) for c in fcols], float)
    mase.append(met.mase(tru, pt, den) if r.status == "ok" else np.nan)
fc["MASE"] = mase
rw = fc.pivot_table(index=KEY, columns="method", values="MASE", dropna=False)

# --- StatsForecast / TimesFM-3 per-series MASE -----------------------------------------------
am = pd.read_csv(ROOT / "results" / "all_metrics.csv",
                 usecols=["dgp", "n", "rep", "method", "horizon_slice", "MASE"])
am = am[(am.horizon_slice == "h1_12") & am.method.isin(PY) & am.dgp.isin(["D4", "D5"])]
pw = am.pivot_table(index=KEY, columns="method", values="MASE", dropna=False)
per = rw.join(pw, how="left")
per.reset_index().to_csv(R2 / "r_forecast_check_per_series.csv", index=False)

# --- StatsForecast chosen forms (n = 24, 48) --------------------------------------------------
ms = pd.read_csv(R2 / "model_selection.csv")
ms_share = ms.groupby(["dgp", "n"])[["ets_seasonal", "arima_seasonal"]].mean()

seas = fc[fc.status == "ok"].pivot_table(index=KEY, columns="method", values="seasonal",
                                         aggfunc="first")
rows = []
for (d, n), g in per.groupby(level=["dgp", "n"]):
    row = {"dgp": d, "n": n, "series": len(g)}
    for c in ["R_auto.arima", "R_ets", "R_thetaf"] + PY:
        row[f"MASE_{c}"] = g[c].mean()
    s = seas.loc[(d, n)]
    row["R_arima_seasonal_share"] = s["R_auto.arima"].astype(str).eq("True").mean()
    row["R_ets_seasonal_share"] = s["R_ets"].astype(str).eq("True").mean()
    if (d, n) in ms_share.index:
        row["SF_arima_seasonal_share"] = ms_share.loc[(d, n), "arima_seasonal"]
        row["SF_ets_seasonal_share"] = ms_share.loc[(d, n), "ets_seasonal"]
    else:
        row["SF_arima_seasonal_share"] = row["SF_ets_seasonal_share"] = np.nan
    sub = fc[(fc.dgp == d) & (fc.n == n)]
    row["R_failures"] = int((sub.status != "ok").sum())
    row["R_failures_by_method"] = ";".join(f"{m}:{k}" for m, k in
                                            sub[sub.status != "ok"].method.value_counts().items())
    for rm, pm in PAIRS:
        x = g[[rm, pm]].dropna()
        row[f"n_pairs_{pm}"] = len(x)
        row[f"median_diff_{rm}_minus_{pm}"] = float(np.median(x[rm] - x[pm]))
        row[f"wilcoxon_p_{rm}_vs_{pm}"] = wilcoxon(x[rm], x[pm]).pvalue
    rows.append(row)
summ = pd.DataFrame(rows)
summ.to_csv(R2 / "r_forecast_check_summary.csv", index=False)
pd.set_option("display.width", 250, "display.max_columns", 50)
print(summ.round(4).T.to_string())
