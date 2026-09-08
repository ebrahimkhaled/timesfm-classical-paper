"""One-off repair: undo the lexicographic misordering in realdata_classical.npz.

The bug
-------
`07_realdata.py` originally labelled windows `unique_id = str(i)`. statsforecast returns rows
sorted lexicographically by unique_id -- "0", "1", "10", "100", "1000", ... -- but the reshape
assumed numeric order, so every classical forecast was paired with the wrong window. The
symptom was unmistakable: seasonal naive scored a mean MASE of 28.9 when, being essentially the
MASE denominator, it must score near 1.

Why a repair rather than a refit
--------------------------------
The forecasts themselves are correct; only their row order is wrong, and the permutation is
known exactly. Row j of the saved array belongs to window `order[j]`, where
`order = sorted(range(N), key=str)`. Inverting that permutation recovers the correct alignment
without repeating a fit that takes roughly fifty minutes.

The source script has been fixed to use zero-padded ids, so a fresh run needs no repair. This
script exists to salvage the arrays already computed, and is idempotent-guarded by writing to a
new file.

Usage:  python code/07c_repair_alignment.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
SRC = RES / "realdata_classical.npz"
BAK = RES / "realdata_classical_misordered.npz"


def main() -> None:
    # np.load keeps the npz file handle open for lazy member access, which blocks the rename
    # on Windows. Materialise every array first, then close.
    with np.load(SRC) as z:
        keys = [k for k in z.files if k != "_order"]
        arrays = {k: np.array(z[k]) for k in keys}

    n = arrays[keys[0]].shape[0]
    order = np.array(sorted(range(n), key=str))
    assert not np.array_equal(order, np.arange(n)), \
        "order is already the identity -- nothing to repair"

    fixed = {}
    for k, arr in arrays.items():
        out = np.empty_like(arr)
        out[order] = arr          # row j of arr belongs to window order[j]
        fixed[k] = out
    fixed["_order"] = np.arange(n)

    SRC.rename(BAK)
    np.savez_compressed(SRC, **fixed)
    print(f"repaired {len(keys)} arrays over {n:,} windows")
    print(f"  original kept at {BAK.name}")
    print(f"  rewrote {SRC.name} in window order")


if __name__ == "__main__":
    main()
