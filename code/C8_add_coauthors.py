"""Add Somia Mohamed Aly and Ahmed El-Kotory as co-authors, and thank Allah in the acknowledgements.

Name forms. "Ahmed El-Kotory" is the display form used on every earlier paper in the family (the
e-mail address spells it elkatory, deliberately). The ORCID is taken from the EF manuscript and is
printed only after the public ORCID record confirms it belongs to Ahmed El-Kotory; if the record
cannot be fetched or does not match, it is omitted rather than printed unchecked. The project holds no record of Somia
Mohamed Aly's affiliation or ORCID, so her affiliation is given as Alexandria University pending
confirmation, and no ORCID is printed for her.

Author order follows the request: Ebrahim Khaled Ebrahim, Somia Mohamed Aly, Ahmed El-Kotory.
Ebrahim remains the corresponding author, so the address block is unchanged.

Also updated: the Zenodo creators (effective only at the next release), and the arXiv metadata
generator, which now reads the authors from \\Plainauthor and carries the Zenodo concept DOI
instead of a placeholder.
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "manuscript" / "timesfm_vs_classical.tex"
ZEN = ROOT / ".zenodo.json"
A1 = ROOT / "code" / "A1_arxiv_metadata.py"

KOTORY_ORCID = "0009-0000-1485-0768"
ZENODO_DOI = "doi:10.5281/zenodo.22681072"


def swap(s: str, old: str, new: str) -> str:
    pattern = r"\s+".join(re.escape(tok) for tok in old.split())
    matches = list(re.finditer(pattern, s))
    assert len(matches) == 1, f"{len(matches)} matches for: {old.split()[:8]}"
    m = matches[0]
    return s[:m.start()] + new + s[m.end():]


def orcid_holder(orcid: str) -> str:
    req = urllib.request.Request(f"https://pub.orcid.org/v3.0/{orcid}/person",
                                 headers={"Accept": "application/json"})
    try:
        person = json.load(urllib.request.urlopen(req, timeout=40))
    except Exception as exc:  # network failure: report it, never guess
        return f"(record unavailable: {exc})"
    name = person.get("name") or {}
    given = (name.get("given-names") or {}).get("value") or ""
    family = (name.get("family-name") or {}).get("value") or ""
    return f"{given} {family}".strip()


def main() -> None:
    holder = orcid_holder(KOTORY_ORCID)
    verified = "ahmed" in holder.lower() and any(k in holder.lower() for k in ("kotory", "katory"))
    print(f"ORCID {KOTORY_ORCID} -> {holder!r}: {'verified' if verified else 'NOT verified, omitted'}")
    kotory_orcid_tex = rf"\,\orcidlink{{{KOTORY_ORCID}}}" if verified else ""

    # ---- manuscript ----------------------------------------------------------------------
    s = TEX.read_text(encoding="utf-8")
    if "Somia Mohamed Aly" in s:
        print("manuscript: co-authors already present")
    else:
        s = swap(s, r"""\author{Ebrahim Khaled Ebrahim\,\orcidlink{0009-0006-7839-8778}\\
        Alexandria University}""",
                 r"""\author{Ebrahim Khaled Ebrahim\,\orcidlink{0009-0006-7839-8778}\\ Alexandria University \And
        Somia Mohamed Aly\\ Alexandria University \And
        Ahmed El-Kotory""" + kotory_orcid_tex + r"""\\ Alexandria University}""")
        s = swap(s, r"""\Plainauthor{Ebrahim Khaled Ebrahim}""",
                 r"""\Plainauthor{Ebrahim Khaled Ebrahim, Somia Mohamed Aly, Ahmed El-Kotory}""")
        s = swap(s, r"""The author used a large language model solely to improve the language and readability of this
manuscript and to assist with the implementation of the simulation code. The author reviewed and
edited all content and takes full responsibility for the content of this publication.""",
                 r"""First and foremost, the authors thank Allah, the Almighty, for everything He has given them,
including the ability to complete this work.

The authors used a large language model solely to improve the language and readability of this
manuscript and to assist with the implementation of the simulation code. The authors reviewed and
edited all content and take full responsibility for the content of this publication.""")
        s = swap(s, r"""The author declares no competing interests.""",
                 r"""The authors declare no competing interests.""")
        TEX.write_text(s, encoding="utf-8")
        print("manuscript: three authors, acknowledgement of Allah, plural declarations")

    # ---- Zenodo creators (applies to the next release) -------------------------------------
    meta = json.loads(ZEN.read_text(encoding="utf-8"))
    names = [c["name"] for c in meta["creators"]]
    if "Aly, Somia Mohamed" not in names:
        kotory = {"name": "El-Kotory, Ahmed", "affiliation": "Alexandria University"}
        if verified:
            kotory["orcid"] = KOTORY_ORCID
        meta["creators"] += [{"name": "Aly, Somia Mohamed", "affiliation": "Alexandria University"},
                             kotory]
        ZEN.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("zenodo creators:", [c["name"] for c in meta["creators"]])

    # ---- arXiv metadata generator ----------------------------------------------------------
    a1 = A1.read_text(encoding="utf-8")
    if "brace_arg(\"Plainauthor\")" not in a1:
        title_line = 'title = re.sub(r"\\s+", " ", brace_arg("Plaintitle") or brace_arg("title")).strip()'
        assert a1.count(title_line) == 1, "title line not found in A1"
        a1 = a1.replace(title_line, title_line + '\nauthors = re.sub(r"\\s+", " ", brace_arg("Plainauthor")).strip()')
        a1 = swap(a1, "## Authors\nEbrahim Khaled Ebrahim\n", "## Authors\n{authors}\n")
        a1 = swap(a1, "protocol: [ZENODO CONCEPT DOI -- insert after publishing the deposit]",
                  f"protocol: {ZENODO_DOI}")
        a1 = swap(a1, "This is IRREVERSIBLE and is the author's decision, not mine.",
                  "This is IRREVERSIBLE and is the authors' decision, not mine.")
        a1 = swap(a1, "The author is already endorsed here and his other preprints sit in it,",
                  "The submitting author (Ebrahim Khaled Ebrahim) is already endorsed here and the author's other\n"
                  "  preprints sit in it,")
        a1 = swap(a1, """None required. This paper shares no text with the author's thesis or with his goodness-of-fit
preprints (arXiv:2607.15454, arXiv:2607.16344, arXiv:2608.20511); it is his first paper on
forecasting and has no textual overlap with any of them.""",
                  """None required. This paper shares no text with the first author's thesis or with the
goodness-of-fit preprints arXiv:2607.15454, arXiv:2607.16344 and arXiv:2608.20511.""")
        a1 = swap(a1, "Check the title, the author name,", "Check the title, the author names,")
        A1.write_text(a1, encoding="utf-8")
        print("A1: authors from \\Plainauthor, Zenodo DOI in Comments, plural wording")
    else:
        print("A1: already updated")


if __name__ == "__main__":
    main()
