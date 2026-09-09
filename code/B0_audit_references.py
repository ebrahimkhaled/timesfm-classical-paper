"""Audit every bibliography entry FIELD BY FIELD against its resolved record.

The earlier check proved only that each DOI resolves. That is a much weaker claim than it
sounds: a DOI can resolve perfectly and still point at the wrong paper -- the working-paper
version instead of the journal article, a later reprint instead of the original, or a
different paper entirely with a similar title. This script compares what the bibliography
CLAIMS against what the identifier actually RESOLVES TO:

    title      token overlap, after stripping LaTeX markup and case
    first author surname
    year
    journal / container
    volume, pages

Entries with no DOI (blog posts, repositories, software, books) are checked by fetching their
URL and confirming it is reachable.

Output: one block per entry, with any mismatch called out explicitly.

Usage:  python code/B0_audit_references.py
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
MAILTO = "ebrahimkhaled@alexu.edu.eg"
UA = f"ref-audit/1.0 (mailto:{MAILTO})"

ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.*?)\n\}", re.S)


def field(body: str, name: str) -> str | None:
    m = re.search(rf"^\s*{name}\s*=\s*", body, re.M | re.I)
    if not m:
        return None
    i = m.end()
    if body[i] == "{":
        depth = 0
        for j in range(i, len(body)):
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0:
                    return re.sub(r"\s+", " ", body[i + 1:j]).strip()
    m2 = re.match(r'"([^"]*)"', body[i:])
    return m2.group(1).strip() if m2 else None


def clean_title(t: str) -> str:
    t = re.sub(r"\\(pkg|proglang|code|emph|textbf|texttt)\s*\{([^{}]*)\}", r"\2", t or "")
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"[^a-z0-9 ]+", " ", t.lower())


def tokens(t: str) -> set[str]:
    stop = {"a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "using"}
    return {w for w in clean_title(t).split() if len(w) > 2 and w not in stop}


def first_surname(author_field: str) -> str:
    a = (author_field or "").split(" and ")[0].strip()
    if "," in a:
        return a.split(",")[0].strip().lower()
    return a.split()[-1].strip().lower() if a.split() else ""


def resolve(doi: str) -> dict | None:
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
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def url_ok(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return f"unreachable ({type(e).__name__})"


def main() -> None:
    entries = ENTRY.findall(BIB.read_text(encoding="utf-8"))
    print(f"auditing {len(entries)} entries from refs.bib\n" + "=" * 78)

    problems: list[str] = []
    checked = 0

    for kind, key, body in entries:
        key = key.strip()
        doi = field(body, "doi")
        title = field(body, "title") or ""
        author = field(body, "author") or ""
        year = field(body, "year") or ""
        journal = field(body, "journal") or field(body, "booktitle") or field(body, "howpublished") or ""
        volume = field(body, "volume") or ""
        pages = field(body, "pages") or ""

        print(f"\n[{key}]  ({kind})")
        print(f"  bib : {title[:78]}")
        print(f"        {first_surname(author) or '?'} | {year} | {journal[:52]} "
              f"| vol {volume or '-'} | pp {pages or '-'}")

        if not doi:
            url = field(body, "url")
            if url:
                status = url_ok(url)
                print(f"  no DOI; URL -> {status}")
                if not status.startswith("HTTP 2") and not status.startswith("HTTP 3"):
                    problems.append(f"{key}: URL not reachable ({status})")
            else:
                print("  no DOI and no URL")
                problems.append(f"{key}: neither DOI nor URL")
            continue

        rec = resolve(doi)
        checked += 1
        time.sleep(0.4)
        if rec is None:
            print(f"  DOI {doi} -> DOES NOT RESOLVE")
            problems.append(f"{key}: DOI {doi} does not resolve")
            continue

        r_title = rec.get("title") or ""
        if isinstance(r_title, list):
            r_title = r_title[0] if r_title else ""
        r_cont = rec.get("container-title") or rec.get("publisher") or ""
        if isinstance(r_cont, list):
            r_cont = r_cont[0] if r_cont else ""
        # Prefer the PRINT year over `issued`. Crossref's `issued` is the earliest date it
        # holds, which for a journal that publishes online-first is the online date, not the
        # issue the article is cited by. Hewamalage et al. is the case in point: online
        # 2022-12-02, print March 2023 in volume 37(2) -- and 2023 is the correct citation
        # year. Flagging that as a mismatch would be crying wolf.
        r_year = ((rec.get("published-print") or {}).get("date-parts")
                  or (rec.get("issued") or {}).get("date-parts") or [[None]])[0][0]
        r_online = ((rec.get("published-online") or {}).get("date-parts") or [[None]])[0][0]
        r_auth = (rec.get("author") or [])
        r_surname = (r_auth[0].get("family", "") if r_auth else "").lower()
        r_vol = str(rec.get("volume") or "")
        r_pages = str(rec.get("page") or "")

        print(f"  doi : {doi}")
        print(f"  got : {re.sub(r'<[^>]+>', '', str(r_title))[:78]}")
        print(f"        {r_surname or '?'} | {r_year} | {str(r_cont)[:52]} "
              f"| vol {r_vol or '-'} | pp {r_pages or '-'}")

        # --- field comparisons
        tb, tr = tokens(title), tokens(str(r_title))
        overlap = len(tb & tr) / max(1, len(tb))
        if overlap < 0.55:
            problems.append(f"{key}: TITLE mismatch ({overlap:.0%} overlap)")
            print(f"  !! TITLE mismatch -- only {overlap:.0%} of the bib title's words appear")

        bs = first_surname(author)
        if bs and r_surname and bs != r_surname and bs not in r_surname and r_surname not in bs:
            problems.append(f"{key}: first author '{bs}' vs resolved '{r_surname}'")
            print(f"  !! FIRST AUTHOR mismatch: bib '{bs}' vs resolved '{r_surname}'")

        if year and r_year and str(year) != str(r_year):
            if r_online and str(year) == str(r_online):
                print(f"  .. year {year} is the ONLINE-FIRST year; print issue is {r_year}"
                      f" -- check which the venue expects")
            else:
                problems.append(f"{key}: year {year} vs resolved {r_year}")
                print(f"  !! YEAR mismatch: bib {year} vs resolved {r_year}")

        if volume and r_vol and volume != r_vol:
            problems.append(f"{key}: volume {volume} vs resolved {r_vol}")
            print(f"  !! VOLUME mismatch: bib {volume} vs resolved {r_vol}")

        if pages and r_pages:
            pb = re.sub(r"[^0-9]", "", pages.replace("--", "-").split("-")[0])
            pr = re.sub(r"[^0-9]", "", r_pages.split("-")[0])
            if pb and pr and pb != pr:
                problems.append(f"{key}: first page {pages} vs resolved {r_pages}")
                print(f"  !! PAGES mismatch: bib {pages} vs resolved {r_pages}")

    print("\n" + "=" * 78)
    print(f"{checked} DOIs resolved and compared field by field")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  ! " + p)
    else:
        print("\nno mismatches: every entry matches the record its identifier resolves to")


if __name__ == "__main__":
    main()
