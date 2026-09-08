"""Validate EVERY DOI in refs.bib by resolving it, and report entries that carry none.

Why this was rewritten
----------------------
The first version of this script checked a hand-typed list of DOIs that was maintained in
parallel with refs.bib. That is exactly the wrong design: the two drifted, the keys stopped
matching, and six DOIs actually present in refs.bib were never checked at all -- every one of
them an arXiv DOI, which `api.crossref.org` does not serve. The manuscript meanwhile claimed
every DOI had been validated. A checker that cannot see what it is checking is worse than none,
because it produces a false assurance.

This version parses refs.bib itself, so it cannot miss an entry, and resolves each DOI through
`doi.org` content negotiation, which answers for BOTH registration agencies -- Crossref for
publisher DOIs and DataCite for arXiv/Zenodo ones. Entries without a DOI are listed separately
rather than passing silently.

Usage:  python code/90_verify_refs.py
"""

from __future__ import annotations

import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "manuscript" / "refs.bib"
OUT = ROOT / "manuscript" / "crossref_verified.json"
MAILTO = "ebrahimkhaled@alexu.edu.eg"
UA = f"ref-check/2.0 (mailto:{MAILTO})"

ENTRY_RE = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", re.S)
DOI_RE = re.compile(r"\bdoi\s*=\s*[{\"]([^}\"]+)[}\"]", re.I)
TITLE_RE = re.compile(r"\btitle\s*=\s*\{(.+?)\}\s*,\s*\n", re.S)


def parse_bib(text: str) -> list[dict]:
    out = []
    for kind, key, body in ENTRY_RE.findall(text):
        doi = DOI_RE.search(body)
        title = TITLE_RE.search(body)
        out.append({
            "key": key.strip(), "kind": kind.lower(),
            "doi": doi.group(1).strip() if doi else None,
            "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else "?",
        })
    return out


def resolve(doi: str) -> dict | None:
    """Resolve a DOI via doi.org content negotiation (works for Crossref AND DataCite)."""
    url = "https://doi.org/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.citationstyles.csl+json", "User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return None
            time.sleep(3 * (attempt + 1))
        except Exception:  # noqa: BLE001
            time.sleep(3 * (attempt + 1))
    return None


def main() -> None:
    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    with_doi = [e for e in entries if e["doi"]]
    without = [e for e in entries if not e["doi"]]

    print(f"refs.bib: {len(entries)} entries, {len(with_doi)} with a DOI, "
          f"{len(without)} without\n")

    good, bad = [], []
    for e in with_doi:
        rec = resolve(e["doi"])
        time.sleep(0.5)
        if rec is None:
            print(f"[FAIL] {e['key']:<22} {e['doi']}  -- does not resolve")
            bad.append(e)
            continue
        got = rec.get("title") or "?"
        if isinstance(got, list):
            got = got[0]
        cont = rec.get("container-title") or rec.get("publisher") or ""
        if isinstance(cont, list):
            cont = cont[0]
        year = ((rec.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        agency = "DataCite" if e["doi"].lower().startswith("10.48550") else "Crossref"
        print(f"[ OK ] {e['key']:<22} {e['doi']}  ({agency})")
        print(f"       {year} | {str(cont)[:70]}")
        print(f"       {re.sub(r'<[^>]+>', '', str(got))[:88]}")
        good.append({**e, "resolved_title": got, "container": cont, "year": year,
                     "agency": agency})

    OUT.write_text(json.dumps(good, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nresolved {len(good)}/{len(with_doi)} -> {OUT.relative_to(ROOT)}")

    if without:
        print(f"\nNo DOI (acceptable only for software/manuals/blogs) -- {len(without)}:")
        for e in without:
            print(f"  {e['kind']:<14} {e['key']:<22} {e['title'][:60]}")
    if bad:
        print(f"\nUNRESOLVED -- {len(bad)}:")
        for e in bad:
            print(f"  {e['key']:<22} {e['doi']}")


if __name__ == "__main__":
    main()
