"""Third referee round: five post-hoc analyses computed from EXISTING result files (no new forecasts).

  1. simultaneous_ci     max-t (sup) bootstrap simultaneous 95% bands for the 36 (process, length)
                         medians of paired log2 MASE ratios, TimesFM-3 / opponent (main design,
                         h = 1..12), compared with the per-scenario percentile intervals of
                         results/round2/forest.csv
  2. familiarity         randomised design (clean): does TimesFM-3's log2 ratio to AutoARIMA differ
                         between processes a classical family specifies (D1-D5) and the others
                         (D6-D8), at matched difficulty (spectral entropy of the context, the R3
                         feature; alternative: log seasonal-naive MASE)? D9 reported separately.
  3. instance_transfer   predict each M4 series' log2 MASE ratio TimesFM-3 / AutoARIMA (official
                         test period, full context) from its k = 10 nearest simulated series
                         (randomised design, n = 96, R3 standardised feature space)
  4. m4_reweighted       post-stratify the 1,000-series M4 sample to the length distribution of
                         all 48,000 M4 Monthly training series; recompute sMAPE, MASE, OWA
  5. mase_scale          instability of the MASE denominator with m = 12 for D4, D5

Features for simulated series are recomputed deterministically with the R3 feature function
(the simulators are seeded); the 900 stored randomised-design rows are used as a check.

Outputs: results/round3/{simultaneous_ci,familiarity,instance_transfer,m4_reweighted,mase_scale}.csv
"""

from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import importlib.util
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "round3"
OUT.mkdir(parents=True, exist_ok=True)
H_M4 = 18
FEATS = ["entropy", "trend", "season", "acf1_diff"]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dgp = _load("dgp", "01_dgp.py")
met = _load("met", "02_metrics.py")
rd = _load("robust_dgp", "R1_robust_dgp.py")
inst = _load("inst", "R3_instance_space.py")


def log2_ratio(w, a, b):
    x = (w[a] / w[b]).replace([np.inf, -np.inf], np.nan)
    x = x[x > 0]
    return np.log2(x)


# ----------------------------------------------------------------------------------------------
# 1. Simultaneous confidence intervals
# ----------------------------------------------------------------------------------------------
def simultaneous_ci(B=2000, seed=20260923):
    rng = np.random.default_rng(seed)
    opp = ["AutoARIMA", "SeasonalNaive", "Theta", "AutoETS", "Combination"]
    d = pd.read_csv(ROOT / "results" / "all_metrics.csv",
                    usecols=["dgp", "n", "rep", "method", "horizon_slice", "MASE"])
    d = d[(d.horizon_slice == "h1_12") & d.method.isin(opp + ["TimesFM3"])]
    w = d.pivot_table(index=["dgp", "n", "rep"], columns="method", values="MASE")
    forest = pd.read_csv(ROOT / "results" / "round2" / "forest.csv").set_index(["dgp", "n", "opponent"])
    rows = []
    for o in opp:
        cells, est, boots = [], [], []
        for (g, n), cell in w.groupby(level=["dgp", "n"]):
            x = log2_ratio(cell, "TimesFM3", o).dropna().to_numpy()
            idx = rng.integers(0, len(x), (B, len(x)))
            cells.append((g, n))
            est.append(np.median(x))
            boots.append(np.median(x[idx], axis=1))
        est, boots = np.array(est), np.array(boots).T          # boots: B x S
        se = boots.std(axis=0, ddof=1)
        tmax = np.max(np.abs(boots - est) / se, axis=1)
        crit = np.quantile(tmax, 0.95)
        for s, (g, n) in enumerate(cells):
            f = forest.loc[(g, n, o)]
            rows.append({"opponent": o, "dgp": g, "n": n, "log2_med": est[s], "boot_se": se[s],
                         "crit_maxt": crit,
                         "sim_lo": est[s] - crit * se[s], "sim_hi": est[s] + crit * se[s],
                         "pw_t_lo": est[s] - 1.96 * se[s], "pw_t_hi": est[s] + 1.96 * se[s],
                         "pct_lo": f.lo, "pct_hi": f.hi, "bh_significant": bool(f.significant)})
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "simultaneous_ci.csv", index=False)
    summ = r.groupby("opponent").apply(lambda g: pd.Series({
        "crit": g.crit_maxt.iloc[0],
        "sim_favTFM": int((g.sim_hi < 0).sum()), "sim_favOpp": int((g.sim_lo > 0).sum()),
        "pct_favTFM": int((g.pct_hi < 0).sum()), "pct_favOpp": int((g.pct_lo > 0).sum()),
        "bh_favTFM": int((g.bh_significant & (g.log2_med < 0)).sum()),
        "bh_favOpp": int((g.bh_significant & (g.log2_med > 0)).sum())})).loc[opp]
    print("\n[1] Simultaneous 95% max-t bands (36 scenarios): counts excluding 0")
    print(summ.to_string())
    lost = r[(r.opponent == "AutoARIMA") & (r.pct_lo > 0) & ~(r.sim_lo > 0)]
    won = r[(r.opponent == "AutoARIMA") & (r.pct_hi < 0) & ~(r.sim_hi < 0)]
    print("  AutoARIMA scenarios losing exclusion under simultaneity:",
          [f"{a}/{b}" for a, b in zip(pd.concat([lost, won]).dgp, pd.concat([lost, won]).n)])
    return summ


# ----------------------------------------------------------------------------------------------
# 2. Familiarity (synthetic-prior) check
# ----------------------------------------------------------------------------------------------
def familiarity(B=2000, seed=20260924):
    import statsmodels.formula.api as smf
    rng = np.random.default_rng(seed)
    d = pd.read_csv(ROOT / "results" / "robust" / "robust_metrics.csv",
                    usecols=["variant", "dgp", "n", "rep", "method", "MASE"])
    d = d[(d.variant == "clean") & d.method.isin(["TimesFM3", "AutoARIMA", "SeasonalNaive"])]
    w = d.pivot_table(index=["dgp", "n", "rep"], columns="method", values="MASE").reset_index()
    w["lr"] = log2_ratio(w, "TimesFM3", "AutoARIMA")
    w["log_snaive"] = np.log(w["SeasonalNaive"].where(w["SeasonalNaive"] > 0))
    ent = []
    for g, n, r in zip(w.dgp, w.n, w.rep):
        y = rd.simulate(g, int(n), int(r), "clean")[0][:int(n)]
        ent.append(inst.spectral_entropy(y))
    w["entropy"] = ent
    w["group"] = np.where(w.dgp.isin(["D1", "D2", "D3", "D4", "D5"]), "classical",
                          np.where(w.dgp == "D9", "D9", "other"))
    w["log2n"] = np.log2(w.n)
    w = w.dropna(subset=["lr", "entropy", "log_snaive"])
    main = w[w.group != "D9"].copy()
    main["other"] = (main.group == "other").astype(int)

    rows = []

    def fit(df, formula, label, diff):
        o = smf.ols(formula, df).fit(cov_type="HC3")
        q = smf.quantreg(formula, df).fit(q=0.5)
        for est, name in ((o, "OLS_HC3"), (q, "median_reg")):
            ci = est.conf_int().loc["other"]
            rows.append({"analysis": label, "difficulty": diff, "estimator": name, "n_obs": len(df),
                         "coef_other_vs_classical": est.params["other"], "lo": ci[0], "hi": ci[1],
                         "p": est.pvalues["other"]})

    for diff in ("entropy", "log_snaive"):
        fit(main, f"lr ~ other + {diff} + log2n", "pooled", diff)
        fit(main, f"lr ~ other + {diff} * C(n)", "pooled_diff_x_n", diff)
        # common support: difficulty range populated by both groups (5th-95th percentiles)
        lo = max(main.loc[main.other == 1, diff].quantile(.05), main.loc[main.other == 0, diff].quantile(.05))
        hi = min(main.loc[main.other == 1, diff].quantile(.95), main.loc[main.other == 0, diff].quantile(.95))
        cs = main[(main[diff] >= lo) & (main[diff] <= hi)]
        fit(cs, f"lr ~ other + {diff} + log2n", "common_support", diff)
        # D9 separately against D1-D5
        d9 = w[w.group != "other"].assign(other=lambda z: (z.group == "D9").astype(int))
        fit(d9, f"lr ~ other + {diff} + log2n", "D9_vs_classical", diff)
        # within difficulty quintiles (pooled over n): difference in medians, bootstrap CI
        main["q"] = pd.qcut(main[diff], 5, labels=False)
        for k, g in main.groupby("q"):
            a = g.loc[g.other == 1, "lr"].to_numpy()
            b = g.loc[g.other == 0, "lr"].to_numpy()
            bs = [np.median(rng.choice(a, len(a))) - np.median(rng.choice(b, len(b))) for _ in range(B)]
            rows.append({"analysis": f"quintile_{k + 1}", "difficulty": diff, "estimator": "median_diff_boot",
                         "n_obs": len(g), "n_other": len(a), "n_classical": len(b),
                         "diff_lo_edge": g[diff].min(), "diff_hi_edge": g[diff].max(),
                         "coef_other_vs_classical": np.median(a) - np.median(b),
                         "lo": np.quantile(bs, .025), "hi": np.quantile(bs, .975),
                         "med_other": np.median(a), "med_classical": np.median(b)})
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "familiarity.csv", index=False)
    print("\n[2] Familiarity: coefficient of D6-D8 (vs D1-D5) on log2 MASE ratio TimesFM3/AutoARIMA")
    print("  (negative = TimesFM-3 relatively better on non-classical processes)")
    print(r[["analysis", "difficulty", "estimator", "n_obs", "coef_other_vs_classical", "lo", "hi"]]
          .round(3).to_string(index=False))
    print("  raw medians by group:", w.groupby("group")["lr"].median().round(3).to_dict())
    print("  median entropy by group:", w.groupby("group")["entropy"].median().round(3).to_dict())
    return r


# ----------------------------------------------------------------------------------------------
# 3. Instance-space transfer check
# ----------------------------------------------------------------------------------------------
def instance_transfer(seed=20260925, n_perm=1000):
    rng = np.random.default_rng(seed)
    N = 96
    space = pd.read_csv(ROOT / "results" / "robust" / "instance_space.csv")
    m4f = space[space.set == "M4"].set_index("id")[FEATS]
    mu, sd = m4f.mean(), m4f.std()            # R3 convention: M4-only standardisation, ddof = 1

    # simulated features: recompute reps 0..199 (R3 stored reps 0..99 of the randomised design)
    def sim_feats(design, reps=200):
        rows = []
        for g in dgp.DGP_IDS:
            for r in range(reps):
                y = (rd.simulate(g, N, r, "clean")[0] if design == "random" else dgp.simulate(g, N, r))[:N]
                rows.append({"dgp": g, "rep": r, **inst.features(y)})
        return pd.DataFrame(rows)

    rnd = sim_feats("random")
    stored = space[space.set == "random"].copy()
    stored[["dgp", "rep"]] = stored.id.str.split("-", expand=True)
    stored["rep"] = stored.rep.astype(int)
    chk = stored.merge(rnd, on=["dgp", "rep"], suffixes=("_s", "_r"))
    maxdiff = max(np.max(np.abs(chk[f + "_s"] - chk[f + "_r"])) for f in FEATS)
    print(f"\n[3] recomputed vs stored randomised features: {len(chk)} matched, max |diff| = {maxdiff:.2e}")
    fix = space[space.set == "fixed"].copy()
    fix[["dgp", "rep"]] = fix.id.str.split("-", expand=True)
    fix["rep"] = fix.rep.astype(int)

    rm = pd.read_csv(ROOT / "results" / "robust" / "robust_metrics.csv",
                     usecols=["variant", "dgp", "n", "rep", "method", "MASE"])
    rm = rm[(rm.variant == "clean") & (rm.n == N) & rm.method.isin(["TimesFM3", "AutoARIMA"])]
    rw = rm.pivot_table(index=["dgp", "rep"], columns="method", values="MASE").reset_index()
    rw["lr"] = log2_ratio(rw, "TimesFM3", "AutoARIMA")
    am = pd.read_csv(ROOT / "results" / "all_metrics.csv",
                     usecols=["dgp", "n", "rep", "method", "horizon_slice", "MASE"])
    am = am[(am.horizon_slice == "h1_12") & (am.n == N) & am.method.isin(["TimesFM3", "AutoARIMA"])]
    fw = am.pivot_table(index=["dgp", "rep"], columns="method", values="MASE").reset_index()
    fw["lr"] = log2_ratio(fw, "TimesFM3", "AutoARIMA")

    p = pd.read_csv(ROOT / "results" / "m4_official" / "per_series.csv")
    p = p[p.context == "full"].pivot(index="unique_id", columns="method", values="MASE")
    m4 = pd.DataFrame({"lr": log2_ratio(p, "TimesFM3", "AutoARIMA")}).join(m4f, how="inner").dropna()
    zm = ((m4[FEATS] - mu) / sd).to_numpy()
    y_m4 = m4.lr.to_numpy()

    rows, per_series = [], None
    for design, feats, lab in (("random", rnd, rw), ("random_first100", stored, rw), ("fixed", fix, fw)):
        s = feats.merge(lab[["dgp", "rep", "lr"]], on=["dgp", "rep"]).dropna(subset=["lr"])
        zs = ((s[FEATS] - mu) / sd).to_numpy()
        ys = s.lr.to_numpy()
        dist = np.linalg.norm(zm[:, None, :] - zs[None, :, :], axis=2)
        order = np.argsort(dist, axis=1)
        for k in (5, 10, 20, 50):
            nb = order[:, :k]
            for agg in ("mean", "median"):
                pred = ys[nb].mean(1) if agg == "mean" else np.median(ys[nb], 1)
                rho = stats.spearmanr(pred, y_m4).statistic
                nz = y_m4 != 0
                sign = np.mean(np.sign(pred[nz]) == np.sign(y_m4[nz]))
                base = np.median(ys)
                base_sign = np.mean(np.sign(base) == np.sign(y_m4[nz]))
                row = {"design": design, "k": k, "agg": agg, "n_m4": len(y_m4), "n_sim": len(ys),
                       "spearman": rho, "sign_agree": sign,
                       "baseline_sim_median": base, "baseline_sign_agree": base_sign,
                       "mae_knn": np.mean(np.abs(pred - y_m4)),
                       "mae_baseline_sim_median": np.mean(np.abs(base - y_m4)),
                       "mae_oracle_m4_median": np.mean(np.abs(np.median(y_m4) - y_m4)),
                       "median_pred": np.median(pred), "median_realised": np.median(y_m4),
                       "share_pred_favTFM": np.mean(pred < 0), "share_realised_favTFM": np.mean(y_m4 < 0)}
                if design == "random" and k == 10 and agg == "mean":
                    # permutation null: shuffle simulated labels across simulated series
                    null = np.array([stats.spearmanr(rng.permutation(ys)[nb].mean(1), y_m4).statistic
                                     for _ in range(n_perm)])
                    row["perm_p_spearman"] = float((1 + np.sum(null >= rho)) / (1 + n_perm))
                    row["perm_null_q975"] = float(np.quantile(null, .975))
                    row["spearman_lo"], row["spearman_hi"] = _boot_spearman(pred, y_m4, rng)
                    per_series = m4.assign(pred=pred)
                rows.append(row)
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "instance_transfer.csv", index=False)
    print(r[r["agg"] == "mean"][["design", "k", "n_sim", "spearman", "sign_agree", "baseline_sign_agree",
                                 "mae_knn", "mae_baseline_sim_median", "mae_oracle_m4_median"]]
          .round(3).to_string(index=False))
    print(r[r.perm_p_spearman.notna()][["spearman", "spearman_lo", "spearman_hi", "perm_p_spearman",
                                        "perm_null_q975", "median_pred", "median_realised"]].round(3).to_string(index=False))
    return r


def _boot_spearman(a, b, rng, B=1000):
    n = len(a)
    bs = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        bs.append(stats.spearmanr(a[i], b[i]).statistic)
    return float(np.quantile(bs, .025)), float(np.quantile(bs, .975))


# ----------------------------------------------------------------------------------------------
# 4. M4 length reweighting
# ----------------------------------------------------------------------------------------------
def m4_reweighted():
    """The sample was drawn uniformly from series with >= 120 training observations (07_realdata.py,
    MIN_LEN = 120), so 32% of the population (training length 42-119) has no sample support.
    Schemes:
      unweighted              the published 1,000-series means
      eligible_q5             post-stratified to population length quintiles among series with
                              length >= 120 (the sampling frame; differences are sampling noise)
      full_q5_supported       population quintiles of all 48,000 series; empty bins (lengths < 120)
                              dropped and the remaining bins renormalised (i.e. it reweights only
                              the supported part of the population)
      proxy_short_last48/96   all 48,000: the unsupported stratum (length < 120, median 69) is
                              represented by the sample's forecasts from its last 48 / 96
                              observations (in-house methods only; Naive2 is available for the
                              full context only, so OWA uses the full-context Naive2 -- a proxy)
    """
    RAW = ROOT / "data" / "m4_raw" / "m4" / "datasets"
    Lpop = pd.read_csv(RAW / "Monthly-train.csv", index_col=0).notna().sum(axis=1).to_numpy()
    s = pd.read_parquet(ROOT / "data" / "m4_monthly_sample_1000.parquet")
    Ls = s.groupby("unique_id").size() - H_M4
    Lmin = int(Ls.min())
    pall = pd.read_csv(ROOT / "results" / "m4_official" / "per_series.csv")
    p = pall[pall.context == "full"]
    DUP = {"CombEAD", "TimesFM3eval", "TimesFM25raw", "Naive2", "M4Theta", "M4CombPub"}
    out, rows_bins = [], []

    def weights(pop, nb, label):
        edges = np.unique(np.quantile(pop, np.linspace(0, 1, nb + 1)))
        edges[0], edges[-1] = -np.inf, np.inf
        bp = pd.Series(pd.cut(pop, edges, labels=False))
        bs = pd.Series(pd.cut(Ls.to_numpy(), edges, labels=False), index=Ls.index)
        ps, ss = bp.value_counts(normalize=True), bs.value_counts(normalize=True)
        for b in range(len(edges) - 1):
            rows_bins.append({"scheme": label, "bin": b + 1, "lo": edges[b], "hi": edges[b + 1],
                              "pop_share": ps.get(b, 0.0), "sample_share": ss.get(b, 0.0),
                              "sample_count": int((bs == b).sum()),
                              "weight": ps.get(b, 0.0) / ss.get(b) if ss.get(b, 0) > 0 else np.nan})
        return bs.map(ps / ss)   # series-level weight; empty sample bins simply drop out

    def summarise(q, wcol, label, ref_n2):
        agg = (q.assign(a=q.sMAPE * q[wcol], b=q.MASE * q[wcol])
               .groupby("method")[["a", "b", wcol]].sum())
        agg["sMAPE"], agg["MASE"] = agg.a / agg[wcol], agg.b / agg[wcol]
        n2 = ref_n2 if ref_n2 is not None else agg.loc["Naive2"]
        agg["OWA"] = 0.5 * (agg.sMAPE / n2.sMAPE + agg.MASE / n2.MASE)
        agg = agg[["sMAPE", "MASE", "OWA"]].sort_values("OWA")
        agg["rank_OWA_all"] = np.arange(1, len(agg) + 1)
        core = agg[~agg.index.isin(DUP)]
        for c in ("OWA", "MASE", "sMAPE"):
            agg[f"rank_{c}_core"] = core[c].rank().reindex(agg.index)
        out.append(agg.reset_index().assign(scheme=label))
        return agg

    base = summarise(p.assign(w=1.0), "w", "unweighted", None)
    elig = Lpop[Lpop >= Lmin]
    summarise(p.assign(w=p.unique_id.map(weights(elig, 5, "eligible_q5"))), "w", "eligible_q5", None)
    full_w = weights(Lpop, 5, "full_q5_supported")
    summarise(p.assign(w=p.unique_id.map(full_w)), "w", "full_q5_supported", None)
    # proxy for the unsupported short stratum
    share_short = float(np.mean(Lpop < Lmin))
    w_long = weights(elig, 5, "proxy_long_part_q5")
    n2_full = None
    for ctx in ("last48", "last96"):
        pc = pall[pall.context == ctx]
        methods = sorted(set(pc.method) & set(p.method))
        long = p[p.method.isin(methods)].assign(w=lambda z: z.unique_id.map(w_long) * (1 - share_short) / 1000)
        short = pc[pc.method.isin(methods)].assign(w=share_short / 1000)
        q = pd.concat([long, short])
        n2 = base.loc["Naive2"]   # full-context Naive2, unweighted: denominator proxy
        summarise(q, "w", f"proxy_short_{ctx}", n2)
    r = pd.concat(out)
    r = r[["scheme", "method", "sMAPE", "MASE", "OWA", "rank_OWA_all", "rank_OWA_core",
           "rank_MASE_core", "rank_sMAPE_core"]]
    r.to_csv(OUT / "m4_reweighted.csv", index=False)
    pd.DataFrame(rows_bins).to_csv(OUT / "m4_reweighted_bins.csv", index=False)
    print(f"\n[4] M4 length reweighting; sample min training length {Lmin}; population share below it "
          f"{share_short:.3f}")
    print(pd.DataFrame(rows_bins).round(3).to_string(index=False))
    wide = r.pivot(index="method", columns="scheme", values="OWA").sort_values("unweighted")
    rk = r.pivot(index="method", columns="scheme", values="rank_OWA_core")
    print(wide.round(3).to_string())
    print(rk.loc[wide.index].to_string())
    return r


# ----------------------------------------------------------------------------------------------
# 5. MASE scale at short lengths with m = 12
# ----------------------------------------------------------------------------------------------
def mase_scale():
    am = pd.read_csv(ROOT / "results" / "all_metrics.csv",
                     usecols=["dgp", "n", "rep", "method", "horizon_slice", "MASE"])
    am = am[(am.horizon_slice == "h1_12") & am.dgp.isin(["D4", "D5"])
            & am.method.isin(["TimesFM3", "AutoETS", "AutoARIMA"])]
    w = am.pivot_table(index=["dgp", "n", "rep"], columns="method", values="MASE")
    rows = []
    for g in ("D4", "D5"):
        for n in (24, 48, 96, 200):
            den = np.array([met.mase_denominator(dgp.simulate(g, n, r)[:n], 12) for r in range(200)])
            cell = w.loc[(g, n)].reindex(range(200))
            row = {"dgp": g, "n": n, "n_seasonal_diffs": n - 12, "denom_mean": np.nanmean(den),
                   "denom_sd": np.nanstd(den, ddof=1),
                   "cv_denom": np.nanstd(den, ddof=1) / np.nanmean(den),
                   "denom_p05_p95_ratio": np.nanquantile(den, .95) / np.nanquantile(den, .05)}
            for m in ("TimesFM3", "AutoETS", "AutoARIMA"):
                x = cell[m].to_numpy()
                ok = np.isfinite(x) & np.isfinite(den) & (x > 0)
                row[f"spearman_denom_MASE_{m}"] = stats.spearmanr(den[ok], x[ok]).statistic
                row[f"pearson_logdenom_logMASE_{m}"] = np.corrcoef(np.log(den[ok]), np.log(x[ok]))[0, 1]
                # share of log-MASE variance attributable to the denominator: MASE = MAE / denom
                row[f"R2_logMASE_on_logdenom_{m}"] = row[f"pearson_logdenom_logMASE_{m}"] ** 2
                row[f"cv_MASE_{m}"] = np.std(x[ok], ddof=1) / np.mean(x[ok])
            rr = np.log2(cell["TimesFM3"] / cell["AutoETS"]).to_numpy()
            ok = np.isfinite(rr) & np.isfinite(den)
            row["spearman_denom_log2ratio_TFM_ETS"] = stats.spearmanr(den[ok], rr[ok]).statistic
            rows.append(row)
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "mase_scale.csv", index=False)
    print("\n[5] MASE denominator (m = 12) instability, main design")
    print(r[["dgp", "n", "cv_denom", "denom_p05_p95_ratio", "spearman_denom_MASE_TimesFM3",
             "spearman_denom_MASE_AutoETS", "R2_logMASE_on_logdenom_TimesFM3", "R2_logMASE_on_logdenom_AutoETS",
             "spearman_denom_log2ratio_TFM_ETS"]].round(3).to_string(index=False))
    return r


if __name__ == "__main__":
    import sys
    todo = sys.argv[1:] or ["1", "2", "3", "4", "5"]
    fns = {"1": simultaneous_ci, "2": familiarity, "3": instance_transfer, "4": m4_reweighted, "5": mase_scale}
    for k in todo:
        fns[k]()
