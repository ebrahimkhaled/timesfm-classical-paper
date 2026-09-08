"""P4: aggregate the per-series metrics and run the pre-registered tests.

Implements PREREGISTRATION.md section 3.4 exactly:

* Within each (DGP, length, horizon slice) cell, TimesFM-3 is compared with each classical
  method by a PAIRED WILCOXON SIGNED-RANK test on per-replication MASE differences.
  Replications are independent draws from the DGP, so a paired rank test is the right tool;
  Diebold-Mariano is not, because it assumes an autocorrelated loss-differential sequence
  from a single series. DM is reserved for the real-data rolling-origin tier.
* A paired t-test is reported alongside as a sensitivity check.
* Multiplicity is controlled by Benjamini-Hochberg at FDR = 0.05 within each comparison
  family (one family per opponent method).
* Every test is accompanied by the median MASE ratio, so that a difference that is
  statistically detectable but practically irrelevant is visible as such.

Outputs (results/):
    table_mase.csv          mean and median MASE by cell and method
    table_coverage.csv      empirical coverage and scaled width of the 60% and 80% intervals
    table_tests.csv         one row per (cell, opponent): effect size and adjusted p-value
    table_decision.csv      the when-to-use-which summary
    summary.txt             a human-readable digest
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"

spec = importlib.util.spec_from_file_location("dgp", ROOT / "code" / "01_dgp.py")
dgp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dgp)

FOUNDATION = "TimesFM3"
OPPONENTS = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination"]
METHOD_ORDER = OPPONENTS + [FOUNDATION]


def benjamini_hochberg(p: np.ndarray) -> np.ndarray:
    """BH step-up adjusted p-values (same convention as p.adjust(method='BH'))."""
    p = np.asarray(p, dtype=float)
    ok = np.isfinite(p)
    adj = np.full(p.shape, np.nan)
    if not ok.any():
        return adj
    q = p[ok]
    order = np.argsort(q)
    ranked = q[order]
    n = len(ranked)
    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.clip(adjusted, 0, 1)
    adj[ok] = out
    return adj


def hodges_lehmann(d: np.ndarray) -> float:
    """Hodges-Lehmann estimate: the median of all Walsh averages (d_i + d_j)/2, i <= j."""
    d = np.asarray(d, dtype=float)
    d = d[np.isfinite(d)]
    if d.size == 0:
        return np.nan
    if d.size > 400:  # keep the O(k^2) Walsh set affordable
        rng = np.random.default_rng(0)
        d = rng.choice(d, 400, replace=False)
    walsh = (d[:, None] + d[None, :])[np.triu_indices(len(d))] / 2.0
    return float(np.median(walsh))


def load() -> pd.DataFrame:
    df = pd.read_csv(RES / "all_metrics.csv")
    df["dgp_label"] = df["dgp"].map(dgp.DGP_LABELS)
    return df


def table_mase(df: pd.DataFrame) -> pd.DataFrame:
    g = (df.groupby(["horizon_slice", "dgp", "dgp_label", "correct_model", "n", "method"])
           .agg(mean_MASE=("MASE", "mean"), median_MASE=("MASE", "median"),
                mean_RMSSE=("RMSSE", "mean"), mean_sMAPE=("sMAPE", "mean"),
                mean_SPL=("SPL", "mean"), n_series=("MASE", "size"),
                n_missing=("MASE", lambda s: int(s.isna().sum())))
           .reset_index())
    return g


def table_coverage(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby(["horizon_slice", "dgp", "dgp_label", "n", "method"])
              .agg(cover60=("cover60", "mean"), cover80=("cover80", "mean"),
                   width60=("width60", "mean"), width80=("width80", "mean"))
              .reset_index())


def table_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Paired Wilcoxon of TimesFM-3 against each classical method, per cell."""
    rows = []
    keys = ["horizon_slice", "dgp", "dgp_label", "correct_model", "n"]
    for key, cell in df.groupby(keys):
        wide = cell.pivot_table(index="rep", columns="method", values="MASE")
        if FOUNDATION not in wide.columns:
            continue
        for opp in OPPONENTS:
            if opp not in wide.columns:
                continue
            pair = wide[[FOUNDATION, opp]].dropna()
            if len(pair) < 10:
                continue
            # d < 0 means TimesFM-3 has the LOWER (better) MASE.
            d = (pair[FOUNDATION] - pair[opp]).to_numpy()
            if np.allclose(d, 0):
                p_w = 1.0
            else:
                p_w = float(stats.wilcoxon(d, zero_method="wilcox").pvalue)
            p_t = float(stats.ttest_rel(pair[FOUNDATION], pair[opp]).pvalue)
            rows.append({
                **dict(zip(keys, key)), "opponent": opp, "n_pairs": len(pair),
                "median_MASE_timesfm": float(pair[FOUNDATION].median()),
                "median_MASE_opponent": float(pair[opp].median()),
                "median_ratio": float(pair[FOUNDATION].median() / pair[opp].median()),
                "median_diff": float(np.median(d)),
                "hodges_lehmann": hodges_lehmann(d),
                "p_wilcoxon": p_w, "p_ttest": p_t,
                "timesfm_wins": bool(np.median(d) < 0),
            })
    out = pd.DataFrame(rows)
    # BH within each comparison family: one family per opponent.
    out["p_adj"] = np.nan
    for opp, idx in out.groupby("opponent").groups.items():
        out.loc[idx, "p_adj"] = benjamini_hochberg(out.loc[idx, "p_wilcoxon"].to_numpy())
    out["significant"] = out["p_adj"] < 0.05
    return out


def table_decision(mase: pd.DataFrame, tests: pd.DataFrame) -> pd.DataFrame:
    """Per (DGP, length): the best method, and whether TimesFM-3 beats the best classical."""
    m = mase[mase.horizon_slice == "h1_12"]
    rows = []
    for (d, lab, correct, n), cell in m.groupby(["dgp", "dgp_label", "correct_model", "n"]):
        s = cell.set_index("method")["mean_MASE"]
        classical = s.drop(index=FOUNDATION, errors="ignore")
        best_cl = classical.idxmin()
        t = tests[(tests.horizon_slice == "h1_12") & (tests.dgp == d) &
                  (tests.n == n) & (tests.opponent == best_cl)]
        rows.append({
            "dgp": d, "dgp_label": lab, "correct_model": correct, "n": n,
            "best_classical": best_cl,
            "MASE_best_classical": float(classical.min()),
            "MASE_timesfm": float(s.get(FOUNDATION, np.nan)),
            "ratio_timesfm_over_best": float(s.get(FOUNDATION, np.nan) / classical.min()),
            "winner": FOUNDATION if s.get(FOUNDATION, np.inf) < classical.min() else best_cl,
            "p_adj_vs_best": float(t["p_adj"].iloc[0]) if len(t) else np.nan,
            "significant": bool(t["significant"].iloc[0]) if len(t) else False,
        })
    return pd.DataFrame(rows).sort_values(["dgp", "n"])


def main() -> None:
    df = load()
    mase = table_mase(df)
    cov = table_coverage(df)
    tests = table_tests(df)
    dec = table_decision(mase, tests)

    mase.to_csv(RES / "table_mase.csv", index=False)
    cov.to_csv(RES / "table_coverage.csv", index=False)
    tests.to_csv(RES / "table_tests.csv", index=False)
    dec.to_csv(RES / "table_decision.csv", index=False)

    lines = []
    add = lines.append
    add("=" * 78)
    add("TimesFM-3 vs classical -- simulation results")
    add("=" * 78)
    add(f"series x methods x slices : {len(df):,} rows")
    add(f"MAPE undefined            : {df.MAPE.isna().sum():,} of {len(df):,} "
        f"({100 * df.MAPE.isna().mean():.1f}%) -- all on the intermittent DGP")
    add("")

    add("MEAN MASE, h = 1..12  (lower is better; * marks the winner in the row)")
    piv = (mase[mase.horizon_slice == "h1_12"]
           .pivot_table(index=["dgp", "correct_model", "n"], columns="method",
                        values="mean_MASE"))
    piv = piv[[c for c in METHOD_ORDER if c in piv.columns]]
    add(piv.round(3).to_string())
    add("")

    wins = dec.winner.value_counts()
    add(f"CELL WINNERS (36 cells): "
        + ", ".join(f"{k} {v}" for k, v in wins.items()))
    add("")
    add("BY REGIME:")
    for correct, grp in dec.groupby("correct_model"):
        w = grp.winner.value_counts().to_dict()
        add(f"  correctly specified by {correct:<18} -> " +
            ", ".join(f"{k} {v}" for k, v in w.items()))
    add("")

    add("COVERAGE OF THE NOMINAL 80% INTERVAL, h = 1..12")
    cpiv = (cov[cov.horizon_slice == "h1_12"]
            .pivot_table(index=["dgp", "n"], columns="method", values="cover80"))
    cpiv = cpiv[[c for c in METHOD_ORDER if c in cpiv.columns]]
    add(cpiv.round(3).to_string())
    add("")

    sig = tests[(tests.horizon_slice == "h1_12")]
    add(f"TESTS (h=1..12, BH-adjusted at FDR 0.05): {len(sig)} comparisons, "
        f"{int(sig.significant.sum())} significant, "
        f"{int((sig.significant & sig.timesfm_wins).sum())} favour TimesFM-3, "
        f"{int((sig.significant & ~sig.timesfm_wins).sum())} favour the classical method.")

    text = "\n".join(lines)
    (RES / "summary.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
