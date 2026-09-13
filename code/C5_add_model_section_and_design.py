"""Revision after supervisor review, part B: a section on TimesFM-3, and the design section.

Addresses: "What is TimesFM-3?" -- a dedicated section on the model; the checkpoint identifier
explained rather than left bare; an opening statement of each section's subdivisions; the
parameter values of the data-generating processes justified with references; the process table
given a title-only caption with a note beneath; consistent leading zeros in the parameters.

Every factual statement about TimesFM-3 is taken from the developers' blog post, the released
configuration and model card, or the installed package source, and is cited to them.
"""

from __future__ import annotations

import re
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "manuscript" / "timesfm_vs_classical.tex"


def swap(s: str, old: str, new: str) -> str:
    pattern = r"\s+".join(re.escape(tok) for tok in old.split())
    matches = list(re.finditer(pattern, s))
    assert len(matches) == 1, f"{len(matches)} matches for: {old.split()[:8]}"
    m = matches[0]
    return s[:m.start()] + new.strip("\n") + s[m.end():]


MODEL_SECTION = r"""
\section{The TimesFM-3 model}
\label{sec:timesfm}

This section summarises the properties of TimesFM-3 that bear on the comparison: its
architecture (\sectionref{sec:tfm-architecture}), its pre-training data
(\sectionref{sec:tfm-data}), and the released checkpoint together with the configuration used in
this study (\sectionref{sec:tfm-config}).

\subsection{Architecture}
\label{sec:tfm-architecture}

TimesFM-3 is the third generation of the TimesFM family of decoder-only time-series foundation
models developed at Google Research \citep{das2024timesfm, timesfm3blog}. Each input series is
normalised and divided into non-overlapping patches of 32 time points, and each patch is
embedded as a token. The released model stacks 20 transformer layers with model dimension 1280
and 16 attention heads, for a total of about 330 million parameters
\citep{timesfm3blog, timesfm3card}.

The principal change from earlier generations is native support for multivariate forecasting.
Layers of causal attention along the time axis alternate with layers of full attention across
variates, so that several target series, past covariates and past--future covariates can be
processed jointly \citep{timesfm3blog}. Forecasts are produced non-autoregressively: a contiguous
patch masking scheme allows the whole horizon to be generated in a single forward pass
\citep{timesfm3blog}, and the released configuration emits output patches of 64 time points
\citep{timesfm3card}. For each step of the horizon the model outputs nine quantiles, from the
10th to the 90th percentile, and its point forecast is the median of these quantiles
\citep{timesfm3blog, timesfm3repo}.

\subsection{Pre-training data}
\label{sec:tfm-data}

TimesFM-3 was pre-trained on a corpus of more than one trillion time points that combines
real-world and synthetic series \citep{timesfm3blog}. According to the model card, the
real-world component includes the GIFT-Eval pre-training corpus \citep{aksu2024gifteval},
Wikipedia page views up to November 2023 and Google Trends queries up to the end of 2022, and it
is supplemented by synthetic and augmented series \citep{timesfm3card}. Two consequences matter
for this study. Public benchmarks may be contained in the corpus, which is why the primary
evaluation uses generated data (\sectionref{sec:dgps}). And because part of the corpus is
synthetic, the model may already be familiar with the parametric families used here even though
it cannot have seen the particular realisations, as discussed in \sectionref{sec:intro}.

\subsection{Released checkpoint and configuration used in this study}
\label{sec:tfm-config}

The pre-trained weights are distributed through the Hugging Face Hub under the repository
identifier \code{google/\allowbreak timesfm-3.0-pytorch} and are loaded with version 3.0.1 of the
\pkg{timesfm} \proglang{Python} package \citep{timesfm3repo, timesfm3card}. They are released
under a non-commercial licence, whose implications are discussed in \sectionref{sec:licence}. In
this study the model is used zero-shot: it receives only the raw context of each series, with no
fine-tuning, no covariates and no information about the seasonal period, and it returns the
median point forecast and the nine deciles for each step of the horizon. Because no quantile
outside the 10th and 90th percentiles is available, the widest prediction interval that can be
formed from its output is the nominal 80\% interval (\sectionref{sec:evaluation}).

"""

DGP_JUSTIFICATION = r"""
The parameter values in \tableref{tab:dgps} were fixed in the pre-registered protocol before any
forecast was produced. They were not taken from a single earlier study; each was chosen so that
its process represents its regime unambiguously, according to four criteria. First, the linear
processes D1--D4 and the conditional mean of D9 use moderate coefficients, none larger than 0.7
in absolute value, so that their autoregressive and moving-average polynomials lie well inside
the stationarity and invertibility regions \citep{brockwell2016introduction} and no automatic
method is assessed at parameter values close to the boundaries of those regions. Second, the
smoothing parameters of the ETS process D5 lie inside the usual region $0 < \beta < \alpha < 1$,
$0 < \gamma < 1 - \alpha$ \citep{hyndman2008ets}, with a small trend parameter so that the level
remains positive over the longest series. Third, the three processes outside the classical
families are placed firmly within the regimes they represent. The break in D6 equals ten standard
deviations of the observation noise, so that its occurrence is not in doubt and the comparison
concerns adaptation to the break rather than its detection \citep{pesaran2007breaks}. D7 follows
the logistic curve, the standard model of saturating growth in diffusion forecasting
\citep{meade2006diffusion}. In D8 a demand occurs with probability 0.3, so the mean interval
between demands is $1/0.3 \approx 3.3$ periods, and demand sizes $1 + \mathrm{Pois}(4)$ have a
squared coefficient of variation of $4/25 = 0.16$; against the cut-offs of 1.32 and 0.49
proposed by \citet{syntetos2005categorization}, the process is intermittent rather than lumpy,
which is the regime for which Croston's method and its variants were developed
\citep{croston1972}. The GARCH(1,1) errors of D9 \citep{bollerslev1986garch} have $\omega = 0.1$
and persistence $a + b = 0.95$, a strongly persistent but covariance-stationary conditional
variance \citep{engle1986persistence}, and GARCH(1,1) is a standard benchmark specification in
volatility forecasting \citep{hansen2005garch}. Fourth, every series has a level of about 100,
or a positive lower asymptote in D7, so that percentage error measures are defined except where
zeros are intrinsic to the process (D8). Two values, the trend parameter of D5 and the lower
asymptote of D7, were adjusted for this reason before any forecast was produced, and both changes
are recorded in the deviation log. The conclusions are conditional on these values, which is
listed among the limitations in \sectionref{sec:limitations}.

Three further design choices require explanation.
"""

REPLACEMENTS = [
    # ---- the new model section precedes the design section, which gains an opening statement
    (r"""\section{Design of the simulation study}
\label{sec:design}

\subsection{Data-generating processes}""",
     MODEL_SECTION + r"""\section{Design of the simulation study}
\label{sec:design}

This section describes the data-generating processes (\sectionref{sec:dgps}), the forecasting
methods compared (\sectionref{sec:methods}), and the evaluation measures and inferential
procedures (\sectionref{sec:evaluation}).

\subsection{Data-generating processes}
\label{sec:dgps}"""),

    # ---- the process table: title-only caption, note beneath, consistent leading zeros
    (r"""\begin{table}[t!]
\centering
\caption{The nine data-generating processes. The final column states which classical family is
correctly specified by construction; for D6--D8 none is, and for D9 the mean is correctly
specified while the conditional variance is not.}
\label{tab:dgps}
\small
\setlength{\tabcolsep}{4pt}""",
     r"""\begin{table}[!htbp]
\centering
\begin{threeparttable}
\caption{The nine data-generating processes and their parameters.}
\label{tab:dgps}
\small\setlength{\tabcolsep}{4pt}"""),
    (r"""$\alpha = .3$, $\beta = .01$, $\gamma = .2$""",
     r"""$\alpha = 0.3$, $\beta = 0.01$, $\gamma = 0.2$"""),
    (r"""$\phi = .6$, $a = .1$, $b = .85$            & ARIMA in mean \\
\bottomrule
\end{tabular}
\end{table}""",
     r"""$\phi = 0.6$, $a = 0.1$, $b = 0.85$         & ARIMA in mean \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item \textit{Note:} The last column states which classical family is correctly specified by
construction; for D6--D8 none is, and for D9 the conditional mean is correctly specified while
the conditional variance is not. In D6, $\sigma$ is the standard deviation of the observation
noise.
\end{tablenotes}
\end{threeparttable}
\end{table}"""),
    (r"""\begin{figure}[t!]
\centering
\includegraphics[width=\textwidth]{../figures/fig1_example_series.pdf}""",
     r"""\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{../figures/fig1_example_series.pdf}"""),

    # ---- justification of the parameter values
    (r"""Three choices in \tableref{tab:dgps} deserve comment, because each was made to keep the
comparison honest rather than to favour an outcome.""",
     DGP_JUSTIFICATION),
    (r"""that is the
behaviour the process is designed to expose.""",
     r"""this is the
behaviour the process is designed to reveal."""),
    (r"""The shortest is deliberately punishing:""",
     r"""The shortest length is deliberately demanding:"""),

    # ---- forecasting methods
    (r"""\subsection{Methods compared}""",
     r"""\subsection{Forecasting methods}
\label{sec:methods}"""),
    (r"""No method receives hand-tuning; each classical model uses its own automatic order and
parameter selection, which is the comparison a practitioner would actually face.
TimesFM-3 is used zero-shot, with no fine-tuning, through the released
\code{google/\allowbreak timesfm-3.0-pytorch} weights \citep{timesfm3repo}; the classical models come from
\pkg{StatsForecast} \citep{statsforecast}.""",
     r"""No method receives manual tuning: each classical model uses its own automatic order and
parameter selection, which is the comparison a practitioner would face. TimesFM-3 is used
zero-shot, as described in \sectionref{sec:tfm-config}, and the classical models are fitted with
\pkg{StatsForecast} \citep{statsforecast}."""),
    (r"""The equal-weight combination of Theta, AutoETS and AutoARIMA is not an optional extra. The
most frequently levelled criticism of foundation-model evaluations is that they are compared
against individual, de-ensembled classical methods, when the classical state of the art is a
combination. Excluding it would build the paper's conclusion into its design.""",
     r"""The equal-weight combination of Theta, AutoETS and AutoARIMA is included deliberately.
Foundation-model evaluations are frequently criticised for comparing against individual classical
methods, whereas the classical state of the art is a combination \citep{makridakis2020m4};
omitting it would bias the design in favour of the foundation model."""),
    (r"""How the combination's \emph{predictive distribution} is formed should also be stated, since one
recommendation rests on it.""",
     r"""The construction of the combination's \emph{predictive distribution} is stated explicitly,
because one recommendation depends on it."""),
    (r"""One asymmetry in the setup should be stated plainly, because it favours the classical side.""",
     r"""One asymmetry in the design favours the classical methods."""),

    # ---- evaluation
    (r"""\subsection{Evaluation}""",
     r"""\subsection{Evaluation measures and statistical inference}"""),
    (r"""Differences in accuracy are tested, not merely tabulated.""",
     r"""Differences in accuracy are tested formally."""),
    (r"""The Diebold--Mariano test \citep{diebold1995comparing}, which is the usual instrument in this
literature, is \emph{not} used anywhere in this paper, and it is worth saying why since its
absence is conspicuous.""",
     r"""The Diebold--Mariano test \citep{diebold1995comparing}, the usual instrument in this
literature, is not used, for the following reasons."""),
]


def main() -> None:
    s = TEX.read_text(encoding="utf-8")
    if "\\label{sec:timesfm}" in s:
        print("part B already applied")
        return
    s = swap(s, r"\section{Introduction}", "\\section{Introduction}\n\\label{sec:intro}")
    for old, new in REPLACEMENTS:
        s = swap(s, old, new)
    TEX.write_text(s, encoding="utf-8")
    print(f"part B applied: model section added, {len(REPLACEMENTS) - 1} design-section edits")


if __name__ == "__main__":
    main()
