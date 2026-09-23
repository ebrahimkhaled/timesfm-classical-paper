"""Insert the robustness section (paper Section 5) into SHARH_ARABIC.md as section 9.

The companion's own numbering differs from the paper's: its results are section 8 and M4 is
section 9. The new section goes between them, and sections 9-15 become 10-16. The limitations,
the deviation count and the final summary are brought in line with the paper. Idempotent.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "SHARH_ARABIC.md"
NEW = (ROOT / "code" / "A5_section9_text.md").read_text(encoding="utf-8")

ANCHOR = "## 9. The Real-Data Tier: M4 Monthly"

EDITS = [
    # deviation log now has ten entries
    ("- `DEVIATIONS.md` فيه **9 انحرافات**،", "- `DEVIATIONS.md` فيه **10 انحرافات**،"),
    ("  - **D-04 لـ D-09:** اتعملوا **بعد** وجود نتايج، وكل واحد بيقول كده في مدخله.",
     "  - **D-04 لـ D-10:** اتعملوا **بعد** وجود نتايج، وكل واحد بيقول كده في مدخله (آخرهم D-10: "
     "دراسة المتانة في القسم 9)."),
    # limitations: the fixed-value limitation is now answered; the remaining bounds are stated
    ("6. **دي دراسة عن موديل واحد.** `Chronos` و `Moirai` مش متقيّمين هنا، فمفيش حاجة هنا تتقري كادعاء عن الـ foundation models عموماً.",
     "6. **دي دراسة عن موديل واحد.** `Chronos` و `Moirai` مش متقيّمين هنا، فمفيش حاجة هنا تتقري كادعاء عن الـ foundation models عموماً.\n"
     "7. **العائلات نفسها ثابتة.** القسم 9 خلّى القيم عشوائية وكسر 3 فرضيات، بس لسه 9 عائلات أحادية المتغير بفترة 12. التصميم العشوائي بيغطّي **81%** من سلاسل M4 الشهرية في فضاء خصائص من 4 أبعاد — يعني **خُمس** السلاسل الشهرية الحقيقية، وكل الترددات التانية، برّا المناطق اللي درسناها.\n"
     "8. **دراسة استكشافية عن صندوق أسود.** التصميم بيقيس **إيه** اللي `TimesFM-3` بيعمله تحت ظروف معروفة، مش **ليه**: البارامترات مالهاش تفسير فردي، وبيانات التدريب مش متاحة. أي تفسير لسلوكه في الورقة هو **تفسير متّسق مع الأرقام**، مش نتيجة."),
    # final summary
    ("3. **التخصيص الصحيح ≠ القابلية للتقدير.** بدورتين موسميتين، `AutoETS` خسر بـ **2.7 مرة** قدام قاعدة من سطر واحد — **على بيانات هو اللي ولّدها**. الـ foundation models أنفع بالظبط لما التقدير الكلاسيكي جعان بيانات.",
     "3. **التخصيص الصحيح ≠ القابلية للتقدير.** بدورتين موسميتين، `AutoETS` خسر بـ **2.7 مرة** قدام قاعدة من سطر واحد — **على بيانات هو اللي ولّدها**. ولما الفترة الموسمية بتتقدّر باختبار عادي، الانهيار **بيختفي**. وفي التصميم ده، `TimesFM-3` كان أنفع بالظبط لما التقدير الكلاسيكي جعان بيانات."),
    ("4. **الموديل بيشتري المتانة مش الدقة القصوى.** عمره ما بقى أسوأ من **1.31×** من الأحسن، بينما كل كلاسيكي بيبقى ≥ **2.2×** أسوأ في مكان ما.",
     "4. **الموديل بيشتري المتانة مش الدقة القصوى.** عمره ما بقى أسوأ من **1.31×** من الأحسن، بينما كل كلاسيكي بيبقى ≥ **2.2×** أسوأ في مكان ما — ولما القيم بقت عشوائية والبيانات فيها ذيول تقيلة وقيم شاذة، أسوأ حالاته بقت **1.51×** بس، والكلاسيكي لسه ≥ **1.60×**."),
]


def main() -> None:
    s = DOC.read_text(encoding="utf-8")
    if "## 9. ⭐ Representativeness and Robustness" in s:
        print("section 9 already present")
        return
    assert s.count(ANCHOR) == 1

    # renumber 9..15 -> 10..16 in headings, highest first so nothing is renumbered twice
    for old in range(15, 8, -1):
        s = re.sub(rf"^(#{{2,3}}) {old}(\.| )", lambda m: f"{m.group(1)} {old + 1}{m.group(2)}",
                   s, flags=re.M)
    s = s.replace("## 10. The Real-Data Tier: M4 Monthly",
                  NEW.rstrip("\n") + "\n\n## 10. The Real-Data Tier: M4 Monthly", 1)
    for old, new in EDITS:
        assert s.count(old) == 1, old[:60]
        s = s.replace(old, new)
    DOC.write_text(s, encoding="utf-8")
    print("inserted section 9; renumbered 9-15 to 10-16; limitations, deviations, summary updated")
    print("\n".join(l for l in s.splitlines() if re.match(r"^## \d", l)))


if __name__ == "__main__":
    main()
