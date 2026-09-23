"""Referee request: a real-data tier whose evaluation values post-date the foundation models' corpora.

Data: FRED-MD monthly database (McCracken and Ng 2016), current vintage downloaded from the
St. Louis Fed (data/fredmd/2026-rev-08-md.csv). Raw LEVEL series are used: the transformation-code
row is skipped and the transformations are NOT applied. Series with any missing value in
1990-01..2026-06 are dropped.

Design: one forecast origin. Context = the last 240 months up to the origin (2005-01..2024-12),
equal for every series; horizon h = 18, so the evaluation window is 2025-01..2026-06.

Documented training cut-offs (see README): TimesFM-3 / TimesFM-2.5 real-world corpus to Nov 2023;
Chronos-Bolt released Nov 2024; TiRex May 2025; Chronos-2 Oct 2025. The evaluation window starts
after the TimesFM and Chronos-Bolt corpora end; TiRex and Chronos-2 were released inside the window,
so only the part of the window after their release is strictly unseen by them.

Methods: SeasonalNaive, Theta, AutoETS, AutoARIMA (statsforecast, m = 12, quantiles from the
20/40/60/80% intervals exactly as in 03_run_forecasts.py) and their Combination (mean of Theta,
AutoETS, AutoARIMA; vincentised quantiles); Naive (random walk) as a reference; TimesFM-3
(predict_batch defaults, as in N3 phase_b), TimesFM-2.5 (N1, max_context 1024), Chronos-Bolt (N1),
Chronos-2 and TiRex (N8). Point forecast of a foundation model = median decile.

Metrics per series: MASE (in-sample seasonal-naive denominator, m = 12, on the 240-month context),
sMAPE (M4), 80% coverage of [q0.1, q0.9], scaled pinball loss over the nine deciles (02_metrics).
Tests: paired Wilcoxon of TimesFM-3 vs each method on per-series MASE with Benjamini-Hochberg;
Friedman + Nemenyi critical difference on per-series MASE ranks (one configuration per model).

Outputs: results/post_cutoff/{forecasts_*.npz, per_series.csv, summary.csv, tests.csv, mcb.csv,
series.csv, timing.csv, README.md}
Usage:   python code/L5_post_cutoff_tier.py [--phase ABC] [--n-jobs 6]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "fredmd" / "2026-rev-08-md.csv"
OUT = ROOT / "results" / "post_cutoff"
OUT.mkdir(parents=True, exist_ok=True)
H, M, CTX = 18, 12, 240
ORIGIN = "2024-12"
LATE = 10  # index of 2025-11 in the evaluation window (Chronos-2 released Oct 2025)
SPAN = ("1990-01", "2026-06")
LEVELS = [20, 40, 60, 80]
QLEV = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
_LO_HI = [("lo", 80), ("lo", 60), ("lo", 40), ("lo", 20), None,
          ("hi", 20), ("hi", 40), ("hi", 60), ("hi", 80)]
CLASSICAL = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA"]
COMBO_PARTS = ["Theta", "AutoETS", "AutoARIMA"]
FMS = ["TimesFM3", "TimesFM25", "ChronosBolt", "Chronos2", "TiRex"]
BATCH = 100  # GPU batch cap (shared GPU)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_panel():
    raw = pd.read_csv(CSV)
    assert str(raw.iloc[0, 0]).startswith("Transform"), "first data row should be transformation codes"
    x = raw.iloc[1:].copy()                         # skip the transformation-code row, keep LEVELS
    x.index = pd.to_datetime(x.pop("sasdate"), format="%m/%d/%Y").dt.to_period("M")
    x = x.apply(pd.to_numeric, errors="coerce")
    w = x.loc[SPAN[0]:SPAN[1]]
    assert str(w.index.max()) == SPAN[1], f"file ends {x.index.max()}"
    keep = [c for c in w.columns if w[c].notna().all()]
    dropped = {c: [str(p) for p in w.index[w[c].isna()]] for c in w.columns if c not in keep}
    ctx = w.loc[:ORIGIN, keep].iloc[-CTX:]
    test = w.loc[ORIGIN:, keep].iloc[1:H + 1]
    assert len(ctx) == CTX and len(test) == H
    assert str(ctx.index[0]) == "2005-01" and str(test.index[0]) == "2025-01" and str(test.index[-1]) == "2026-06"
    meta = {"file": CSV.name, "sha256": hashlib.sha256(CSV.read_bytes()).hexdigest(),
            "last_month_in_file": str(x.index.max()), "n_columns": int(w.shape[1]),
            "n_kept": len(keep), "dropped": dropped,
            "nonpositive": [c for c in keep if (w[c] <= 0).any()]}
    return keep, ctx.to_numpy(float).T, test.to_numpy(float).T, meta


def _q(fc, model, k):
    pt = fc[model].to_numpy(float).reshape(k, H)
    q = np.repeat(pt[:, :, None], 9, axis=2)
    for i, spec in enumerate(_LO_HI):
        if spec is not None:
            q[:, :, i] = fc[f"{model}-{spec[0]}-{spec[1]}"].to_numpy(float).reshape(k, H)
    return pt, np.sort(q, axis=2)


def phase_a(n_jobs):
    f = OUT / "forecasts_classical.npz"
    if f.exists():
        return
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA, AutoETS, SeasonalNaive, Theta
    ids, ctx, _, _ = load_panel()
    k = len(ids)
    long = pd.DataFrame({"unique_id": np.repeat(np.arange(k), CTX), "ds": np.tile(np.arange(CTX), k),
                         "y": ctx.ravel()})
    t0 = time.time()
    sf = StatsForecast(models=[SeasonalNaive(season_length=M), Theta(season_length=M),
                               AutoETS(season_length=M), AutoARIMA(season_length=M)],
                       freq=1, n_jobs=n_jobs)
    fc = sf.forecast(df=long, h=H, level=LEVELS).sort_values(["unique_id", "ds"])
    secs = time.time() - t0
    store = {}
    for m in CLASSICAL:
        store[f"{m}_pt"], store[f"{m}_q"] = _q(fc, m, k)
    store["Combination_pt"] = np.mean([store[f"{m}_pt"] for m in COMBO_PARTS], 0)
    store["Combination_q"] = np.sort(np.mean([store[f"{m}_q"] for m in COMBO_PARTS], 0), 2)
    nv = np.repeat(ctx[:, -1:], H, axis=1)          # random walk, point only (reference)
    store["Naive_pt"] = nv
    np.savez_compressed(f, secs=np.array([secs]), **store)
    print(f"A classical: {secs:.1f}s", flush=True)


def phase_b(names):
    import torch
    ids, ctx, _, _ = load_panel()
    ctxs = [c.astype(np.float32) for c in ctx]
    for name in names:
        f = OUT / f"forecasts_{name}.npz"
        if f.exists():
            continue
        if name == "TimesFM3":
            import timesfm3
            tf3 = timesfm3.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")

            def run(c):
                return np.sort(np.array([np.asarray(o.quantiles, float)[:H, :9] for o in
                                         tf3.predict_batch(contexts=c, horizon=H, return_quantiles=True)]), 2)
            holder = tf3
        elif name in ("TimesFM25", "ChronosBolt"):
            fm = _load("fm", "N1_foundation_models.py")
            fm.H = H
            holder = fm.TFM25(max_context=1024) if name == "TimesFM25" else fm.Chronos()
            run = holder.run
        else:
            n8 = _load("n8", "N8_more_foundation_models.py")
            holder = n8.CTOR[name]()

            def run(c, _m=holder):
                return _m.run(c, H)
        t0 = time.time()
        q = np.concatenate([run(ctxs[i:i + BATCH]) for i in range(0, len(ctxs), BATCH)])
        secs = time.time() - t0
        assert q.shape == (len(ids), H, 9), q.shape
        np.savez_compressed(f, secs=np.array([secs]), **{f"{name}_pt": q[:, :, 4], f"{name}_q": q})
        print(f"B {name}: {secs:.1f}s", flush=True)
        del holder, run
        torch.cuda.empty_cache()


def _smape(a, f):
    d = np.abs(a) + np.abs(f)
    return 200 * np.mean(np.where(d > 0, np.abs(a - f) / np.where(d > 0, d, 1), 0), axis=1)


def _spl(a, q, denom):
    diff = a[:, :, None] - q
    loss = np.where(diff >= 0, QLEV * diff, (QLEV - 1.0) * diff)
    return loss.mean(axis=(1, 2)) / denom


def benjamini_hochberg(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    adj = p[o] * len(p) / np.arange(1, len(p) + 1)
    adj = np.minimum(np.minimum.accumulate(adj[::-1])[::-1], 1.0)
    out = np.empty_like(adj)
    out[o] = adj
    return out


def phase_c():
    from scipy import stats
    from scipy.stats import friedmanchisquare, studentized_range
    ids, ctx, test, meta = load_panel()
    denom = np.mean(np.abs(ctx[:, M:] - ctx[:, :-M]), axis=1)
    assert np.all(denom > 0)
    preds, timing = {}, []
    for f in sorted(OUT.glob("forecasts_*.npz")):
        z = np.load(f)
        for key in z.files:
            if key.endswith("_pt"):
                m = key[:-3]
                preds[m] = (z[key], z[m + "_q"] if m + "_q" in z.files else None)
        timing.append({"file": f.name, "secs": float(z["secs"][0]) if "secs" in z.files else np.nan})
    nonpos = np.array([c in meta["nonpositive"] for c in ids])
    rows = []
    for m, (pt, q) in preds.items():
        r = pd.DataFrame({"series": ids, "method": m, "nonpositive": nonpos,
                          "MASE": np.mean(np.abs(test - pt), axis=1) / denom,
                          "sMAPE": _smape(test, pt),
                          # 2025-11..2026-06 only (steps 11-18): after every model's release date
                          "MASE_late": np.mean(np.abs(test - pt)[:, LATE:], axis=1) / denom})
        if q is not None:
            r["cover80"] = ((test >= q[:, :, 0]) & (test <= q[:, :, 8])).mean(axis=1)
            r["SPL"] = _spl(test, q, denom)
            r["width80"] = np.mean(q[:, :, 8] - q[:, :, 0], axis=1) / denom
        rows.append(r)
    per = pd.concat(rows, ignore_index=True)
    per.to_csv(OUT / "per_series.csv", index=False)
    pd.DataFrame(timing).to_csv(OUT / "timing.csv", index=False)

    sn = per[per.method == "SeasonalNaive"].set_index("series").MASE
    g = per.groupby("method")
    summ = pd.DataFrame({
        "mean_MASE": g.MASE.mean(), "median_MASE": g.MASE.median(),
        "relMASE_vs_SNaive": g.MASE.mean() / sn.mean(),
        "gmean_ratio_vs_SNaive": g.apply(lambda d: float(np.exp(np.mean(np.log(
            d.set_index("series").MASE / sn))))),
        "mean_MASE_late": g.MASE_late.mean(), "median_MASE_late": g.MASE_late.median(),
        "mean_sMAPE_pos": per[~per.nonpositive].groupby("method").sMAPE.mean(),
        "cover80": g.cover80.mean(), "SPL": g.SPL.mean(), "width80": g.width80.mean(),
        "n_series": g.size()}).sort_values("mean_MASE")
    summ.to_csv(OUT / "summary.csv")
    print(summ.round(3).to_string())

    wide = per.pivot(index="series", columns="method", values="MASE")
    tests = []
    for m in wide.columns:
        if m == "TimesFM3":
            continue
        d = wide["TimesFM3"] - wide[m]
        tests.append({"comparison": f"TimesFM3 vs {m}", "median_diff": float(d.median()),
                      "mean_diff": float(d.mean()), "share_TimesFM3_better": float((d < 0).mean()),
                      "p_wilcoxon": float(stats.wilcoxon(d, zero_method="wilcox").pvalue)})
    tests = pd.DataFrame(tests)
    tests["p_adj_BH"] = benjamini_hochberg(tests.p_wilcoxon.to_numpy())
    tests = tests.sort_values("p_wilcoxon")
    tests.to_csv(OUT / "tests.csv", index=False)
    print(tests.round(4).to_string(index=False))

    contenders = wide.drop(columns=["Naive"])      # Naive is a reference, not a contender
    ranks = contenders.rank(axis=1)
    k, n = contenders.shape[1], contenders.shape[0]
    chi2, p = friedmanchisquare(*[contenders[c] for c in contenders.columns])
    cd = studentized_range.ppf(0.95, k, np.inf) / np.sqrt(2) * np.sqrt(k * (k + 1) / (6 * n))
    mcb = pd.DataFrame({"mean_rank": ranks.mean()}).sort_values("mean_rank")
    best = mcb.mean_rank.iloc[0]
    mcb["lower"], mcb["upper"] = mcb.mean_rank - cd / 2, mcb.mean_rank + cd / 2
    mcb["differs_from_best"] = mcb["lower"] > best + cd / 2
    mcb["friedman_chi2"], mcb["friedman_p"], mcb["nemenyi_cd"], mcb["k"], mcb["N"] = chi2, p, cd, k, n
    mcb.to_csv(OUT / "mcb.csv")
    print(f"Friedman chi2={chi2:.1f}, p={p:.2e}; Nemenyi CD={cd:.3f} (k={k}, N={n})")
    print(mcb[["mean_rank", "differs_from_best"]].round(3).to_string())

    pd.DataFrame({"series": ids, "nonpositive": nonpos, "mase_denominator": denom}).to_csv(
        OUT / "series.csv", index=False)
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="ABC")
    ap.add_argument("--n-jobs", type=int, default=6)
    ap.add_argument("--models", default=",".join(FMS))
    a = ap.parse_args()
    assert a.n_jobs <= 6
    if "A" in a.phase:
        phase_a(a.n_jobs)
    if "B" in a.phase:
        phase_b(a.models.split(","))
    if "C" in a.phase:
        phase_c()


if __name__ == "__main__":
    main()
