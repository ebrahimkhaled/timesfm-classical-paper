"""Robustness study, part 1: randomised-parameter generators and departures from assumptions.

The main design fixes one parameter vector per process (01_dgp.py). This module answers the two
questions a fixed design cannot: (i) do the conclusions survive when every series draws its own
parameters from a wide range, and (ii) do they survive departures from the Gaussian, outlier-free,
known-period assumptions?

Each series draws its parameters uniformly from the ranges in PARAM_RANGES, then one of four
variants is applied:

  clean       Gaussian innovations, as in the main design
  heavy_tail  Student-t(3) innovations rescaled to the same variance, built from the SAME normal
              draws as the clean variant (common random numbers); for D8, over-dispersed
              (negative-binomial) demand sizes with the same mean
  outliers    additive outliers in the CONTEXT only: each point, with probability 0.03, is
              shifted by +/- U(4, 6) robust standard deviations; for D8, a demand is multiplied
              by 5. The held-out truth is left clean.
  est_period  the clean series, but the classical methods receive a seasonal period estimated
              from the context (M4 seasonality test) instead of the true one. TimesFM-3 never
              receives a period, so its forecasts are those of the clean variant.

Seeding: seed = 700_000_000 + 1_000_000 * dgp_index + 1_000 * length_index + rep, disjoint from
the main design's seeds. The same seed gives the same parameters and innovations in every variant,
so the variants are paired.
"""

from __future__ import annotations

import numpy as np

DGP_IDS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
LENGTHS = [24, 48, 96, 200]
HORIZON = 12
BURN_IN = 300
VARIANTS = ["clean", "heavy_tail", "outliers", "est_period"]
TRUE_PERIOD = {d: (12 if d in ("D4", "D5") else 1) for d in DGP_IDS}

# Uniform ranges. The main design's fixed value lies inside every range.
PARAM_RANGES = {
    "D1": {"phi": (0.10, 0.95), "sigma": (1.0, 5.0)},
    "D2": {"phi": (0.10, 0.90), "theta": (-0.60, 0.80), "sigma": (1.0, 5.0)},
    "D3": {"phi": (-0.50, 0.80), "theta": (-0.50, 0.60), "drift": (0.0, 0.6), "sigma": (1.0, 5.0)},
    "D4": {"phi": (0.10, 0.80), "Phi": (0.10, 0.80), "amp": (5.0, 20.0), "sigma": (1.0, 5.0)},
    "D5": {"alpha": (0.05, 0.50), "beta": (0.001, 0.03), "gamma": (0.05, 0.30),
           "trend": (0.0, 0.5), "amp": (5.0, 20.0), "sigma": (1.0, 5.0)},
    "D6": {"jump_sd": (3.0, 15.0), "break_pos": (0.50, 0.85), "sigma_level": (0.2, 1.0),
           "sigma": (1.0, 5.0)},
    "D7": {"r": (0.04, 0.15), "infl_pos": (0.40, 0.80), "K": (100.0, 250.0), "sigma": (1.0, 6.0)},
    "D8": {"p": (0.10, 0.60), "lam": (1.0, 8.0)},
    "D9": {"phi": (0.10, 0.90), "a": (0.05, 0.15), "b": (0.75, 0.90)},
}


def make_seed(dgp_id: str, n: int, rep: int) -> int:
    return 700_000_000 + 1_000_000 * DGP_IDS.index(dgp_id) + 1_000 * LENGTHS.index(n) + rep


def draw_params(dgp_id: str, rng: np.random.Generator) -> dict:
    p = {k: float(rng.uniform(lo, hi)) for k, (lo, hi) in PARAM_RANGES[dgp_id].items()}
    if dgp_id == "D6":
        p["jump_sign"] = float(rng.choice([-1.0, 1.0]))
    if dgp_id == "D9" and p["a"] + p["b"] >= 0.98:      # keep the variance stationary
        p["b"] = 0.97 - p["a"]
    return p


class _Streams:
    """Two random streams for common random numbers across variants.

    `norm` drives every Gaussian draw and every non-innovation draw; `chi` supplies the
    chi-square mixing variables that turn a normal draw into a Student-t draw. The Gaussian
    and heavy-tailed variants therefore share the same normal component, draw for draw, and
    differ only by the t mixing -- they are paired (common random numbers).
    """

    def __init__(self, seed: int):
        self.norm = np.random.default_rng([seed, 1, 0])
        self.chi = np.random.default_rng([seed, 3])

    def __getattr__(self, name):
        return getattr(self.norm, name)


def _innov(rng: "_Streams", size: int, heavy: bool) -> np.ndarray:
    """Unit-variance innovations: N(0,1), or t(3) = Z / sqrt(W/3) scaled by sqrt(1/3)."""
    z = rng.norm.normal(0.0, 1.0, size)
    if heavy:
        w = rng.chi.chisquare(3, size)
        return z / np.sqrt(w / 3.0) / np.sqrt(3.0)
    return z


def _gen(dgp_id: str, p: dict, total: int, n_ctx: int, rng: np.random.Generator,
         heavy: bool) -> np.ndarray:
    if dgp_id == "D1":
        e = p["sigma"] * _innov(rng, total + BURN_IN, heavy)
        x = np.zeros(total + BURN_IN)
        for t in range(1, total + BURN_IN):
            x[t] = p["phi"] * x[t - 1] + e[t]
        return 100.0 + x[BURN_IN:]
    if dgp_id == "D2":
        e = p["sigma"] * _innov(rng, total + BURN_IN, heavy)
        x = np.zeros(total + BURN_IN)
        for t in range(1, total + BURN_IN):
            x[t] = p["phi"] * x[t - 1] + e[t] + p["theta"] * e[t - 1]
        return 100.0 + x[BURN_IN:]
    if dgp_id == "D3":
        e = p["sigma"] * _innov(rng, total + BURN_IN, heavy)
        d = np.zeros(total + BURN_IN)
        for t in range(1, total + BURN_IN):
            d[t] = p["drift"] + p["phi"] * (d[t - 1] - p["drift"]) + e[t] + p["theta"] * e[t - 1]
        return 100.0 + np.cumsum(d[BURN_IN:])
    if dgp_id == "D4":
        m, size = 12, total + BURN_IN
        e = p["sigma"] * _innov(rng, size, heavy)
        z = np.zeros(size)
        for t in range(13, size):
            z[t] = p["phi"] * z[t - 1] + p["Phi"] * z[t - 12] - p["phi"] * p["Phi"] * z[t - 13] + e[t]
        z = z[BURN_IN:]
        y = np.zeros(total)
        y[:m] = (100.0 + p["amp"] * np.sin(2 * np.pi * np.arange(m) / m)
                 + p["sigma"] * _innov(rng, m, heavy))
        for t in range(m, total):
            y[t] = y[t - m] + z[t]
        return y
    if dgp_id == "D5":
        m = 12
        e = p["sigma"] * _innov(rng, total, heavy)
        level, trend = 100.0, p["trend"]
        season = list(p["amp"] * np.sin(2 * np.pi * np.arange(m) / m))
        y = np.zeros(total)
        for t in range(total):
            s_old = season.pop(0)
            y[t] = level + trend + s_old + e[t]
            level, trend = level + trend + p["alpha"] * e[t], trend + p["beta"] * e[t]
            season.append(s_old + p["gamma"] * e[t])
        return y
    if dgp_id == "D6":
        level = 100.0 + np.cumsum(p["sigma_level"] * _innov(rng, total, heavy))
        y = level + p["sigma"] * _innov(rng, total, heavy)
        brk = int(p["break_pos"] * n_ctx)
        y[brk:] += p["jump_sign"] * p["jump_sd"] * p["sigma"]
        return y
    if dgp_id == "D7":
        t = np.arange(total, dtype=float)
        t0 = p["infl_pos"] * total
        return (20.0 + p["K"] / (1.0 + np.exp(-p["r"] * (t - t0)))
                + p["sigma"] * _innov(rng, total, heavy))
    if dgp_id == "D8":
        occurs = rng.random(total) < p["p"]
        if heavy:
            # negative binomial with mean lam and variance 3*lam (over-dispersed sizes)
            k = p["lam"] / 2.0
            sizes = 1.0 + rng.negative_binomial(k, k / (k + p["lam"]), total)
        else:
            sizes = 1.0 + rng.poisson(p["lam"], total)
        return np.where(occurs, sizes, 0.0).astype(float)
    if dgp_id == "D9":
        size = total + BURN_IN
        omega = 0.1
        z = _innov(rng, size, heavy)
        s2 = np.zeros(size)
        e = np.zeros(size)
        s2[0] = omega / (1.0 - p["a"] - p["b"])
        e[0] = np.sqrt(s2[0]) * z[0]
        for t in range(1, size):
            s2[t] = omega + p["a"] * e[t - 1] ** 2 + p["b"] * s2[t - 1]
            e[t] = np.sqrt(s2[t]) * z[t]
        x = np.zeros(size)
        for t in range(1, size):
            x[t] = p["phi"] * x[t - 1] + e[t]
        return 100.0 + x[BURN_IN:]
    raise KeyError(dgp_id)


def _add_outliers(y: np.ndarray, n_ctx: int, dgp_id: str, rng: np.random.Generator) -> np.ndarray:
    """Additive outliers in the context only, at rate 0.03."""
    y = y.copy()
    hit = rng.random(n_ctx) < 0.03
    if dgp_id == "D8":
        y[:n_ctx][hit] *= 5.0
        return y
    dif = np.diff(y[:n_ctx])
    scale = 1.4826 * np.median(np.abs(dif - np.median(dif))) / np.sqrt(2.0)
    scale = scale if scale > 0 else np.std(y[:n_ctx])
    sign = rng.choice([-1.0, 1.0], n_ctx)
    y[:n_ctx][hit] += (sign * rng.uniform(4.0, 6.0, n_ctx) * scale)[hit]
    return y


def simulate(dgp_id: str, n: int, rep: int, variant: str, horizon: int = HORIZON):
    """Return (series of length n + horizon, parameter dict) for one replication."""
    rng = np.random.default_rng(make_seed(dgp_id, n, rep))
    params = draw_params(dgp_id, rng)
    heavy = variant == "heavy_tail"
    # Separate streams: parameters, innovations (common random numbers), contamination.
    rng_innov = _Streams(make_seed(dgp_id, n, rep))
    y = _gen(dgp_id, params, n + horizon, n, rng_innov, heavy)
    if variant == "outliers":
        y = _add_outliers(y, n, dgp_id, np.random.default_rng([make_seed(dgp_id, n, rep), 2]))
    y = np.asarray(y, dtype=np.float64)
    if not np.all(np.isfinite(y)):
        raise ValueError(f"non-finite series {dgp_id} n={n} rep={rep} {variant}")
    return y, params


def m4_seasonality_test(x: np.ndarray, m: int = 12) -> bool:
    """The seasonality test of the M4 benchmarks: lag-m autocorrelation against a 90% bound."""
    n = len(x)
    if n < 3 * m:
        return False
    xc = x - x.mean()
    denom = float(np.sum(xc ** 2))
    if denom <= 0:
        return False
    acf = np.array([np.sum(xc[k:] * xc[:n - k]) / denom for k in range(1, m + 1)])
    limit = 1.645 * np.sqrt((1.0 + 2.0 * np.sum(acf[:m - 1] ** 2)) / n)
    return bool(abs(acf[m - 1]) > limit)


def period_for(dgp_id: str, context: np.ndarray, variant: str) -> int:
    """Seasonal period handed to the classical methods."""
    if variant == "est_period":
        return 12 if m4_seasonality_test(context, 12) else 1
    return TRUE_PERIOD[dgp_id]


if __name__ == "__main__":
    for d in DGP_IDS:
        for v in VARIANTS[:3]:
            ys = [simulate(d, 96, r, v)[0] for r in range(50)]
            neg = np.mean([np.mean(y < 0) for y in ys])
            print(f"{d} {v:<10} mean {np.mean([y.mean() for y in ys]):8.2f} "
                  f"neg {100 * neg:5.2f}%")
    a, _ = simulate("D4", 96, 3, "clean")
    b, _ = simulate("D4", 96, 3, "clean")
    assert np.array_equal(a, b)
    c, _ = simulate("D4", 96, 3, "outliers")
    assert np.sum(a[:96] != c[:96]) > 0 and np.array_equal(a[96:], c[96:])
    det = np.mean([m4_seasonality_test(simulate("D4", 96, r, "clean")[0][:96]) for r in range(100)])
    det1 = np.mean([m4_seasonality_test(simulate("D1", 96, r, "clean")[0][:96]) for r in range(100)])
    print(f"seasonality detected: D4 {det:.2f}, D1 {det1:.2f}")
    print("checks PASS")
