"""Data-generating processes for the TimesFM-3 vs classical comparison.

Nine DGPs, D1-D9, spanning "a classical model is exactly right" to "no classical model
is right". Every generator returns a float64 array of length n + H: the first n points
are the context handed to every forecasting method, the last H are the held-out truth.

Seeding contract (frozen in PREREGISTRATION.md section 3.1):
    seed = 1_000_000 * dgp_index + 1_000 * length_index + replication
so a series is reproducible from its identifiers alone, independent of core count or
execution order.
"""

from __future__ import annotations

import numpy as np

# Seasonal period per DGP. Only D4 and D5 carry genuine seasonality.
SEASONAL_PERIOD = {
    "D1": 1, "D2": 1, "D3": 1, "D4": 12,
    "D5": 12, "D6": 1, "D7": 1, "D8": 1, "D9": 1,
}

DGP_LABELS = {
    "D1": "AR(1)",
    "D2": "ARMA(1,1)",
    "D3": "ARIMA(1,1,1) with drift",
    "D4": "SARIMA(1,0,0)(1,1,0)[12]",
    "D5": "ETS(A,A,A)",
    "D6": "Local level with structural break",
    "D7": "Logistic growth",
    "D8": "Intermittent demand",
    "D9": "AR(1) with GARCH(1,1) errors",
}

# Which family is correctly specified by construction. Used for the results tables.
CORRECT_MODEL = {
    "D1": "ARIMA", "D2": "ARIMA", "D3": "ARIMA", "D4": "ARIMA",
    "D5": "ETS", "D6": "none", "D7": "none", "D8": "none", "D9": "ARIMA (mean only)",
}

DGP_IDS = list(DGP_LABELS)
LENGTHS = [24, 48, 96, 200]
HORIZON = 12
BURN_IN = 300


def make_seed(dgp_id: str, n: int, rep: int) -> int:
    """Deterministic seed from the series' identifiers."""
    return 1_000_000 * DGP_IDS.index(dgp_id) + 1_000 * LENGTHS.index(n) + rep


# --------------------------------------------------------------------------- D1
def _d1(total: int, rng: np.random.Generator) -> np.ndarray:
    """AR(1): phi = 0.7, sigma = 2, level 100. AutoARIMA is correctly specified."""
    phi, sigma, level = 0.7, 2.0, 100.0
    e = rng.normal(0.0, sigma, total + BURN_IN)
    x = np.zeros(total + BURN_IN)
    for t in range(1, total + BURN_IN):
        x[t] = phi * x[t - 1] + e[t]
    return level + x[BURN_IN:]


# --------------------------------------------------------------------------- D2
def _d2(total: int, rng: np.random.Generator) -> np.ndarray:
    """ARMA(1,1): phi = 0.6, theta = 0.4, sigma = 2, level 100."""
    phi, theta, sigma, level = 0.6, 0.4, 2.0, 100.0
    e = rng.normal(0.0, sigma, total + BURN_IN)
    x = np.zeros(total + BURN_IN)
    for t in range(1, total + BURN_IN):
        x[t] = phi * x[t - 1] + e[t] + theta * e[t - 1]
    return level + x[BURN_IN:]


# --------------------------------------------------------------------------- D3
def _d3(total: int, rng: np.random.Generator) -> np.ndarray:
    """ARIMA(1,1,1) with drift: the differences are ARMA(1,1) about a drift of 0.3."""
    phi, theta, drift, sigma, start = 0.5, 0.3, 0.3, 2.0, 100.0
    e = rng.normal(0.0, sigma, total + BURN_IN)
    d = np.zeros(total + BURN_IN)
    for t in range(1, total + BURN_IN):
        d[t] = drift + phi * (d[t - 1] - drift) + e[t] + theta * e[t - 1]
    return start + np.cumsum(d[BURN_IN:])


# --------------------------------------------------------------------------- D4
def _d4(total: int, rng: np.random.Generator) -> np.ndarray:
    """SARIMA(1,0,0)(1,1,0)[12].

    With z_t = y_t - y_{t-12}, the model (1 - phi B)(1 - Phi B^12) z_t = e_t expands to
        z_t = phi z_{t-1} + Phi z_{t-12} - phi*Phi z_{t-13} + e_t
    and the series is rebuilt by y_t = y_{t-12} + z_t.
    """
    phi, Phi, sigma, m, start = 0.6, 0.5, 2.0, 12, 100.0

    # z is stationary, so it is burnt in; y is seasonally integrated, so it is NOT --
    # burning in an integrated process merely lets its level wander before the series
    # begins, which would make the simulated level meaningless.
    size = total + BURN_IN
    e = rng.normal(0.0, sigma, size)
    z = np.zeros(size)
    for t in range(13, size):
        z[t] = phi * z[t - 1] + Phi * z[t - 12] - phi * Phi * z[t - 13] + e[t]
    z = z[BURN_IN:]

    y = np.zeros(total)
    # Seed the first seasonal cycle with a fixed seasonal shape plus noise.
    y[:m] = start + 10.0 * np.sin(2 * np.pi * np.arange(m) / m) + rng.normal(0, sigma, m)
    for t in range(m, total):
        y[t] = y[t - m] + z[t]
    return y


# --------------------------------------------------------------------------- D5
def _d5(total: int, rng: np.random.Generator) -> np.ndarray:
    """ETS(A,A,A) in innovations state-space form. AutoETS is correctly specified."""
    # beta = 0.01, not 0.1: see DEVIATIONS.md D-01. At beta = 0.1 the random-walk
    # trend drives the level negative in ~25% of observations at n = 200, which
    # makes sMAPE/MAPE undefined and the series unlike any real measured quantity.
    alpha, beta, gamma, sigma, m = 0.3, 0.01, 0.2, 2.0, 12

    # No burn-in: ETS(A,A,A) is non-stationary (the level integrates a random-walk
    # trend), so a burn-in would only let the level drift away before observation.
    # The series starts from its stated initial state, which is what "level 100 with
    # trend 0.2" is meant to mean.
    size = total
    e = rng.normal(0.0, sigma, size)

    level, trend = 100.0, 0.2
    season = list(10.0 * np.sin(2 * np.pi * np.arange(m) / m))
    y = np.zeros(size)
    for t in range(size):
        s_old = season.pop(0)
        y[t] = level + trend + s_old + e[t]
        new_level = level + trend + alpha * e[t]
        new_trend = trend + beta * e[t]
        season.append(s_old + gamma * e[t])
        level, trend = new_level, new_trend
    return y


# --------------------------------------------------------------------------- D6
def _d6(total: int, rng: np.random.Generator, n_context: int) -> np.ndarray:
    """Local level (random walk) with a structural break inside the CONTEXT.

    The break is placed at 0.7 * n_context so that the jump is observable to every
    method. Putting it inside the forecast window would make it unforecastable by
    anyone and would only measure which method is most conservative.
    """
    sigma_level, sigma_obs, start = 0.5, 2.0, 100.0
    jump = 10.0 * sigma_obs
    level = start + np.cumsum(rng.normal(0.0, sigma_level, total))
    y = level + rng.normal(0.0, sigma_obs, total)
    brk = int(0.7 * n_context)
    y[brk:] += jump
    return y


# --------------------------------------------------------------------------- D7
def _d7(total: int, rng: np.random.Generator) -> np.ndarray:
    """Logistic growth with additive noise.

    The inflection sits at 0.6 * total, so the held-out window lies in the saturating
    arm. A drift-fitting linear method should overshoot here; that is the point.
    """
    # baseline = 20 so the lower asymptote is 20, not 0: see DEVIATIONS.md D-02.
    # Without it, additive noise drives the early part of the curve negative.
    baseline, K, r, sigma = 20.0, 180.0, 0.08, 3.0
    t = np.arange(total, dtype=float)
    t0 = 0.6 * total
    return baseline + K / (1.0 + np.exp(-r * (t - t0))) + rng.normal(0.0, sigma, total)


# --------------------------------------------------------------------------- D8
def _d8(total: int, rng: np.random.Generator) -> np.ndarray:
    """Intermittent demand: a demand occurs with probability 0.3, size 1 + Poisson(4)."""
    p, lam = 0.3, 4.0
    occurs = rng.random(total) < p
    sizes = 1.0 + rng.poisson(lam, total)
    return np.where(occurs, sizes, 0.0).astype(float)


# --------------------------------------------------------------------------- D9
def _d9(total: int, rng: np.random.Generator) -> np.ndarray:
    """AR(1) mean with GARCH(1,1) innovations: correct in the mean, wrong in the variance."""
    phi, omega, a, b, level = 0.6, 0.1, 0.1, 0.85, 100.0
    size = total + BURN_IN
    sigma2 = np.zeros(size)
    e = np.zeros(size)
    sigma2[0] = omega / max(1e-8, 1.0 - a - b)
    z = rng.normal(0.0, 1.0, size)
    e[0] = np.sqrt(sigma2[0]) * z[0]
    for t in range(1, size):
        sigma2[t] = omega + a * e[t - 1] ** 2 + b * sigma2[t - 1]
        e[t] = np.sqrt(sigma2[t]) * z[t]

    x = np.zeros(size)
    for t in range(1, size):
        x[t] = phi * x[t - 1] + e[t]
    return level + x[BURN_IN:]


_GENERATORS = {
    "D1": _d1, "D2": _d2, "D3": _d3, "D4": _d4, "D5": _d5,
    "D6": _d6, "D7": _d7, "D8": _d8, "D9": _d9,
}


def simulate(dgp_id: str, n: int, rep: int, horizon: int = HORIZON) -> np.ndarray:
    """Generate one series of length n + horizon for the given DGP and replication."""
    if dgp_id not in _GENERATORS:
        raise KeyError(f"unknown DGP {dgp_id!r}; expected one of {DGP_IDS}")
    rng = np.random.default_rng(make_seed(dgp_id, n, rep))
    total = n + horizon
    gen = _GENERATORS[dgp_id]
    series = gen(total, rng, n) if dgp_id == "D6" else gen(total, rng)
    series = np.asarray(series, dtype=np.float64)
    if series.shape != (total,):
        raise ValueError(f"{dgp_id} produced shape {series.shape}, expected {(total,)}")
    if not np.all(np.isfinite(series)):
        raise ValueError(f"{dgp_id} produced non-finite values (seed {make_seed(dgp_id, n, rep)})")
    return series


if __name__ == "__main__":
    print(f"{'DGP':<4} {'label':<34} {'m':>3} {'correct':<18} "
          f"{'mean':>9} {'sd':>8} {'%zero':>6}")
    print("-" * 92)
    for did in DGP_IDS:
        s = simulate(did, 200, 0)
        pct_zero = 100.0 * np.mean(s == 0)
        print(f"{did:<4} {DGP_LABELS[did]:<34} {SEASONAL_PERIOD[did]:>3} "
              f"{CORRECT_MODEL[did]:<18} {s.mean():>9.2f} {s.std():>8.2f} {pct_zero:>5.1f}%")

    # Determinism check: the same identifiers must reproduce the same series exactly.
    a = simulate("D4", 96, 7)
    b = simulate("D4", 96, 7)
    assert np.array_equal(a, b), "seeding is not reproducible"
    c = simulate("D4", 96, 8)
    assert not np.array_equal(a, c), "different replications produced identical series"
    print("\nreproducibility check: PASS")
