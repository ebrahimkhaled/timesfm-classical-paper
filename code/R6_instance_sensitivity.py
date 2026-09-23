"""Revision (JoF referee 2, M5): sensitivity of the instance-space coverage statistic.

R3_instance_space.py defines "covered": an M4 series is covered when its nearest simulated series
is no farther than the 95th percentile of M4-to-nearest-other-M4 distances. This script reports
how that answer depends on the choices behind it:

  threshold     80th, 90th, 95th, 99th percentile
  reverse       share of SIMULATED series within the threshold of some M4 series (how much
                simulated mass lies inside real data), not only the forward share
  equal size    the fixed design (1,800 series at n = 96) subsampled to 900, the size of the
                randomised design, 200 times
  bootstrap     95% interval for the forward share, resampling M4 series (500 draws)
  length        n in {48, 96, 200}; M4 series cut to their last n training observations
                (series shorter than n are excluded)
  features      the four features, and six (adding the first autocorrelation of the series and
                lumpiness, the variance of the variances of non-overlapping windows of 12)

Standardisation uses the M4 series only, so the scale does not depend on the design assessed.
The parameter ranges of the randomised design were fixed in R1_robust_dgp.py before this
coverage statistic was first computed.

Output: results/robust/instance_sensitivity.csv
"""

from __future__ import annotations

import importlib.util
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "code" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dgp = _load("dgp", "01_dgp.py")
rd = _load("robust_dgp", "R1_robust_dgp.py")
inst = _load("inst", "R3_instance_space.py")


def feats6(x):
    f = inst.features(x)
    xc = x - x.mean()
    den = np.sum(xc ** 2)
    f["acf1"] = float(np.sum(xc[1:] * xc[:-1]) / den) if den > 0 else 0.0
    # lumpiness is computed on the standardised series, as in Kang et al. (2017), so that it is
    # scale-free: M4 levels are in the thousands, the simulated levels near 100.
    xs = xc / x.std() if x.std() > 0 else xc
    blocks = [np.var(xs[i:i + 12]) for i in range(0, len(xs) - 11, 12)]
    f["lumpiness"] = float(np.var(blocks))
    return f


def build(n):
    m4 = pd.read_parquet(ROOT / "data" / "m4_monthly_sample_1000.parquet")
    rows = []
    for uid, g in m4.groupby("unique_id"):
        y = g.sort_values("ds")["y"].to_numpy()[:-18]
        if len(y) >= n:
            rows.append({"set": "M4", **feats6(y[-n:])})
    for d in dgp.DGP_IDS:
        for r in range(200):
            rows.append({"set": "fixed", **feats6(dgp.simulate(d, n, r)[:n])})
        for r in range(100):
            rows.append({"set": "random", **feats6(rd.simulate(d, n, r, "clean")[0][:n])})
    return pd.DataFrame(rows)


def nn(a, b, same=False):
    d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)
    if same:
        np.fill_diagonal(d, np.inf)
    return d.min(axis=1)


def main():
    rng = np.random.default_rng(20260923)
    out = []
    for n in (48, 96, 200):
        df = build(n)
        for fset, cols in (("4", ["entropy", "trend", "season", "acf1_diff"]),
                           ("6", ["entropy", "trend", "season", "acf1_diff", "acf1", "lumpiness"])):
            X = df[cols].to_numpy(float)
            if fset == "6":
                pass
            is_m4 = (df.set == "M4").to_numpy()
            mu, sd = X[is_m4].mean(0), X[is_m4].std(0)
            Z = (X - mu) / sd
            zm4 = Z[is_m4]
            m4nn = nn(zm4, zm4, same=True)
            for design in ("fixed", "random"):
                zs = Z[(df.set == design).to_numpy()]
                fwd = nn(zm4, zs)
                rev = nn(zs, zm4)
                for pct in (80, 90, 95, 99):
                    thr = np.quantile(m4nn, pct / 100)
                    row = {"n": n, "features": fset, "design": design, "pct": pct,
                           "n_m4": len(zm4), "n_sim": len(zs),
                           "forward": float(np.mean(fwd <= thr)),
                           "reverse": float(np.mean(rev <= thr))}
                    if pct == 95:
                        boots = []
                        for _ in range(500):
                            i = rng.integers(0, len(zm4), len(zm4))
                            boots.append(np.mean(fwd[i] <= thr))
                        row["forward_lo"], row["forward_hi"] = np.quantile(boots, [0.025, 0.975])
                        if design == "fixed":
                            sub = [np.mean(nn(zm4, zs[rng.choice(len(zs), 900, replace=False)]) <= thr)
                                   for _ in range(200)]
                            row["forward_fixed_sub900"] = float(np.mean(sub))
                    out.append(row)
            print(f"n={n} features={fset} done", flush=True)
    res = pd.DataFrame(out)
    res.to_csv(ROOT / "results" / "robust" / "instance_sensitivity.csv", index=False)
    print(res[res.pct == 95].round(3).to_string())
    print(res[(res.n == 96) & (res.features == "4")].round(3).to_string())


if __name__ == "__main__":
    main()
