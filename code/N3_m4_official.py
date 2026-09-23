"""Revision (JoF referees 1 and 3): the M4 official test period, OWA, MCB, and context truncation.

For the same seeded 1,000 M4 Monthly series as the rolling-origin tier (07_realdata.py), each
method forecasts the official 18-month M4 test period from the full training series, so results
can be placed against the published M4 benchmarks:

  sMAPE and MASE exactly as defined by M4 (MASE scaled by the in-sample seasonal-naive error, m=12),
  OWA = (sMAPE / sMAPE_Naive2 + MASE / MASE_Naive2) / 2 on the averages, as in M4,
  Naive2 read from the official submission-Naive2.csv,
  80% coverage and MSIS at 80% (the widest interval every method can form from nine deciles).

Multiple comparisons: Friedman test on per-series MASE ranks and the Nemenyi/MCB critical
difference (Koning et al. 2005; Demsar 2006).

Context truncation (referee 3, M6b): the same series forecast from only the last 24, 48 and 96
training observations, scored with the full-history MASE denominator so only the information
given to the method changes. This links the real-data tier to the estimability result of the
simulation and moves the forecast origin's information set away from the canonical M4 split.

Outputs: results/m4_official/{forecasts_*.npz, per_series.csv, summary.csv, mcb.csv,
truncation.csv, lengths.csv}
Usage:  python code/N3_m4_official.py --phase A   (classical, CPU)
        python code/N3_m4_official.py --phase B   (foundation models, GPU)
        python code/N3_m4_official.py --phase C   (scoring)
"""

from __future__ import annotations

import argparse
import importlib.util
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "m4_raw" / "m4" / "datasets"
OUT = ROOT / "results" / "m4_official"
OUT.mkdir(parents=True, exist_ok=True)
H, M = 18, 12
CONTEXTS = {"full": None, "last96": 96, "last48": 48, "last24": 24}
LEVELS = [20, 40, 60, 80]
_LO_HI = [("lo", 80), ("lo", 60), ("lo", 40), ("lo", 20), None,
          ("hi", 20), ("hi", 40), ("hi", 60), ("hi", 80)]
CLASSICAL = ["SeasonalNaive", "Theta", "DOTM", "AutoETS", "AutoARIMA"]
FMS = ["TimesFM3", "TimesFM3eval", "TimesFM25", "ChronosBolt"]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_series():
    sample = pd.read_parquet(ROOT / "data" / "m4_monthly_sample_1000.parquet")
    ids = sorted(sample.unique_id.unique())
    # The seeded sample stores each series as its M4 training part followed by the official
    # 18-month test period (checked against Monthly-train.csv / Monthly-test.csv: 1000/1000).
    train = {u: g.sort_values("ds")["y"].to_numpy(float)[:-H] for u, g in sample.groupby("unique_id")}
    test = pd.read_csv(RAW / "Monthly-test.csv").set_index("V1").loc[ids]
    naive2 = pd.read_csv(RAW / "submission-Naive2.csv").set_index("id").loc[ids]
    return ids, train, test.to_numpy(float)[:, :H], naive2.to_numpy(float)[:, :H]


def ctx_list(ids, train, key):
    L = CONTEXTS[key]
    return [train[u] if L is None else train[u][-L:] for u in ids]


def _q(fc, model, k, with_levels=True):
    pt = fc[model].to_numpy(float).reshape(k, H)
    q = np.repeat(pt[:, :, None], 9, axis=2)
    if with_levels:
        for i, spec in enumerate(_LO_HI):
            if spec is not None:
                side, lvl = spec
                q[:, :, i] = fc[f"{model}-{side}-{lvl}"].to_numpy(float).reshape(k, H)
    return pt, np.sort(q, axis=2)


def phase_a(n_jobs):
    from statsforecast import StatsForecast
    from statsforecast.models import (AutoARIMA, AutoETS, DynamicOptimizedTheta,
                                      SeasonalNaive, Theta)
    ex = _load("extras", "N2_classical_extras.py")
    ex.H = H
    ids, train, _, _ = load_series()
    for key in CONTEXTS:
        f = OUT / f"forecasts_classical_{key}.npz"
        if f.exists():
            continue
        ctxs = ctx_list(ids, train, key)
        long = pd.concat([pd.DataFrame({"unique_id": i, "ds": np.arange(len(c)), "y": c})
                          for i, c in enumerate(ctxs)])
        sf = StatsForecast(models=[SeasonalNaive(season_length=M), Theta(season_length=M),
                                   DynamicOptimizedTheta(season_length=M, alias="DOTM"),
                                   AutoETS(season_length=M), AutoARIMA(season_length=M)],
                           freq=1, n_jobs=n_jobs)
        fc = sf.forecast(df=long, h=H, level=LEVELS).sort_values(["unique_id", "ds"])
        store = {}
        for m in CLASSICAL:
            store[f"{m}_pt"], store[f"{m}_q"] = _q(fc, m, len(ids))
        store["Combination_pt"] = np.mean([store[f"{m}_pt"] for m in ("Theta", "AutoETS", "AutoARIMA")], 0)
        store["Combination_q"] = np.sort(np.mean([store[f"{m}_q"] for m in ("Theta", "AutoETS", "AutoARIMA")], 0), 2)
        store["CombEAD_pt"] = np.mean([store[f"{m}_pt"] for m in ("AutoETS", "AutoARIMA", "DOTM")], 0)
        store["CombEAD_q"] = np.sort(np.mean([store[f"{m}_q"] for m in ("AutoETS", "AutoARIMA", "DOTM")], 0), 2)
        if key == "full":
            # M4Comb needs equal-length rows for its helper; run it per series length group
            pts = np.zeros((len(ids), H))
            for L in sorted({len(c) for c in ctxs}):
                idx = [i for i, c in enumerate(ctxs) if len(c) == L]
                pts[idx] = ex.m4comb(np.array([ctxs[i] for i in idx]), n_jobs)
            store["M4Comb_pt"] = pts
            store["M4Comb_q"] = np.repeat(pts[:, :, None], 9, axis=2)
        np.savez_compressed(f, **store)
        print(f"A {key}: done", flush=True)


def phase_b():
    fm = _load("fm", "N1_foundation_models.py")
    fm.H = H
    ids, train, _, _ = load_series()
    import timesfm3
    tf3 = timesfm3.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    runners = {
        "TimesFM3": lambda c: np.sort(np.array([np.asarray(o.quantiles, float)[:H, :9] for o in
                                                tf3.predict_batch(contexts=[x.astype(np.float32) for x in c],
                                                                  horizon=H, return_quantiles=True)]), 2),
        "TimesFM3eval": lambda c: np.sort(np.array([np.asarray(o.quantiles, float)[:H, :9] for o in
                                                    tf3.predict_batch(contexts=[x.astype(np.float32) for x in c],
                                                                      horizon=H, return_quantiles=True,
                                                                      use_symmetric_averaging=True,
                                                                      make_positive=True)]), 2),
    }
    t25, chb = fm.TFM25(max_context=1024), fm.Chronos()
    runners["TimesFM25"] = t25.run
    runners["ChronosBolt"] = chb.run
    for key in CONTEXTS:
        f = OUT / f"forecasts_fm_{key}.npz"
        if f.exists():
            continue
        ctxs = ctx_list(ids, train, key)
        store = {}
        for name, run in runners.items():
            q = np.concatenate([run(ctxs[i:i + 250]) for i in range(0, len(ctxs), 250)])
            store[f"{name}_pt"], store[f"{name}_q"] = q[:, :, 4], q
        np.savez_compressed(f, **store)
        print(f"B {key}: done", flush=True)


def smape(a, f):
    d = np.abs(a) + np.abs(f)
    return 200 * np.mean(np.where(d > 0, np.abs(a - f) / np.where(d > 0, d, 1), 0), axis=1)


def phase_c():
    from scipy.stats import friedmanchisquare, studentized_range
    ids, train, test, naive2 = load_series()
    denom = np.array([np.mean(np.abs(train[u][M:] - train[u][:-M])) for u in ids])
    rows, cov = [], []
    for key in CONTEXTS:
        preds = {}
        # fm2: N8 (Chronos-2, TiRex, TimesFM-2.5 raw); published: M4 submissions (L3), full context only
        for kind in ("classical", "fm", "fm2", "published"):
            if not (OUT / f"forecasts_{kind}_{key}.npz").exists():
                continue
            z = np.load(OUT / f"forecasts_{kind}_{key}.npz")
            for k in z.files:
                if k.endswith("_pt"):
                    preds[k[:-3]] = (z[k], z[k[:-3] + "_q"] if k[:-3] + "_q" in z.files else None)
        if key == "full":
            preds["Naive2"] = (naive2, None)
        for m, (pt, q) in preds.items():
            mase = np.mean(np.abs(test - pt), axis=1) / denom
            sm = smape(test, pt)
            r = {"context": key, "method": m, "sMAPE": sm, "MASE": mase}
            if q is not None and not np.allclose(q[:, :, 0], q[:, :, 8]):
                lo, hi = q[:, :, 0], q[:, :, 8]
                inside = (test >= lo) & (test <= hi)
                a = 0.2
                msis = (np.mean(hi - lo + 2 / a * (lo - test) * (test < lo) + 2 / a * (test - hi) * (test > hi),
                                axis=1) / denom)
                r["cover80"], r["MSIS80"] = inside.mean(axis=1), msis
            rows.append(r)
    per = []
    for r in rows:
        df = pd.DataFrame({"unique_id": ids, "context": r["context"], "method": r["method"],
                           "sMAPE": r["sMAPE"], "MASE": r["MASE"],
                           "cover80": r.get("cover80", np.nan), "MSIS80": r.get("MSIS80", np.nan)})
        per.append(df)
    per = pd.concat(per)
    per.to_csv(OUT / "per_series.csv", index=False)

    full = per[per.context == "full"]
    agg = full.groupby("method")[["sMAPE", "MASE", "cover80", "MSIS80"]].mean()
    n2 = agg.loc["Naive2"]
    agg["OWA"] = 0.5 * (agg.sMAPE / n2.sMAPE + agg.MASE / n2.MASE)
    agg.sort_values("OWA").to_csv(OUT / "summary.csv")
    print(agg.sort_values("OWA").round(3).to_string())

    # MCB / Nemenyi on per-series MASE ranks (full context). Second referee round: one configuration
    # per model -- near-duplicates (a second combination, alternative settings of the same network)
    # distort rank-based comparisons (Benavoli et al. 2016); Naive2 is the reference, not a contender.
    DUPLICATES = {"CombEAD", "TimesFM3eval", "TimesFM25raw", "Naive2", "M4Theta", "M4CombPub"}
    wide = full[~full.method.isin(DUPLICATES)].pivot(index="unique_id", columns="method", values="MASE").dropna()
    ranks = wide.rank(axis=1)
    k, n = wide.shape[1], wide.shape[0]
    stat, p = friedmanchisquare(*[wide[c] for c in wide.columns])
    q = studentized_range.ppf(0.95, k, np.inf) / np.sqrt(2)
    cd = q * np.sqrt(k * (k + 1) / (6 * n))
    mcb = pd.DataFrame({"mean_rank": ranks.mean()}).sort_values("mean_rank")
    best = mcb.mean_rank.iloc[0]
    mcb["lower"], mcb["upper"] = mcb.mean_rank - cd / 2, mcb.mean_rank + cd / 2
    mcb["differs_from_best"] = mcb["lower"] > best + cd / 2
    mcb.attrs = {}
    mcb.to_csv(OUT / "mcb.csv")
    print(f"Friedman chi2={stat:.1f}, p={p:.2e}; Nemenyi CD={cd:.3f} (k={k}, N={n})")
    print(mcb.round(3).to_string())
    pd.DataFrame([{"friedman_chi2": stat, "p": p, "cd": cd, "k": k, "N": n}]).to_csv(
        OUT / "mcb_test.csv", index=False)

    trunc = per.groupby(["context", "method"])["MASE"].agg(["mean", "median"]).reset_index()
    trunc.to_csv(OUT / "truncation.csv", index=False)
    print(trunc.pivot(index="method", columns="context", values="mean").round(3).to_string())

    alltrain = pd.read_csv(RAW / "Monthly-train.csv", index_col=0)
    Lpop = alltrain.notna().sum(axis=1)
    Ls = pd.Series([len(train[u]) for u in ids])
    pd.DataFrame([{"set": "M4 Monthly population", "n": len(Lpop), "median": Lpop.median(),
                   "q25": Lpop.quantile(.25), "q75": Lpop.quantile(.75)},
                  {"set": "sample", "n": len(Ls), "median": Ls.median(),
                   "q25": Ls.quantile(.25), "q75": Ls.quantile(.75)}]).to_csv(OUT / "lengths.csv", index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="ABC")
    ap.add_argument("--n-jobs", type=int, default=8)
    a = ap.parse_args()
    if "A" in a.phase:
        phase_a(a.n_jobs)
    if "B" in a.phase:
        phase_b()
    if "C" in a.phase:
        phase_c()


if __name__ == "__main__":
    main()
