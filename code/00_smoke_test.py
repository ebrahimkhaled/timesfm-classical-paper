"""P0 smoke test: confirm TimesFM-3 loads and forecasts, and that statsforecast works.

Run:  python code/00_smoke_test.py
"""

import time
import numpy as np


def smoke_timesfm():
    import timesfm

    t0 = time.time()
    fc = timesfm.TimesFM3Forecaster.from_pretrained("google/timesfm-3.0-pytorch")
    print(f"[timesfm] loaded in {time.time() - t0:.1f}s")

    rng = np.random.default_rng(0)
    n, h = 120, 12
    t = np.arange(n)
    context = 10 + 0.05 * t + 2 * np.sin(2 * np.pi * t / 12) + rng.normal(0, 0.3, n)

    t0 = time.time()
    out = fc.predict(context=context.astype(np.float32), horizon=h, return_quantiles=True)
    print(f"[timesfm] predicted in {time.time() - t0:.2f}s")

    print("[timesfm] output fields:", [f for f in dir(out) if not f.startswith("_")])
    mean = np.asarray(out.forecast)
    print("[timesfm] point forecast shape:", mean.shape)
    print("[timesfm] point forecast[:6]:", np.round(mean.ravel()[:6], 3))
    q = getattr(out, "quantiles", None)
    if q is not None:
        q = np.asarray(q)
        print("[timesfm] quantile shape:", q.shape)
        print("[timesfm] quantiles at h=1:", np.round(q.reshape(q.shape[0], -1)[0], 3)
              if q.ndim >= 2 else np.round(q, 3))
    return True


def smoke_statsforecast():
    import pandas as pd
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA, AutoETS, Theta, SeasonalNaive

    rng = np.random.default_rng(1)
    n, h = 120, 12
    t = np.arange(n)
    y = 10 + 0.05 * t + 2 * np.sin(2 * np.pi * t / 12) + rng.normal(0, 0.3, n)
    df = pd.DataFrame({"unique_id": "s1", "ds": np.arange(n), "y": y})

    sf = StatsForecast(
        models=[AutoARIMA(season_length=12), AutoETS(season_length=12),
                Theta(season_length=12), SeasonalNaive(season_length=12)],
        freq=1, n_jobs=1,
    )
    t0 = time.time()
    fcst = sf.forecast(df=df, h=h, level=[80, 90])
    print(f"[statsforecast] fitted+predicted in {time.time() - t0:.2f}s")
    print("[statsforecast] columns:", list(fcst.columns))
    print(fcst.head(3).to_string(index=False))
    return True


if __name__ == "__main__":
    ok_sf = smoke_statsforecast()
    print("-" * 70)
    ok_tf = smoke_timesfm()
    print("-" * 70)
    print(f"RESULT: statsforecast={'OK' if ok_sf else 'FAIL'}  timesfm={'OK' if ok_tf else 'FAIL'}")
