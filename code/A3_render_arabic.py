"""Render SHARH_ARABIC.md as a properly right-to-left HTML and PDF.

Why the standard recipe is not enough here
------------------------------------------
The md-to-pdf skill wraps occasional Arabic BOXES inside an otherwise English document
(`div[dir="rtl"]` with a tinted background). This document is the opposite: it is Arabic
throughout, with English technical terms embedded in nearly every sentence. Left as plain
Markdown the page direction stays LTR, and then:

  * paragraphs align left, so the eye starts on the wrong side of every line;
  * sentence-final punctuation (the colon, the full stop) jumps to the wrong end;
  * a line that opens with an English term or `code` span is laid out backwards relative
    to the Arabic that follows it.

So the PAGE is made RTL and LTR is forced back only where it belongs.

The four rules that actually fix the mixing
-------------------------------------------
1. `body { direction: rtl }` - the document is Arabic, so that is its natural direction.
2. Headings get `unicode-bidi: plaintext`, which picks each heading's direction from its
   first strong character. The headings are written "English - Arabic", so they keep that
   order instead of being flipped by the RTL page.
3. Inline `code` gets `direction: ltr; unicode-bidi: embed`. This is the single most
   important rule: it stops an English identifier inside an Arabic sentence from dragging
   its neighbouring punctuation to the wrong side.
4. `pre` blocks and the numeric table columns are LTR, since code and numbers are read
   left-to-right even inside an Arabic page.

Usage:  python code/A3_render_arabic.py
"""

from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "SHARH_ARABIC.md"
HTML = ROOT / "SHARH_ARABIC.html"
PDF = ROOT / "SHARH_ARABIC.pdf"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@400;600;700&family=Inter:wght@400;600;700&family=Fira+Code:wght@400;500&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

/* RULE 1 - the page itself is Arabic, so it is RTL. */
body {
  direction: rtl;
  text-align: right;
  font-family: 'Noto Sans Arabic', 'Segoe UI', Tahoma, sans-serif;
  font-size: 12pt;
  line-height: 2.0;
  color: #1a1a2e;
  background: #fff;
  padding: 32px 44px;
  max-width: 980px;
  margin: 0 auto;
}

/* RULE 2 - headings are "English - Arabic"; plaintext keeps that authored order. */
h1, h2, h3, h4 {
  unicode-bidi: plaintext;
  font-family: 'Inter', 'Noto Sans Arabic', sans-serif;
  line-height: 1.5;
}

h1 {
  font-size: 21pt; font-weight: 700; color: #0f0f23;
  border-bottom: 3px solid #D55E00; padding-bottom: 10px; margin-bottom: 6px;
}
h2 {
  font-size: 15.5pt; font-weight: 700; color: #0072B2;
  margin-top: 26px; margin-bottom: 10px;
  border-bottom: 2px solid #e8eef4; padding-bottom: 6px;
}
h3 { font-size: 12.5pt; font-weight: 700; color: #2c3e50; margin-top: 18px; margin-bottom: 7px; }
h4 { font-size: 11.5pt; font-weight: 600; color: #444; margin-top: 14px; }

p { margin-bottom: 11px; }
strong { font-weight: 700; color: #0f0f23; }
hr { border: none; border-top: 1px solid #dde3e8; margin: 22px 0; }

/* RULE 3 - THE important one. An English identifier inside an Arabic sentence must be
   its own LTR island, or it drags the punctuation around it to the wrong side. */
code {
  direction: ltr;
  unicode-bidi: embed;
  font-family: 'Fira Code', Consolas, monospace;
  font-size: 10pt;
  background: #f2f5f8;
  padding: 1px 5px;
  border-radius: 3px;
  color: #b3402a;
  white-space: nowrap;
}

/* RULE 4 - code blocks and formulae are read left-to-right. */
pre {
  direction: ltr;
  text-align: left;
  background: #1e1e2e; color: #cdd6f4;
  border-radius: 8px; padding: 13px 17px;
  font-family: 'Fira Code', Consolas, monospace;
  font-size: 9.5pt; line-height: 1.5;
  overflow-x: auto; margin: 12px 0;
  page-break-inside: avoid;
}
pre code { background: none; padding: 0; color: inherit; white-space: pre; }

/* Tables: RTL layout, but each cell picks its own direction so numeric and English
   columns stay readable. */
table {
  direction: rtl;
  width: 100%; border-collapse: collapse;
  margin: 14px 0; font-size: 10.5pt;
  page-break-inside: avoid;
}
th {
  background: #0072B2; color: #fff; font-weight: 600;
  padding: 8px 12px; text-align: right; border: 1px solid #005a8d;
  unicode-bidi: plaintext;
}
td {
  padding: 7px 12px; border: 1px solid #dde3e8;
  text-align: right;
  unicode-bidi: plaintext;   /* a cell that is purely a number or English reads LTR */
}
tr:nth-child(even) { background: #f7fafc; }

blockquote {
  border-right: 4px solid #D55E00; border-left: none;
  background: #fff8f3;
  padding: 10px 16px; margin: 13px 0;
  border-radius: 6px 0 0 6px;
  font-size: 11pt;
}

/* Lists indent from the right in an RTL page. */
ul, ol { padding-right: 26px; padding-left: 0; margin-bottom: 11px; }
li { margin-bottom: 5px; }

a { color: #0072B2; }

/* The LTR islands created for each Latin run. inline-block would break
   line wrapping, so they stay plain inline. */
span[dir="ltr"] { unicode-bidi: isolate; }

/* Figures: full width, centred, with the Arabic caption beneath. */
img { max-width: 100%; height: auto; display: block; margin: 6px auto 2px; }
figure { margin: 18px 0; page-break-inside: avoid; }
figcaption {
  font-size: 9.5pt; color: #555; text-align: center;
  margin-top: 4px; line-height: 1.6;
}

/* A formula is read left-to-right even on an RTL page. */
.math { direction: ltr; unicode-bidi: isolate; }
mjx-container { direction: ltr; }
mjx-container[display="true"] { margin: 14px 0 !important; }

@media print {
  body { padding: 0; font-size: 10.5pt; line-height: 1.85; }
  h1 { font-size: 18pt; } h2 { font-size: 13.5pt; } h3 { font-size: 11.5pt; }
  pre { font-size: 8.5pt; }
  table { font-size: 9pt; }
  h2 { page-break-after: avoid; }
}
@page { size: A4; margin: 1.4cm 1.6cm; }
"""


# A run of Latin script together with the punctuation that belongs INSIDE it. Setting the
# page direction to RTL is not enough on its own: a neutral character (?, :, ., parentheses)
# sitting at the edge of an English run takes the direction of the PARAGRAPH, not of the run,
# so "Foundation or Formula?" renders as "?Foundation or Formula". Wrapping each Latin run in
# an explicit LTR span pins its punctuation to it.
# A token must CONTAIN a Latin letter but may START with digits -- otherwise "16k" is split,
# the "k" alone becomes the LTR island, and the stranded "16" is placed by the RTL rules,
# rendering as "k16". Pure numbers are left alone; they need no island.
# The run must OPEN with a token containing a letter, but a CONTINUATION token may be pure
# digits -- otherwise "TimesFM-3" ends at "TimesFM", the trailing "-3" is left outside the
# island, and the RTL context moves it in front: "3-TimesFM". That term appears on almost
# every page, so this case matters more than any other.
_TOKEN = r"[A-Za-z0-9]*[A-Za-z][A-Za-z0-9]*"
_NEXT = r"[A-Za-z0-9]+"
# The inner separators MUST include the EN DASH (–). Compound author names are written
# with it -- Diebold-Mariano, Harvey-Leybourne-Newbold, Syntetos-Boylan, Hodges-Lehmann -- and
# with only the ASCII hyphen in this class each name splits into two islands that the RTL
# context then swaps, rendering "Diebold-Mariano" as "Mariano-Diebold".
# The EM DASH (—) is deliberately EXCLUDED: it separates the English and Arabic halves of
# every heading, and swallowing it would make the whole heading one LTR run.
_SEP = r"[ \-–_./&'+,:()]"
LATIN_RUN = re.compile(
    rf"{_TOKEN}(?:{_SEP}{{1,2}}{_NEXT})*[?!.,:;%]?"
)
TAG_SPLIT = re.compile(r"(<[^>]+>)")


def wrap_latin_runs(html: str) -> tuple[str, int]:
    """Wrap Latin-script runs in <span dir="ltr"> inside text nodes only.

    Splits on tags so attribute values and tag names are never touched, and skips the
    contents of <pre>/<code>, which are already LTR by CSS.
    """
    out, n = [], 0
    skip_depth = 0
    for part in TAG_SPLIT.split(html):
        if part.startswith("<"):
            tag = part.lower()
            if tag.startswith(("<pre", "<code")):
                skip_depth += 1
            elif tag.startswith(("</pre", "</code")) and skip_depth:
                skip_depth -= 1
            out.append(part)
            continue
        if skip_depth or not part.strip():
            out.append(part)
            continue

        def repl(m: re.Match) -> str:
            nonlocal n
            n += 1
            return f'<span dir="ltr">{m.group(0)}</span>'

        out.append(LATIN_RUN.sub(repl, part))
    return "".join(out), n


MATH_BLOCK = re.compile(r"\$\$(.+?)\$\$", re.S)
MATH_INLINE = re.compile(r"(?<!\$)\$([^$\n]+?)\$(?!\$)")


def protect_math(md_text: str) -> tuple[str, list[str]]:
    """Pull math out before Markdown runs, leaving inert placeholders.

    Markdown would otherwise mangle it: underscores become emphasis, backslashes are
    escaped, and `*` inside a formula starts a bullet list. Placeholders contain no
    Markdown-significant characters, so they survive untouched.
    """
    store: list[str] = []

    def keep(m: re.Match, display: bool) -> str:
        store.append(("$$" + m.group(1) + "$$") if display
                     else ("$" + m.group(1) + "$"))
        # The placeholder must contain NO Latin letter, or wrap_latin_runs() will wrap it
        # in an LTR span before the math is restored.
        return f"⟦{len(store) - 1}⟧"

    md_text = MATH_BLOCK.sub(lambda m: keep(m, True), md_text)
    md_text = MATH_INLINE.sub(lambda m: keep(m, False), md_text)
    return md_text, store


def restore_math(html: str, store: list[str]) -> str:
    for i, tex in enumerate(store):
        # dir="ltr" because a formula is read left-to-right even on an RTL page.
        html = html.replace(f"⟦{i}⟧",
                            f'<span class="math" dir="ltr">{tex}</span>')
    return html


IMG_RE = re.compile(r'<img alt="([^"]*)" src="([^"]+)"\s*/?>')


def embed_figures(html: str) -> tuple[str, int]:
    """Replace <img src="...pdf"> with an embedded PNG rendered from that PDF.

    The paper's figures are vector PDFs, which a browser will not display inline. They are
    rasterised at 200 dpi and inlined as data URIs so the HTML stays self-contained -- no
    external files to lose when the document is shared.
    """
    import base64

    import fitz

    n = 0

    def repl(m: re.Match) -> str:
        nonlocal n
        alt, src = m.group(1), m.group(2)
        path = (ROOT / src).resolve()
        if not path.is_file():
            print(f"  ! figure not found: {src}")
            return m.group(0)
        if path.suffix.lower() == ".pdf":
            page = fitz.open(path)[0]
            data = page.get_pixmap(dpi=200).tobytes("png")
        else:
            data = path.read_bytes()
        n += 1
        b64 = base64.b64encode(data).decode()
        return (f'<img alt="{alt}" src="data:image/png;base64,{b64}" />')

    return IMG_RE.sub(repl, html), n


def build_html() -> Path:
    md_text = SRC.read_text(encoding="utf-8")
    md_text, math_store = protect_math(md_text)
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "codehilite", "md_in_html", "attr_list"],
        extension_configs={"codehilite": {"css_class": "highlight", "guess_lang": False}},
    )
    body, n_wrapped = wrap_latin_runs(body)
    body = restore_math(body, math_store)
    body, n_fig = embed_figures(body)
    print(f"wrapped {n_wrapped:,} Latin runs | {len(math_store)} math spans | "
          f"{n_fig} figures embedded")
    # `lang` and `dir` on <html> make the whole document Arabic to the renderer, which is
    # what fixes list bullets, scrollbar side and default alignment.
    doc = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>شرح الورقة بالمصري — TimesFM-3 vs Classical</title>
<style>{CSS}</style>
<script>
window.MathJax = {{
  tex: {{ inlineMath: [['$', '$']], displayMath: [['$$', '$$']] }},
  options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }},
  startup: {{ pageReady: () => MathJax.startup.defaultPageReady()
                 .then(() => {{ window.__mathjaxDone = true; }}) }}
}};
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
{body}
</body>
</html>"""
    HTML.write_text(doc, encoding="utf-8")
    print(f"HTML: {HTML.name} ({HTML.stat().st_size:,} bytes)")
    return HTML


async def build_pdf() -> Path:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("file:///" + str(HTML.resolve()).replace(os.sep, "/"),
                        wait_until="networkidle")
        await page.wait_for_timeout(2500)  # let the Arabic web font actually arrive
        try:
            # Print only once MathJax has finished typesetting, otherwise the PDF can
            # capture the raw TeX source mid-render.
            await page.wait_for_function("window.__mathjaxDone === true", timeout=25000)
            print("  MathJax finished typesetting")
        except Exception:
            print("  ! MathJax did not report completion; check the formulae in the PDF")
        await page.wait_for_timeout(800)
        await page.pdf(path=str(PDF), format="A4", print_background=True,
                       margin={"top": "1.4cm", "bottom": "1.4cm",
                               "left": "1.6cm", "right": "1.6cm"})
        await browser.close()
    print(f"PDF : {PDF.name} ({PDF.stat().st_size:,} bytes)")
    return PDF


if __name__ == "__main__":
    build_html()
    asyncio.run(build_pdf())
    print("\nboth written next to SHARH_ARABIC.md")
