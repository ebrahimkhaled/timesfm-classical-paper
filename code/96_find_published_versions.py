"""Find published versions of the works currently cited as arXiv preprints.

Citing the version of record rather than the preprint is better practice and is what a
referee expects. DBLP is the authoritative index for machine-learning conference and journal
venues, so each title is looked up there and every indexed venue is printed for inspection --
the choice of which record to cite is made by hand, not automatically.
"""

from __future__ import annotations

import io
import json
import sys
import time
import urllib.parse
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

QUERIES = [
    ("das2024timesfm", "A decoder-only foundation model for time-series forecasting"),
    ("ansari2024chronos", "Chronos: Learning the Language of Time Series"),
    ("woo2024moirai", "Unified Training of Universal Time Series Forecasting Transformers"),
    ("aksu2024gifteval", "GIFT-Eval: A Benchmark For General Time Series Forecasting"),
    ("meyer2025leakage", "Rethinking Evaluation in the Era of Time Series Foundation Models"),
    ("adler2026calibrated", "Beyond Accuracy: Are Time Series Foundation Models Well-Calibrated"),
    ("paszke2019pytorch", "PyTorch: An Imperative Style, High-Performance Deep Learning Library"),
]


UA = "ref-check/1.0 (mailto:ebrahimkhaled@alexu.edu.eg)"


def dblp(title: str, tries: int = 4) -> list[dict]:
    """Query DBLP. It rejects requests without a User-Agent and rate-limits hard, so the
    header is set explicitly and failures back off rather than giving up."""
    url = ("https://dblp.org/search/publ/api?"
           + urllib.parse.urlencode({"q": title, "format": "json", "h": 6}))
    data = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.load(r)
            break
        except Exception as exc:  # noqa: BLE001
            wait = 5 * (attempt + 1)
            print(f"    . attempt {attempt + 1} failed ({exc}); retrying in {wait}s")
            time.sleep(wait)
    if data is None:
        print("    ! DBLP unavailable for this title")
        return []
    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    return [h.get("info", {}) for h in hits]


for key, title in QUERIES:
    print("=" * 78)
    print(f"{key}   ({title[:60]})")
    for info in dblp(title):
        venue = info.get("venue", "?")
        if isinstance(venue, list):
            venue = ", ".join(venue)
        typ = info.get("type", "?")
        year = info.get("year", "?")
        t = info.get("title", "?")
        doi = info.get("doi", "")
        pages = info.get("pages", "")
        vol = info.get("volume", "")
        mark = "  <-- PUBLISHED" if "CoRR" not in venue and typ != "Informal and Other Publications" else ""
        print(f"  [{typ:<34}] {year} {venue}{(' vol ' + vol) if vol else ''}"
              f"{(' pp ' + pages) if pages else ''}{mark}")
        print(f"      {t[:88]}")
        if doi:
            print(f"      doi:{doi}")
    time.sleep(3)
