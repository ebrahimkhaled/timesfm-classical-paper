"""Summarise the multi-agent review journal: which findings survived adversarial verification."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WF = Path(
    r"C:\Users\ebrah\.claude\projects"
    r"\C--Users-ebrah-AppData-Roaming-Claude-scratch-workspaces-df6a2419-fa15-4bcb-8e1c-3799afd27416-97f100ca-5a65-4e69-b0fb-cf4296fe8298-scratch-2026-09-08-222e83"
    r"\8faf84e5-3b50-4fe4-85a2-dc4bd439fe92\subagents\workflows\wf_efccb198-d37"
)

findings, verdicts = [], []
for line in (WF / "journal.jsonl").read_text(encoding="utf-8").splitlines():
    try:
        j = json.loads(line)
    except Exception:
        continue
    label = j.get("label") or j.get("agentLabel") or ""
    r = j.get("result")
    if isinstance(r, dict) and "findings" in r:
        for f in r["findings"]:
            findings.append((label, f))
    elif isinstance(r, dict) and "refuted" in r:
        verdicts.append((label, r))

print(f"REVIEWERS reported {len(findings)} findings; {len(verdicts)} verdicts returned\n")

by_dim: dict[str, list] = {}
for label, f in findings:
    by_dim.setdefault(label or "?", []).append(f)

for dim, fs in by_dim.items():
    print(f"--- {dim} ({len(fs)}) ---")
    for f in fs:
        print(f"  [{f.get('severity','?'):<8}] {f.get('claim','')}")
        print(f"             loc: {f.get('location','')}")
    print()

print("=" * 70)
kept = [v for _, v in verdicts if not v.get("refuted")]
killed = [v for _, v in verdicts if v.get("refuted")]
print(f"VERDICTS: {len(kept)} confirmed, {len(killed)} refuted")
print("\nCONFIRMED (real defects):")
for v in kept:
    print(f"  [{v.get('corrected_severity')}] {str(v.get('reason'))[:260]}")
