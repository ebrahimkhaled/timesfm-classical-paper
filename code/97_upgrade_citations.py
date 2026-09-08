"""Replace preprint citations in refs.bib with their published versions of record.

Citing the version of record rather than the arXiv preprint is better scholarly practice and
is what a referee expects. Five of the six preprint-cited works have since appeared:

  das2024timesfm       -> ICML 2024, PMLR 235:10148-10167
  woo2024moirai        -> ICML 2024, PMLR 235:53140-53164
  ansari2024chronos    -> Transactions on Machine Learning Research, 2024
  aksu2024gifteval     -> NeurIPS 2024 Time Series in the Age of Large Models workshop
  adler2026calibrated  -> ICLR 2026
  paszke2019pytorch    -> NeurIPS 32 (2019), 8024-8035

meyer2025leakage has no published version and stays a preprint, correctly labelled as one.

PMLR, TMLR, OpenReview and the Curran NeurIPS proceedings do not mint DOIs, so these entries
carry a `url` to the proceedings page and keep the arXiv identifier in `note` for readers who
want the open copy. Leaving the arXiv DOI in the `doi` field would be wrong: it identifies the
preprint, not the version being cited.
"""

from __future__ import annotations

import re
from pathlib import Path

BIB = Path(__file__).resolve().parent.parent / "manuscript" / "refs.bib"

REPLACEMENTS = {
"das2024timesfm": r"""@inproceedings{das2024timesfm,
  author    = {Abhimanyu Das and Weihao Kong and Rajat Sen and Yichen Zhou},
  title     = {A Decoder-Only Foundation Model for Time-Series Forecasting},
  booktitle = {Proceedings of the 41st International Conference on Machine Learning},
  series    = {Proceedings of Machine Learning Research},
  volume    = {235},
  pages     = {10148--10167},
  publisher = {PMLR},
  year      = {2024},
  note      = {Preprint: arXiv:2310.10688},
  url       = {https://proceedings.mlr.press/v235/das24c.html}
}""",
"woo2024moirai": r"""@inproceedings{woo2024moirai,
  author    = {Gerald Woo and Chenghao Liu and Akshat Kumar and Caiming Xiong and
               Silvio Savarese and Doyen Sahoo},
  title     = {Unified Training of Universal Time Series Forecasting Transformers},
  booktitle = {Proceedings of the 41st International Conference on Machine Learning},
  series    = {Proceedings of Machine Learning Research},
  volume    = {235},
  pages     = {53140--53164},
  publisher = {PMLR},
  year      = {2024},
  note      = {Preprint: arXiv:2402.02592},
  url       = {https://proceedings.mlr.press/v235/woo24a.html}
}""",
"ansari2024chronos": r"""@article{ansari2024chronos,
  author  = {Abdul Fatir Ansari and Lorenzo Stella and Ali Caner T{\"u}rkmen and
             Xiyuan Zhang and Pedro Mercado and Huibin Shen and Oleksandr Shchur and
             Syama Sundar Rangapuram and Sebastian Pineda Arango and Shubham Kapoor and
             Jasper Zschiegner and Danielle C. Maddix and Hao Wang and
             Michael W. Mahoney and Kari Torkkola and Andrew Gordon Wilson and
             Michael Bohlke-Schneider and Yuyang Wang},
  title   = {Chronos: Learning the Language of Time Series},
  journal = {Transactions on Machine Learning Research},
  year    = {2024},
  note    = {Preprint: arXiv:2403.07815},
  url     = {https://openreview.net/forum?id=gerNCVqqtR}
}""",
"aksu2024gifteval": r"""@inproceedings{aksu2024gifteval,
  author    = {Taha Aksu and Gerald Woo and Juncheng Liu and Xu Liu and Chenghao Liu and
               Silvio Savarese and Caiming Xiong and Doyen Sahoo},
  title     = {{GIFT-Eval}: A Benchmark for General Time Series Forecasting Model Evaluation},
  booktitle = {NeurIPS Workshop on Time Series in the Age of Large Models},
  year      = {2024},
  note      = {Preprint: arXiv:2410.10393},
  url       = {https://arxiv.org/abs/2410.10393}
}""",
"adler2026calibrated": r"""@inproceedings{adler2026calibrated,
  author    = {Coen Adler and Yuxin Chang and Felix Draxler and Samar Abdi and
               Padhraic Smyth},
  title     = {Beyond Accuracy: Are Time Series Foundation Models Well-Calibrated?},
  booktitle = {Proceedings of the International Conference on Learning Representations},
  year      = {2026},
  note      = {Preprint: arXiv:2510.16060},
  url       = {https://arxiv.org/abs/2510.16060}
}""",
"paszke2019pytorch": r"""@inproceedings{paszke2019pytorch,
  author    = {Adam Paszke and Sam Gross and Francisco Massa and Adam Lerer and
               James Bradbury and Gregory Chanan and Trevor Killeen and others},
  title     = {\pkg{PyTorch}: An Imperative Style, High-Performance Deep Learning Library},
  booktitle = {Advances in Neural Information Processing Systems 32},
  pages     = {8024--8035},
  publisher = {Curran Associates},
  year      = {2019},
  note      = {Preprint: arXiv:1912.01703},
  url       = {https://papers.neurips.cc/paper/9015-pytorch-an-imperative-style-high-performance-deep-learning-library}
}""",
"meyer2025leakage": r"""@misc{meyer2025leakage,
  author = {Marcel Meyer and Sascha Kaltenpoth and Kevin Zalipski and Oliver M{\"u}ller},
  title  = {Rethinking Evaluation in the Era of Time Series Foundation Models:
            (Un)known Information Leakage Challenges},
  year   = {2025},
  note   = {Preprint, arXiv:2510.13654; no published version as of September 2026},
  doi    = {10.48550/arXiv.2510.13654}
}""",
}


def main() -> None:
    text = BIB.read_text(encoding="utf-8")
    n = 0
    for key, new in REPLACEMENTS.items():
        pat = re.compile(r"@\w+\{" + re.escape(key) + r",.*?\n\}", re.S)
        if not pat.search(text):
            print(f"  ! {key}: entry not found, skipped")
            continue
        text = pat.sub(lambda _m, v=new: v, text, count=1)
        n += 1
        print(f"  upgraded {key}")
    BIB.write_text(text, encoding="utf-8")
    print(f"\n{n} entries rewritten to cite the version of record")


if __name__ == "__main__":
    main()
