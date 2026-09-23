"""Build manuscript_jof/supporting_information.tex (JoF: appendices as separate files).

S1  Results under the mean absolute percentage error (the appendix of the AJS version)
S2  Mean MASE with Monte Carlo standard errors (N7 si_mcse.tex)
S3  Coverage of 80% intervals by process (N7 si_coverage.tex)
S4  Gaussian versus split-conformal intervals (N7 si_conformal.tex)
S5  Response-surface regressions of the robustness study (from results/robust/robust_response.csv)
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "manuscript_jof"
SRC_AJS = ROOT / "manuscript" / "timesfm_vs_classical.tex"


def response_table():
    full = pd.read_csv(ROOT / "results" / "robust" / "robust_response.csv")
    return (one_table(full[full.dgp.isin(["D1", "D2", "D3", "D4"])], "D1--D4", "tab:si-response")
            + "\n" + one_table(full[full.dgp.isin(["D5", "D6", "D7", "D8", "D9"])], "D5--D9",
                               "tab:si-response2"))


def one_table(r, part, label):
    r = r[r.term != "Intercept"].copy()
    name = {"logn": "$\\log_2 n$"}
    rows = []
    for _, x in r.iterrows():
        t = x.term
        if t.startswith("C(variant"):
            t = "version: " + t.split("[T.")[1].rstrip("]").replace("_", " ")
        elif t.startswith("par_"):
            t = "parameter " + t[4:].replace("_", " ")
        else:
            t = name.get(t, t)
        rows.append(f"{x.dgp} & {t} & {x.coef:.3f} & [{x.lo:.3f}, {x.hi:.3f}] & {x.p:.3f} & {x.r2:.3f} \\\\")
    body = "\n".join(rows)
    return ("\\begin{table}[!htbp]\n\\centering\n\\begin{threeparttable}\n"
            f"\\caption{{Response-surface regressions of the robustness study, processes {part}.}}\n"
            f"\\label{{{label}}}\n"
            "\\scriptsize\n\\begin{tabular}{llcccc}\n\\toprule\n"
            "Process & Term & Coefficient & 95\\% interval & $p$ & $R^2$ \\\\\n\\midrule\n"
            f"{body}\n\\bottomrule\n\\end{{tabular}}\n"
            "\\begin{tablenotes}[flushleft]\\footnotesize\n\\item \\textit{Note:} One ordinary "
            "least-squares regression per process of the per-series $\\log_2$ ratio of the MASE of "
            "TimesFM-3 to that of AutoARIMA on $\\log_2 n$, the version (reference: random parameters "
            "with Gaussian innovations) and the drawn parameters, each standardised to mean 0 and "
            "standard deviation 1. Heteroskedasticity-robust (HC3) standard errors; 3\\,200 series per "
            "process (3\\,188 for D8, where series with a zero MASE denominator are excluded). Positive "
            "coefficients move the ratio against TimesFM-3.\n\\end{tablenotes}\n"
            "\\end{threeparttable}\n\\end{table}\n")


def main():
    si = (D / "supporting_information.tex").read_text(encoding="utf-8")
    head = si[:si.index("\\maketitle") + len("\\maketitle")]
    head = head.replace("Section S1 onwards.", "Sections S1 to S5.")
    if "\\graphicspath" not in head:
        head = head.replace("\\usepackage{xurl}", "\\usepackage{xurl}\n\\graphicspath{{images/}{./images/}}")
    ajs = SRC_AJS.read_text(encoding="utf-8")
    app = ajs[ajs.index("\n\\appendix\n") + len("\n\\appendix\n"):ajs.index("\\end{document}")]
    app = app.replace("\\label{app:mape}", "\\label{si:mape}")
    (D / "si_response.tex").write_text(response_table(), encoding="utf-8")
    body = f"""
{app.strip()}

\\section{{Monte Carlo standard errors}}
\\label{{si:mcse}}

\\tableref{{tab:si-mcse}} gives the mean MASE of the six methods of the main design in every cell,
with its Monte Carlo standard error.

\\input{{si_mcse}}

\\section{{Coverage by process}}
\\label{{si:coverage}}

\\tableref{{tab:si-coverage}} gives the empirical coverage of the nominal 80\\% intervals of the four
foundation-model configurations and of AutoARIMA and AutoETS, by process, and
\\tableref{{tab:si-conformal}} compares the Gaussian and split-conformal intervals of the two classical
models at $n \\geq 96$.

\\input{{si_coverage}}

\\input{{si_conformal}}

\\section{{Response-surface regressions}}
\\label{{si:response}}

Tables~\\ref{{tab:si-response}} and~\\ref{{tab:si-response2}} report the regressions summarised in the section of the main text on
randomised parameters and departures from the assumptions.

\\input{{si_response}}

\\end{{document}}
"""
    # USG.cls cannot place floats on the title page: start the body on a new page.
    (D / "supporting_information.tex").write_text(head + "\n\\clearpage\n" + body, encoding="utf-8")
    print("supporting_information.tex rebuilt")


if __name__ == "__main__":
    main()
