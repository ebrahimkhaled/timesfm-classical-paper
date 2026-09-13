"""Revision after supervisor review: bibliography.

1. timesfm3blog carried a wrong author list (Sen, Zhou, Das, Kong). The post's byline reads
   "Ayush Jain and Rajat Sen"; Zhou, Mol, Das and Oymak are thanked in its acknowledgements.
2. New entries supporting the justification of the data-generating parameters. Every DOI was
   resolved through doi.org and every field below is taken from the Crossref record; nothing
   is filled in by inference (subtitles and editions that Crossref does not report are left out).
3. The Hugging Face model card, the source for the pre-training corpus composition.
"""

from __future__ import annotations

from pathlib import Path

BIB = Path(__file__).resolve().parent.parent / "manuscript" / "refs.bib"

OLD_AUTHORS = "  author       = {Rajat Sen and Yichen Zhou and Abhimanyu Das and Weihao Kong},\n"
NEW_AUTHORS = "  author       = {Ayush Jain and Rajat Sen},\n"

NEW_ENTRIES = r"""
@misc{timesfm3card,
  author       = {{Google Research}},
  title        = {\texttt{google/timesfm-3.0-pytorch}},
  howpublished = {Model card, Hugging Face Hub},
  year         = {2026},
  url          = {https://huggingface.co/google/timesfm-3.0-pytorch}
}

@article{syntetos2005categorization,
  author  = {A. A. Syntetos and J. E. Boylan and J. D. Croston},
  title   = {On the Categorization of Demand Patterns},
  journal = {Journal of the Operational Research Society},
  year    = {2005},
  volume  = {56},
  number  = {5},
  pages   = {495--503},
  doi     = {10.1057/palgrave.jors.2601841}
}

@article{engle1986persistence,
  author  = {Robert F. Engle and Tim Bollerslev},
  title   = {Modelling the Persistence of Conditional Variances},
  journal = {Econometric Reviews},
  year    = {1986},
  volume  = {5},
  number  = {1},
  pages   = {1--50},
  doi     = {10.1080/07474938608800095}
}

@article{hansen2005garch,
  author  = {Peter R. Hansen and Asger Lunde},
  title   = {A Forecast Comparison of Volatility Models: Does Anything Beat a {GARCH(1,1)}?},
  journal = {Journal of Applied Econometrics},
  year    = {2005},
  volume  = {20},
  number  = {7},
  pages   = {873--889},
  doi     = {10.1002/jae.800}
}

@book{hyndman2008ets,
  author    = {Rob J. Hyndman and Anne B. Koehler and J. Keith Ord and Ralph D. Snyder},
  title     = {Forecasting with Exponential Smoothing},
  series    = {Springer Series in Statistics},
  publisher = {Springer-Verlag},
  address   = {Berlin},
  year      = {2008},
  doi       = {10.1007/978-3-540-71918-2}
}

@article{meade2006diffusion,
  author  = {Nigel Meade and Towhidul Islam},
  title   = {Modelling and Forecasting the Diffusion of Innovation -- A 25-Year Review},
  journal = {International Journal of Forecasting},
  year    = {2006},
  volume  = {22},
  number  = {3},
  pages   = {519--545},
  doi     = {10.1016/j.ijforecast.2006.01.005}
}

@article{pesaran2007breaks,
  author  = {M. Hashem Pesaran and Allan Timmermann},
  title   = {Selection of Estimation Window in the Presence of Breaks},
  journal = {Journal of Econometrics},
  year    = {2007},
  volume  = {137},
  number  = {1},
  pages   = {134--161},
  doi     = {10.1016/j.jeconom.2006.03.010}
}

@book{brockwell2016introduction,
  author    = {Peter J. Brockwell and Richard A. Davis},
  title     = {Introduction to Time Series and Forecasting},
  series    = {Springer Texts in Statistics},
  publisher = {Springer-Verlag},
  address   = {Cham},
  year      = {2016},
  doi       = {10.1007/978-3-319-29854-2}
}
"""


def main() -> None:
    bib = BIB.read_text(encoding="utf-8")
    if OLD_AUTHORS in bib:
        bib = bib.replace(OLD_AUTHORS, NEW_AUTHORS, 1)
        print("timesfm3blog: author list corrected to the post's byline")
    else:
        assert NEW_AUTHORS in bib, "timesfm3blog author line not found"
        print("timesfm3blog: already corrected")

    added = 0
    for block in NEW_ENTRIES.strip().split("\n\n"):
        key = block.split("{", 1)[1].split(",", 1)[0]
        if "{" + key + "," in bib:
            continue
        bib = bib.rstrip("\n") + "\n\n" + block.strip() + "\n"
        added += 1
    BIB.write_text(bib, encoding="utf-8")
    print(f"added {added} new entries")


if __name__ == "__main__":
    main()
