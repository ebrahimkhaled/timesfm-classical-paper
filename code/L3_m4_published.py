"""Referee request: place TimesFM-3 against the published M4 submissions on the same 1,000 series.

Source (the only one used): the official M4 repository github.com/Mcompetitions/M4-methods,
folder "Point Forecasts" (submission-<ID>.rar, all 100,000 series, columns F1..F48) plus
"Point Forecasts/Submission Info.xlsx" and "Evaluation and Ranks.xlsx" for IDs, authors, ranks
and the published scores.

Submissions: the ten best-ranked by overall OWA (IDs 118, 245, 237, 72, 69, 36, 78, 260, 238, 39,
as listed in Submission Info.xlsx) and the Theta and Comb benchmarks.

Steps
 1. Download each rar once into data/m4_submissions/ (skipped when present) and cache its Monthly
    rows (F1..F18) as data/m4_submissions/monthly_<ID>.csv.gz. Extraction uses the Windows tar
    (libarchive), which reads RAR.
 2. Validation on all 48,000 Monthly series: sMAPE, MASE (in-sample seasonal-naive scale, m=12),
    OWA against Naive2 (data/m4_raw/.../submission-Naive2.csv), compared with the published
    Monthly columns of "Evaluation and Ranks.xlsx" (sheet Point Forecasts-Summary).
 3. The 1,000-series sample of N3_m4_official.py (same ids, test, Naive2, training series and
    scaling as its load_series()/phase_c()): forecasts saved to
    results/m4_official/forecasts_published_full.npz as "<Label>_pt" (1000, 18) in ids order;
    scores to results/m4_official/published_check.csv.

Usage: python code/L3_m4_published.py
"""

from __future__ import annotations

import subprocess
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "m4_raw" / "m4" / "datasets"
SUB = ROOT / "data" / "m4_submissions"
OUT = ROOT / "results" / "m4_official"
H, M = 18, 12
BASE = "https://raw.githubusercontent.com/Mcompetitions/M4-methods/master/Point%20Forecasts/"
WIN_TAR = r"C:\Windows\System32\tar.exe"

# (label, file id, id in Submission Info / Evaluation and Ranks)
SUBMISSIONS = [
    ("Smyl", "118", 118), ("FFORMA", "245", 245), ("Pawlikowski", "237", 237),
    ("Jaganathan", "072", 72), ("Fiorucci", "069", 69), ("Petropoulos", "036", 36),
    ("Shaub", "078", 78), ("Legaki", "260", 260), ("Doornik", "238", 238),
    ("Pedregal", "039", 39), ("M4Theta", "Theta", "Theta"), ("M4CombPub", "Com", "Com"),
]


def smape(a, f):  # identical to N3_m4_official.smape
    d = np.abs(a) + np.abs(f)
    return 200 * np.mean(np.where(d > 0, np.abs(a - f) / np.where(d > 0, d, 1), 0), axis=1)


def fetch(fid):
    rar = SUB / f"submission-{fid}.rar"
    if not rar.exists():
        urllib.request.urlretrieve(BASE + f"submission-{fid}.rar", rar)
    cache = SUB / f"monthly_{fid}.csv.gz"
    if not cache.exists():
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([WIN_TAR, "-xf", str(rar), "-C", tmp], check=True)
            csv = next(Path(tmp).rglob("*.csv"))
            df = pd.read_csv(csv, usecols=["id"] + [f"F{i}" for i in range(1, H + 1)])
        df = df[df["id"].astype(str).str.startswith("M")]
        df.to_csv(cache, index=False, compression="gzip")
    return pd.read_csv(cache).set_index("id"), BASE + f"submission-{fid}.rar", rar.stat().st_size


def scores(test, pt, denom, n2_s, n2_m):
    s, m = smape(test, pt), np.mean(np.abs(test - pt), axis=1) / denom
    return s.mean(), m.mean(), 0.5 * (s.mean() / n2_s + m.mean() / n2_m)


def main():
    info = pd.read_excel(SUB / "Submission_Info.xlsx", sheet_name=0)
    info["ID"] = info["ID"].astype(str)
    meth = pd.read_excel(SUB / "Evaluation_and_Ranks.xlsx", sheet_name="Methods")
    meth["User ID"] = meth["User ID"].astype(str)
    ev = pd.read_excel(SUB / "Evaluation_and_Ranks.xlsx", sheet_name="Point Forecasts-Summary",
                       header=None).iloc[2:]
    ev[0] = ev[0].astype(str)
    pub = {r[0]: (float(r[6]), float(r[13]), float(r[20])) for _, r in ev.iterrows()}

    # ---- all 48,000 Monthly series (official train/test files)
    tr = pd.read_csv(RAW / "Monthly-train.csv").set_index("V1")
    te = pd.read_csv(RAW / "Monthly-test.csv").set_index("V1")
    all_ids = list(te.index)
    test_all = te.to_numpy(float)[:, :H]
    trv = tr.loc[all_ids].to_numpy(float)
    denom_all = np.empty(len(all_ids))
    for i, row in enumerate(trv):
        y = row[~np.isnan(row)]
        denom_all[i] = np.mean(np.abs(y[M:] - y[:-M]))
    n2_all = pd.read_csv(RAW / "submission-Naive2.csv").set_index("id").loc[all_ids].to_numpy(float)[:, :H]
    n2s_all, n2m_all = smape(test_all, n2_all).mean(), (np.mean(np.abs(test_all - n2_all), axis=1) / denom_all).mean()
    print(f"Naive2, 48,000 Monthly: sMAPE {n2s_all:.3f} MASE {n2m_all:.3f} "
          f"(published {pub['Naive2'][0]:.3f} / {pub['Naive2'][1]:.3f})")

    # ---- the 1,000-series sample, exactly as N3_m4_official.load_series()
    sample = pd.read_parquet(ROOT / "data" / "m4_monthly_sample_1000.parquet")
    ids = sorted(sample.unique_id.unique())
    train = {u: g.sort_values("ds")["y"].to_numpy(float)[:-H] for u, g in sample.groupby("unique_id")}
    test = te.loc[ids].to_numpy(float)[:, :H]
    n2 = pd.read_csv(RAW / "submission-Naive2.csv").set_index("id").loc[ids].to_numpy(float)[:, :H]
    denom = np.array([np.mean(np.abs(train[u][M:] - train[u][:-M])) for u in ids])
    # consistency: the parquet training part equals Monthly-train.csv
    pos = pd.Series(range(len(all_ids)), index=all_ids)
    assert np.allclose(denom, denom_all[pos.loc[ids].to_numpy()]), "sample train != Monthly-train"
    n2s, n2m = smape(test, n2).mean(), (np.mean(np.abs(test - n2), axis=1) / denom).mean()

    rows, store = [], {}
    for label, fid, key in SUBMISSIONS:
        fc, url, size = fetch(fid)
        missing = set(all_ids) - set(fc.index)
        assert not missing, f"{label}: {len(missing)} Monthly series missing"
        pt_all = fc.loc[all_ids].to_numpy(float)
        assert np.isfinite(pt_all).all(), f"{label}: non-finite forecasts"
        s_a, m_a, o_a = scores(test_all, pt_all, denom_all, n2s_all, n2m_all)
        pt = fc.loc[ids].to_numpy(float)
        store[f"{label}_pt"] = pt
        s_s, m_s, o_s = scores(test, pt, denom, n2s, n2m)
        irow = info[info["ID"] == str(key)].iloc[0]
        mrow = meth[meth["User ID"] == str(key)]
        authors = mrow["Team Members"].iloc[0] if len(mrow) else irow["Author(s)"]
        p = pub.get(str(key), (np.nan,) * 3)
        rows.append({"label": label, "submission": str(key), "rank_owa_overall": int(irow["Rank (OWA)"]),
                     "authors": str(authors).strip(), "type": irow["Type"], "url": url, "size_bytes": size,
                     "sMAPE_48k": s_a, "MASE_48k": m_a, "OWA_48k": o_a,
                     "sMAPE_pub": p[0], "MASE_pub": p[1], "OWA_pub": p[2],
                     "sMAPE_1000": s_s, "MASE_1000": m_s, "OWA_1000": o_s})
        print(f"{label:12s} 48k OWA {o_a:.4f} (pub {p[2]:.4f})  sMAPE {s_a:.3f} ({p[0]:.3f})  "
              f"MASE {m_a:.3f} ({p[1]:.3f})  | sample OWA {o_s:.4f}")

    np.savez_compressed(OUT / "forecasts_published_full.npz", ids=np.array(ids), **store)
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "published_check.csv", index=False)

    own = pd.read_csv(OUT / "summary.csv")[["method", "sMAPE", "MASE", "OWA"]]
    own["source"] = "paper"
    pubs = res.rename(columns={"label": "method", "sMAPE_1000": "sMAPE", "MASE_1000": "MASE",
                               "OWA_1000": "OWA"})[["method", "sMAPE", "MASE", "OWA"]]
    pubs["source"] = "M4 published"
    comb = pd.concat([own, pubs]).sort_values("OWA")
    print("\n1,000-series sample, full context (official M4 test period):")
    print(comb.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
