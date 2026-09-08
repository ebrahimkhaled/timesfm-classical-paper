"""Forecast accuracy metrics, defined exactly as in PREREGISTRATION.md section 3.3.

All scale-free metrics use the same denominator: the in-sample mean absolute (or squared)
error of the seasonal naive method computed on the CONTEXT, with seasonal period m. This is
the Hyndman-Koehler convention and it keeps MASE, RMSSE and the scaled pinball loss on one
common footing.
"""

from __future__ import annotations

import numpy as np

# The nine deciles both families emit. Fixed by TimesFM-3's output head.
QUANTILE_LEVELS = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])


def mase_denominator(context: np.ndarray, m: int) -> float:
    """In-sample mean absolute seasonal-naive error on the context.

    Returns NaN when the context is too short or perfectly seasonally constant; such a
    series is excluded and counted, never imputed (PREREGISTRATION.md section 4).
    """
    if len(context) <= m:
        return np.nan
    d = np.abs(context[m:] - context[:-m])
    denom = float(np.mean(d))
    return denom if denom > 0 else np.nan


def rmsse_denominator(context: np.ndarray, m: int) -> float:
    """In-sample mean squared seasonal-naive error on the context."""
    if len(context) <= m:
        return np.nan
    d = (context[m:] - context[:-m]) ** 2
    denom = float(np.mean(d))
    return denom if denom > 0 else np.nan


def mase(actual: np.ndarray, pred: np.ndarray, denom: float) -> float:
    if not np.isfinite(denom):
        return np.nan
    return float(np.mean(np.abs(actual - pred)) / denom)


def rmsse(actual: np.ndarray, pred: np.ndarray, denom2: float) -> float:
    if not np.isfinite(denom2):
        return np.nan
    return float(np.sqrt(np.mean((actual - pred) ** 2) / denom2))


def smape(actual: np.ndarray, pred: np.ndarray) -> float:
    """Symmetric MAPE in the M4 convention (range 0-200).

    Points where |actual| + |pred| == 0 contribute 0 rather than NaN: both forecast and
    truth are zero there, which is a perfect prediction, not an undefined one.
    """
    denom = np.abs(actual) + np.abs(pred)
    ratio = np.divide(np.abs(actual - pred), denom, out=np.zeros_like(denom, dtype=float),
                      where=denom > 0)
    return float(200.0 * np.mean(ratio))


def mape(actual: np.ndarray, pred: np.ndarray) -> float:
    """MAPE. Returns NaN if any actual is zero -- undefined, and reported as such.

    Kept for the appendix only. It is undefined at zero, asymmetric, and unusable on the
    intermittent DGP (D8), which is precisely the point made in the paper.
    """
    if np.any(actual == 0):
        return np.nan
    return float(100.0 * np.mean(np.abs((actual - pred) / actual)))


def scaled_pinball_loss(actual: np.ndarray, quantiles: np.ndarray, denom: float,
                        levels: np.ndarray = QUANTILE_LEVELS) -> float:
    """Mean pinball loss over the nine deciles, scaled by the MASE denominator.

    `quantiles` has shape (horizon, n_levels). The pinball loss at level q is
        q * (y - f)      if y >= f
        (1 - q) * (f - y) otherwise
    averaged over horizons and levels. Scaling by the seasonal-naive MAE makes the value
    comparable across DGPs of different magnitude, as in the M5 uncertainty competition.
    """
    if not np.isfinite(denom):
        return np.nan
    y = np.asarray(actual, dtype=float)[:, None]
    f = np.asarray(quantiles, dtype=float)
    if f.shape != (len(actual), len(levels)):
        raise ValueError(f"quantiles shape {f.shape}, expected {(len(actual), len(levels))}")
    diff = y - f
    loss = np.where(diff >= 0, levels * diff, (levels - 1.0) * diff)
    return float(np.mean(loss) / denom)


def interval_coverage(actual: np.ndarray, lo: np.ndarray, hi: np.ndarray) -> float:
    """Fraction of held-out points falling inside [lo, hi]."""
    return float(np.mean((actual >= lo) & (actual <= hi)))


def interval_width(lo: np.ndarray, hi: np.ndarray, denom: float) -> float:
    """Mean interval width, scaled by the MASE denominator so it is comparable."""
    if not np.isfinite(denom):
        return np.nan
    return float(np.mean(hi - lo) / denom)


def evaluate(actual: np.ndarray, point: np.ndarray, quantiles: np.ndarray,
             context: np.ndarray, m: int) -> dict:
    """All metrics for one series and one method, over the full held-out horizon.

    `quantiles` has shape (horizon, 9), ordered by QUANTILE_LEVELS.
    The 60% interval is [q0.2, q0.8] and the 80% interval is [q0.1, q0.9]; 90% is not used
    because TimesFM-3 emits only deciles (PREREGISTRATION.md section 3.3).
    """
    denom = mase_denominator(context, m)
    denom2 = rmsse_denominator(context, m)
    q = np.asarray(quantiles, dtype=float)

    return {
        "MASE": mase(actual, point, denom),
        "RMSSE": rmsse(actual, point, denom2),
        "sMAPE": smape(actual, point),
        "MAPE": mape(actual, point),
        "SPL": scaled_pinball_loss(actual, q, denom),
        "cover60": interval_coverage(actual, q[:, 1], q[:, 7]),
        "cover80": interval_coverage(actual, q[:, 0], q[:, 8]),
        "width60": interval_width(q[:, 1], q[:, 7], denom),
        "width80": interval_width(q[:, 0], q[:, 8], denom),
        "denom_ok": bool(np.isfinite(denom)),
    }


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    ctx = 100 + np.cumsum(rng.normal(0, 1, 100))
    truth = 100 + np.cumsum(rng.normal(0, 1, 12))
    pt = truth + rng.normal(0, 0.5, 12)
    qs = pt[:, None] + np.quantile(rng.normal(0, 1, 4000), QUANTILE_LEVELS)[None, :]

    res = evaluate(truth, pt, qs, ctx, m=1)
    for k, v in res.items():
        print(f"  {k:<10} {v}")

    # A perfect forecast must score 0 on every error metric.
    perfect = evaluate(truth, truth, np.repeat(truth[:, None], 9, axis=1), ctx, m=1)
    assert abs(perfect["MASE"]) < 1e-12 and abs(perfect["sMAPE"]) < 1e-12, "perfect forecast not 0"
    assert abs(perfect["SPL"]) < 1e-12, "perfect quantiles gave non-zero pinball loss"
    print("\nsanity check: PASS (a perfect forecast scores zero on MASE, sMAPE and SPL)")
