"""Representativeness of the simulation design: a feature-based instance space.

Following Kang, Hyndman and Smith-Miles (2017), every series is summarised by four features and
the simulated series are placed in the same space as real series. The real reference set is the
1,000-series M4 Monthly sample of the empirical tier, each cut to the last 96 observations of its M4 training period so that
all series have the same length as the simulated contexts at n = 96.

Features
  entropy    normalised spectral entropy of the series (forecastability; 1 = white noise)
  trend      STL trend strength,      max(0, 1 - var(R) / var(T + R))
  season     STL seasonal strength,   max(0, 1 - var(R) / var(S + R)), period 12
  acf1_diff  first-order autocorrelation of the first differences

Coverage statistic: for each M4 series, the Euclidean distance (standardised features) to its
nearest simulated series, compared with the 95th percentile of the distance from an M4 series to
its nearest OTHER M4 series. An M4 series is "covered" when a simulated series lies at least as
close to it as real series typically lie to one another.

Outputs: results/robust/instance_space.csv, results/robust/instance_coverage.csv,
figures/fig11_instance_space.pdf
"""

from __future__ import annotations

import importlib.util
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
N = 96


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dgp = _load("dgp", "01_dgp.py")
rd = _load("robust_dgp", "R1_robust_dgp.py")


def spectral_entropy(x: np.ndarray) -> float:
    x = x - x.mean()
    p = np.abs(np.fft.rfft(x))[1:] ** 2
    if p.sum() <= 0:
        return 1.0
    p = p / p.sum()
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)) / np.log(len(np.fft.rfft(x)) - 1))


def features(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    res = STL(x, period=12, robust=True).fit()
    r, t, s = res.resid, res.trend, res.seasonal
    vr = np.var(r)
    trend = max(0.0, 1.0 - vr / np.var(t + r)) if np.var(t + r) > 0 else 0.0
    season = max(0.0, 1.0 - vr / np.var(s + r)) if np.var(s + r) > 0 else 0.0
    d = np.diff(x)
    dc = d - d.mean()
    acf1 = float(np.sum(dc[1:] * dc[:-1]) / np.sum(dc ** 2)) if np.sum(dc ** 2) > 0 else 0.0
    return {"entropy": spectral_entropy(x), "trend": trend, "season": season, "acf1_diff": acf1}


def main() -> None:
    rows = []
    m4 = pd.read_parquet(ROOT / "data" / "m4_monthly_sample_1000.parquet")
    for uid, g in m4.groupby("unique_id"):
        y = g.sort_values("ds")["y"].to_numpy()[:-18][-N:]   # training part only
        rows.append({"set": "M4", "group": "M4", "id": uid, **features(y)})
    for d in dgp.DGP_IDS:
        for r in range(200):
            y = dgp.simulate(d, N, r)[:N]
            rows.append({"set": "fixed", "group": d, "id": f"{d}-{r}", **features(y)})
        for r in range(100):
            y = rd.simulate(d, N, r, "clean")[0][:N]
            rows.append({"set": "random", "group": d, "id": f"{d}-{r}", **features(y)})
    df = pd.DataFrame(rows)
    out = ROOT / "results" / "robust"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "instance_space.csv", index=False)

    cols = ["entropy", "trend", "season", "acf1_diff"]
    # standardise on the M4 series only, so the scale does not depend on the design assessed
    mu, sd = df.loc[df["set"] == "M4", cols].mean(), df.loc[df["set"] == "M4", cols].std()
    Z = ((df[cols] - mu) / sd).to_numpy()
    is_m4 = (df["set"] == "M4").to_numpy()
    zm4 = Z[is_m4]
    dm = np.linalg.norm(zm4[:, None, :] - zm4[None, :, :], axis=2)
    np.fill_diagonal(dm, np.inf)
    ref = np.quantile(dm.min(axis=1), 0.95)

    cov_rows = []
    for design in ["fixed", "random"]:
        mask = (df["set"] == design).to_numpy()
        zs, grp = Z[mask], df.loc[mask, "group"].to_numpy()
        dist = np.linalg.norm(zm4[:, None, :] - zs[None, :, :], axis=2)
        nn = dist.min(axis=1)
        nearest = grp[dist.argmin(axis=1)]
        comp = pd.Series(nearest).value_counts(normalize=True)
        cov_rows.append({"design": design, "ref_distance_p95": ref,
                         "covered_share": float(np.mean(nn <= ref)),
                         "median_nn_distance": float(np.median(nn)),
                         **{f"nearest_{g}": float(comp.get(g, 0.0)) for g in dgp.DGP_IDS}})
    cov = pd.DataFrame(cov_rows)
    cov.to_csv(out / "instance_coverage.csv", index=False)
    print(cov.round(3).T)
    print(df.groupby(["set"])[cols].median().round(3))

    # PCA on the standardised features, fitted on the pooled set.
    Zc = Z - Z.mean(axis=0)
    _, sv, vt = np.linalg.svd(Zc, full_matrices=False)
    pcs = Zc @ vt[:2].T
    expl = sv[:2] ** 2 / np.sum(sv ** 2)
    print("PCA loadings:\n", pd.DataFrame(vt[:2].T, index=cols, columns=["PC1", "PC2"]).round(2))

    colors = dict(zip(dgp.DGP_IDS, plt.cm.tab10(np.arange(9))))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharex=True, sharey=True)
    for ax, design, label in [(axes[0], "fixed", "(a) Fixed-parameter design"),
                              (axes[1], "random", "(b) Randomised-parameter design")]:
        ax.scatter(pcs[is_m4, 0], pcs[is_m4, 1], s=6, c="0.75", label="M4 Monthly", zorder=1)
        for g in dgp.DGP_IDS:
            m = ((df["set"] == design) & (df["group"] == g)).to_numpy()
            ax.scatter(pcs[m, 0], pcs[m, 1], s=5, color=colors[g], alpha=0.7, label=g, zorder=2)
        share = cov.loc[cov.design == design, "covered_share"].iloc[0]
        ax.set_title(label, fontsize=10)
        ax.set_xlabel(f"PC1 ({100 * expl[0]:.0f}% of variance)")
    axes[0].set_ylabel(f"PC2 ({100 * expl[1]:.0f}% of variance)")
    h, lab = axes[1].get_legend_handles_labels()
    fig.legend(h, lab, loc="center right", markerscale=3, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0, 0.9, 1))
    fig.savefig(ROOT / "figures" / "fig11_instance_space.pdf")
    print("wrote figures/fig11_instance_space.pdf")


if __name__ == "__main__":
    main()
