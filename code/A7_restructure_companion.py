"""Rebuild SHARH_ARABIC.md in the order of the restructured manuscript (K11), 2026-09-24.

Existing explanations are moved as blocks (not rewritten); new text is written only where the paper gained
a part (contributions, hypotheses stated before the results, summary of findings, hedged practical
considerations) or where the old text had become wrong (decision table, hypothesis verdicts, limitations,
final summary). Afterwards the author's terminology: "cell"/خلية -> "scenario"/سيناريو.

Paper -> companion:
  1 Introduction + contributions   -> 1 (old 2, old 3, new 1.3)
  2 TimesFM-3                      -> 2 (old 1)
  3 Design + hypotheses            -> 3 (old 4, 5, 6, 7, new 3.6)
  4 Pre-registered comparison      -> 4 (old 8.1, 8.2 + forest, 8.9, 8.3, 8.5, 8.7 + interval score, 4.7 verdicts)
  5 Post-hoc analyses              -> 5 (review items, 8.8, 8.6, old 9 robustness, horizon, 9.9)
  6 M4                             -> 6 (old 10, 9.2, M4 official, truncation)
  7 Discussion                     -> 7 (findings, old 8.4, practical + old 11, threats)
  8 Conclusion / 9 Reproducibility -> 8 (old 16), 9 (old 15)
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "SHARH_ARABIC.md"


def load():
    return SRC.read_text(encoding="utf-8")


def h2(s, num):
    """Whole old '## num.' section, heading included, up to the next '## '."""
    m = re.search(rf"^## {num}\. .*$", s, re.M)
    a = m.start()
    n = re.search(r"^## ", s[m.end():], re.M)
    b = m.end() + n.start() if n else len(s)
    return s[a:b]


def body(sec):
    """Section without its heading line."""
    return sec.split("\n", 1)[1]


def intro(sec):
    """Text between the ## heading and its first ### heading."""
    b = body(sec)
    m = re.search(r"^### ", b, re.M)
    return b[:m.start()] if m else b


def h3(s, num):
    """Old '### num ' block without its heading, up to the next ### or ##."""
    m = re.search(rf"^### {re.escape(num)} .*$", s, re.M)
    rest = s[m.end():]
    n = re.search(r"^#{2,3} ", rest, re.M)
    return rest[:n.start()] if n else rest


def h3_named(s, title_start):
    m = re.search(rf"^### {re.escape(title_start)}.*$", s, re.M)
    rest = s[m.end():]
    n = re.search(r"^#{2,3} ", rest, re.M)
    return m.group(0), (rest[:n.start()] if n else rest)


def items98(s):
    """Split old 9.8 into its numbered items {1: text, ...}."""
    blk = h3(s, "9.8")
    parts = re.split(r"(?m)^(?=\*\*\d+\) )", blk)
    out = {}
    for p in parts:
        m = re.match(r"\*\*(\d+)\) ", p)
        if m:
            txt = p
            txt = re.split(r"(?m)^\*\*من الآخر للمراجعة:\*\*", txt)[0]
            out[int(m.group(1))] = txt.rstrip() + "\n\n"
    return out


def demote(text):
    """### -> #### inside a moved block."""
    return re.sub(r"(?m)^### ", "#### ", text)


def strip_rule(t):
    return re.sub(r"\n---\s*$", "\n", t.rstrip()) + "\n\n"


CONTRIB = """### 1.3 The Four Contributions — إيه الجديد في الورقة دي بالظبط؟

الورقة مش بتخترع طريقة جديدة — بس فيها **أربع حاجات جديدة** على الأدبيات:

1. **تقييم نضيف من التلوث بالبناء:** البيانات اتولّدت بعد الموديل، فمستحيل يكون شافها، وكل ده تحت
   **بروتوكول متجمّد قبل أي تنبؤ**، وكل انحراف عنه متسجّل.
2. **أسوأ حالة، مش المتوسط بس:** الـ benchmarks بتقارن **متوسطات**؛ إحنا بصّينا كمان على **أسوأ
   سيناريو** لكل طريقة — ولقينا إن الحد ده **خاص بـ `TimesFM-3`** من بين خمس موديلات أساس، و**في الأفق
   القصير بس** (لحد حوالي سنتين من الخطوات الشهرية).
3. **التخصيص الصحيح ≠ القابلية للتقدير:** أكبر إخفاقات `AutoARIMA` و`AutoETS` بتحصل لما **دورتين
   موسميتين مايكفوش** لتقدير شكل موسمي — مش لما الموديل غلط.
4. **مقارنة بأبطال M4 الحقيقيين ومعايير بسيطة:** حطّينا الموديلات الأساس قدام **التنبؤات المنشورة**
   لأحسن مشاركات مسابقة M4، وقدام معايير بسيطة من التاريخ نفسه في الطلب المتقطع — وسجّلنا كمان
   قيود **الرخصة والتكلفة**.

**من الآخر:** الجديد مش "مين كسب"، الجديد إننا عرفنا **إمتى ولحد فين** كل طرف بيصمد، في ظروف نضيفة.

"""

HYPOTHESES_STATED = """### 3.6 The Pre-registered Hypotheses — الفرضيات المسجّلة مسبقاً

قبل أي تنبؤ، في **8 سبتمبر 2026**، اتكتب البروتوكول واتجمّد، وفيه **5 فرضيات** (زي ما هي بالظبط):

- **`H1`:** في `D1`–`D5` (الكلاسيكي صح بالبناء)، `AutoARIMA`/`AutoETS` أدق من `TimesFM-3`، والفرق **أكبر
  عند `n = 24`**.
- **`H2`:** في `D6`–`D8` (مفيش شكل كلاسيكي صح)، `TimesFM-3` أدق من **كل** الطرق الكلاسيكية.
- **`H3`:** في `D9` العيلتين **متعادلين في المتوسط**، بس فترات الكلاسيكي **بتقصّر في التغطية**.
- **`H4`:** الدمج أحسن من كل طريقة كلاسيكية لوحدها، وهو **أصعب خصم** لـ `TimesFM-3`.
- **`H5`:** فترات الـ 80% في العيلتين **بتقصّر**، و`TimesFM-3` أكتر في الآفاق الأطول.

البروتوكول **ماحددش قواعد قرار** رقمية — فالأحكام في آخر القسم 4 هي **حكم على نمط الاختبارات**. وكل حاجة
في القسم 5 (التحليلات البعدية) اتضافت **بعد** ما النتايج ظهرت، ومتسجّلة كانحرافات.

"""

VERDICTS = """### 4.7 The Hypotheses, Judged — حكم الفرضيات

| # | المتوقَّع | الحكم | الدليل |
|---|---|---|---|
| `H1` | الكلاسيكي الصح يكسب في `D1`–`D5`، أكتر عند n صغير | ❌ **مش مدعومة** | عند `n = 24` الفرق بيروح **بالعكس**؛ الكلاسيكي بيكسب بس لما الموديل كمان **قابل للتقدير** (`D4` و`D5` من `n = 48`) |
| `H2` | `TimesFM-3` يكسب في `D6`–`D8` | ⚠️ **جزئياً** | شوية في الكسر الهيكلي؛ في اللوجستي حسب الطول؛ في المتقطع قدام الكلاسيكي بس، مش قدام معايير التاريخ |
| `H3` | `D9`: تعادل في المتوسط والكلاسيكي يقصّر | ⚠️ **جزئياً** | التعادل صح، بس `AutoARIMA` لوحده اللي بيقصّر |
| `H4` | الدمج يكسب الكل وهو أصعب خصم | ❌ **متناقضة في الشقين** | `AutoARIMA` أدق منه، وهو الخصم الأصعب (11–9 مقابل 27–3) |
| `H5` | الطرفين يقصّروا، و`TimesFM-3` أكتر مع الأفق | ❌ **مش مدعومة** | `TimesFM-3` قريب من المطلوب في المتوسط ومابيسوءش جوّه الـ 12 خطوة؛ الكلاسيكي **بيزوّد** من `n = 96` |

**النقطة المهمة:** إن **ولا فرضية** نجت سليمة هو **أقوى حجة** للتسجيل المسبق — لو الفرضيات اتكتبت **بعد**
النتايج، الجدول ده كان هيبلّغ 5 تأكيدات.

"""

POSTHOC_INTRO = """## 5. Post-hoc Analyses — التحليلات البعدية

كل اللي في القسم ده اتصمّم **بعد** ما نتايج القسم 4 ظهرت — أغلبه رداً على أسئلة المحكّمين — ومتسجّل
كانحراف عن البروتوكول. بنفصله عن القسم 4 عشان القارئ يعرف دايماً: ده **مسجّل مسبقاً** ولا **بعدي**.

"""

SCATTER = """**الصورة الكاملة في رسمة واحدة:**

![المتانة مقابل الدقة](figures/fig6_robustness_scatter.pdf)

**إزاي تقراها؟** كل نقطة طريقة من الخمستاشر. المحور الأفقي = **الأداء المعتاد** (قد إيه بعيد عن الأحسن
في المتوسط)، والرأسي = **أسوأ سيناريو**. **تحت وشمال = أحسن في الاتنين.** `TimesFM-3` (بالإعدادين) قاعد
**لوحده** في الركن ده؛ الموديلات الأساس التانية متجمّعة مع `AutoARIMA` عند حوالي 2.2.

"""

FINDINGS = """### 7.1 Summary of Findings — ملخص النتايج في جدول

| النتيجة | فين في الورقة | مسجّلة مسبقاً؟ | صحيحة في حدود |
|---|---|---|---|
| مفيش عيلة كسبت؛ `AutoARIMA` الوحيد اللي `TimesFM-3` مابيغلبوش بوضوح | 4.1، رسم الغابة | ✅ مسجّلة | 9 عمليات، أفق 12 |
| أسوأ نسبة لـ `TimesFM-3` = 1.31، وكل كلاسيكي ≥ 2.2 | جدول 3، 5.1 | ملخص بعدي | أفق 12؛ نسبي للطرق المقارَنة |
| أكبر إخفاقات الكلاسيكي من موسمية مش قابلة للتقدير بدورتين | 4.3، 5.2 | مسجّلة، واتفحصت بعدياً | `m = 12`، `n = 24`؛ اتكررت في R |
| مع ≥ 4 دورات `AutoARIMA` أدق بـ 21–24% | 4.4 | ✅ مسجّلة | `D4`، `D5` |
| المتانة خاصة بـ `TimesFM-3` من بين 5 موديلات أساس | 5.3، شكل 5 | بعدي | أفق 12 |
| في الطلب المتقطع مفيش ميزة قدام معايير التاريخ | 5.4 | بعدي | عملية مستقلة عبر الزمن |
| عند 48 خطوة `AutoARIMA` أمتن، وكل الموديلات الأساس بتتوقع نزول لسلسلة ثابتة | 5.6 | بعدي | التصميم المعاد توليده |
| على M4: قد المراكز 5–7، ورا أحسن أربعة | 6.3 | بعدي | 1,000 سلسلة شهرية طويلة |

(الأرقام في العمود التاني هي أقسام **الورقة** نفسها.)

"""

PRACTICAL = """### 7.3 Practical Considerations — اعتبارات عملية (مش قواعد)

الورقة **شالت جدول القرار** القديم وحطّت مكانه فقرات حذرة — لأن جدول "استخدم كذا" بيدّي ثقة أكبر من اللي
دراسة محاكاة استكشافية تقدر تدّيها. فخد دول **كنقط بداية تفحصها على بياناتك**، مش كقوانين:

- **آلاف السلاسل من غير وقت تظبط كل واحدة:** هنا متانة `TimesFM-3` فرقت أكتر — عمره ما بعد كتير عن الأحسن.
  بس لو قدامك **سلسلة واحدة** تقدر تحدد موديلها، الكلاسيكي مابيخسرش كتير قدام `AutoARIMA`، وبيدّيك
  معاملات وتشخيص تقدر **تشرحها وتراجعها**.
- **سلاسل موسمية:** مع **4 دورات أو أكتر** `AutoARIMA` كان في المقدمة بوضوح (و`SeasonalNaive` كمان
  قدام `TimesFM-3` في `D4`). مع **دورتين** الكلاسيكي الأوتوماتيكي رجع لموديلات مش موسمية ووقع —
  و`SeasonalNaive` أو `TimesFM-3` كانوا الأأمن.
- **طلب متقطع:** المعايير البسيطة من التاريخ **كانت قد أي حاجة جرّبناها** — عُشيرات التاريخ أقل pinball،
  ومتوسطه (زي عيلة Croston) أقل RMSSE. والتنبؤ الوسيط لـ `TimesFM-3` مكانش أحسن من تنبؤ **صفر**.
- **آفاق طويلة:** بعد حوالي **سنتين** من الخطوات الشهرية `AutoARIMA` بقى الأمتن، وكل الموديلات الأساس
  توقّعت نزول لسلسلة ثابتة — فراجع تنبؤاتها الطويلة قدام **المستوى الأخير** قبل ما تستخدمها.

"""

THREATS = """### 7.4 Threats to Validity — حدود الدراسة (بصراحة)

الورقة قسّمتها لتلات أنواع:

- **حدود "المقياس" (construct):** الملخصات اللي شايلة نتيجة المتانة — **أسوأ نسبة** و**عدد السيناريوهات
  المكسوبة** — اتعرّفت **بعد** البروتوكول، وبتعتمد على الطرق المقارَنة (خصوصاً `SeasonalNaive` اللي عارف
  الفترة)؛ وفي `D8` الحكم بيتقلب حسب مقياس الخطأ.
- **حدود "داخلية" (internal):** مفيش تظبيط يدوي لأي طريقة، والكلاسيكي اتشغّل بمكتبة واحدة بإعداداتها
  الافتراضية — مراجعة R كرّرت الإخفاقات بس لقت **خطأ تنفيذ واحد**؛ والبروتوكول متجمّد بس محفوظ في
  الأرشيف مش في سجل خارجي؛ وكل القسم 5 بعدي.
- **حدود "خارجية" (external):** السلاسل المولّدة نضيفة ومافيهاش خطأ قياس ولا مواسم تقويمية ولا تغيّرات
  نظام؛ حوالي **ربع** سلاسل M4 الشهرية وكل الترددات التانية برّا التغطية؛ 9 عائلات ثابتة بفترة 12؛ الأفق
  المسجّل 12 خطوة والأطول اتفحص مرة واحدة؛ والانحرافات اتجرّبت واحدة واحدة. `TimesFM-3` اتقيّم zero-shot
  وأحادي المتغير بس، و**خمس** موديلات أساس بس اتقيّمت وبيتصرفوا **مختلف** — فمفيش تعميم على الفئة.

**وفوق ده كله:** دي **دراسة استكشافية عن صندوق أسود** — بتقيس **إيه** اللي الموديل بيعمله، مش **ليه**.

"""

SUMMARY = """## 8. الخلاصة الكبيرة — لو هتفتكر 5 حاجات بس

1. **مفيش عيلة كسبت.** `TimesFM-3` كسب أغلب المقارنات المعنوية — **ما عدا** قدام `AutoARIMA` (11–9) —
   ومع 4 دورات موسمية أو أكتر `AutoARIMA` أدق بوضوح.
2. **اللي بيميّز `TimesFM-3` هو أسوأ حالة ليه:** عمره ما بقى أسوأ من **1.31×** من الأحسن، وكل كلاسيكي
   ≥ **2.2×** في سيناريو ما — ومن بين **خمس** موديلات أساس هو الوحيد اللي كده.
3. **بس الميزة دي ليها حدود:** نسبية للطرق المقارَنة، صحيحة **لحد حوالي سنتين** من الخطوات الشهرية (بعدها
   `AutoARIMA` أمتن وكل الموديلات الأساس بتتوقع نزول لسلسلة ثابتة)، وفي الطلب المتقطع **معايير التاريخ
   البسيطة** قدها.
4. **على M4 الحقيقية:** `TimesFM-3` قد أصحاب المراكز من **5 لـ 7** في المسابقة، ورا **أحسن أربعة**.
5. **الدرس الأعمق عن الكلاسيكي:** المهم مش بس إن الموديل **صح**، المهم إنه **يتقدّر** من البيانات اللي
   قدامك — بدورتين `AutoETS` خسر **2.7 مرة** قدام قاعدة من سطر واحد، على بيانات هو اللي ولّدها. و**الرخصة**
   غير التجارية ممكن تحسم الموضوع لفئة كاملة **قبل** أي كلام عن دقة.

**من الآخر خالص:** مش "الجديد أحسن من القديم" ولا العكس — الجديد **أثبت في الأفق القصير**، والقديم **أدق
لما يقدر يتقدّر**، والرخصة ممكن تحسم الموضوع قبل الاتنين.

---

*الملف ده شرح مصاحب للورقة. الأرقام كلها متطابقة مع ملفات النتايج في `results/`.*
"""

AR_TERMS = [
    ("خلية واحدة", "سيناريو واحد"), ("وخلية واحدة كارثية", "وسيناريو واحد كارثي"), ("وخلية تانية", "وسيناريو تاني"),
    ("الخلية الوسيطة", "السيناريو الوسيط"), ("خلايا معينة", "سيناريوهات معينة"),
]


def arabic_scenario(t):
    for a, b in sorted(AR_TERMS, key=lambda x: -len(x[0])):
        t = t.replace(a, b)
    # prefixes و/ب/ل + ال, then the bare nouns; word-initial only (spares داخلية, خليني, يخليها)
    t = re.sub("(?<![ء-ي])(و?(?:بال|لل|ال)?)خلايا(?![ء-ي])", lambda m: m.group(1) + "سيناريوهات", t)
    t = re.sub("(?<![ء-ي])(و?(?:بال|لل|ال)?)خلية(?![ء-ي])", lambda m: m.group(1) + "سيناريو", t)
    for a, b in [("سيناريو لوحدها", "سيناريو لوحده"), ("سيناريو بيوعد فيها", "سيناريو بيوعد فيه"),
                 ("وسيناريو تاني\nبيوفي فيها", "وسيناريو تاني\nبيوفي فيه")]:
        t = t.replace(a, b)
    # English "cell" inside the companion
    t = re.sub(r"\bcell-best\b", "scenario-best", t)
    t = re.sub(r"\bcells\b", "scenarios", t)
    t = re.sub(r"\bcell\b", "scenario", t)
    return t


def main():
    s = load()
    pre = s[:s.index("## 0. ")]
    it = items98(s)

    out = [pre, strip_rule(h2(s, 0))]
    # 1 Introduction
    out.append("## 1. Introduction — المقدمة: ليه الدراسة دي وإيه الجديد فيها\n\n")
    out.append("### 1.1 Why the Published Evidence Is Not Enough — ليه الأدلة المنشورة مش كفاية؟\n"
               + demote(strip_rule(body(h2(s, 2)))))
    out.append("### 1.2 The Idea That Closes Both Objections — الفكرة اللي بتقفل الاعتراضين مع بعض\n"
               + demote(strip_rule(body(h2(s, 3)))))
    out.append(CONTRIB)
    # 2 TimesFM-3
    out.append("## 2. What Is TimesFM-3? — إيه هو الـ TimesFM-3 أصلاً؟\n" + strip_rule(body(h2(s, 1))))
    # 3 Design
    d = h2(s, 4)
    out.append("## 3. Design of the Simulation — تصميم دراسة المحاكاة\n" + intro(d))
    out.append("### 3.1 The Nine DGPs — التسع عمليات المولّدة للبيانات\n" + h3(s, "4.1"))
    out.append("### 3.2 Lengths, Replications, Horizon — الأطوال والتكرارات والأفق\n" + strip_rule(h3(s, "4.2")))
    out.append("### 3.3 The Methods Compared — الطرق اللي اتقارنت\n" + demote(strip_rule(body(h2(s, 5)))))
    out.append("### 3.4 The Metrics — المقاييس، وإزاي بنقيس \"الغلط\"\n" + demote(strip_rule(body(h2(s, 6)))))
    out.append("### 3.5 The Statistical Tests — الاختبارات الإحصائية\n" + demote(strip_rule(body(h2(s, 7)))))
    out.append(HYPOTHESES_STATED)
    # 4 Pre-registered comparison
    r = h2(s, 8)
    out.append("## 4. The Pre-registered Comparison — المقارنة المسجّلة مسبقاً\n" + intro(r))
    out.append("### 4.1 A Split Decision, Not a Rout — قرار منقسم مش كاسح\n" + h3(s, "8.1"))
    out.append("### 4.2 Who Actually Holds Their Ground — مين بيصمد قدامه فعلاً؟\n" + h3(s, "8.2")
               + it[11].replace("**11) رسم الغابة (forest plot):**", "**رسم الغابة (forest plot):**"))
    out.append("### 4.3 Effect Sizes and a Sensitivity Check — أحجام الأثر وفحص الحساسية\n" + h3(s, "8.9"))
    out.append("### 4.4 ⭐ Specification Is Not Estimability — التخصيص الصحيح مش زي القابلية للتقدير\n" + h3(s, "8.3"))
    out.append("### 4.5 Two Decisive Regimes — النظامين اللي فيهم قرار واضح\n" + h3(s, "8.5"))
    out.append("### 4.6 Interval Reliability — ثبات الفترات: هل الـ 80% فعلاً 80%؟\n" + h3(s, "8.7")
               + it[6].replace("**6) درجة الفترات (interval score):**", "**درجة الفترات (interval score) — تحليل بعدي:**"))
    out.append(VERDICTS)
    # 5 Post hoc
    out.append(POSTHOC_INTRO)
    out.append("### 5.1 Precision of the Numbers — دقة الأرقام نفسها\n\n" + it[1].replace("**1) ", "**"))
    out.append("### 5.2 Implementation and Configuration Checks — فحص التنفيذ والإعدادات\n\n"
               + it[4].replace("**4) ", "**") + it[10].replace("**10) ", "**")
               + "#### Was the Combination a Straw Man? — هل الـ Combination كان خصم ضعيف؟\n" + h3(s, "8.8"))
    out.append("### 5.3 Stronger Benchmarks and Other Foundation Models — طرق أقوى وموديلات أساس تانية\n\n"
               + it[2].replace("**2) ", "**") + it[3].replace("**3) ", "**") + it[9].replace("**9) ", "**")
               + SCATTER)
    out.append("### 5.4 Intermittent Demand Re-examined — الطلب المتقطع من تاني\n" + h3(s, "8.6")
               + it[5].replace("**5) ", "**"))
    rob = h2(s, 9)
    out.append("### 5.5 Randomised Parameters and Departures — قيم عشوائية وبيانات مش مثالية\n" + intro(rob))
    for num, title in [("9.1", "Why Fixed Values Are a Risk — ليه القيم الثابتة مخاطرة؟"),
                       ("9.3", "Randomised Parameters — كل سلسلة بقيمها الخاصة"),
                       ("9.4", "Four Departures from the Assumptions — أربع نسخ: لما البيانات مابتبقاش مثالية"),
                       ("9.5", "The Verdict — النتيجة: إيه اللي صمد وإيه اللي لأ؟"),
                       ("9.6", "⭐ The Two-Cycle Collapse, Corrected — انهيار الدورتين: الصورة الصح"),
                       ("9.7", "How the Answer Moves with the Parameters — النتيجة بتتغيّر إزاي مع القيم؟")]:
        out.append(f"#### {title}\n" + h3(s, num))
    out.append("### 5.6 ⭐⭐ A Longer Horizon — أفق أطول: 48 خطوة بدل 12\n\n" + it[12].replace("**12) ⭐⭐ أفق أطول — 48 خطوة بدل 12:** ", ""))
    out.append("### 5.7 What the Post-hoc Analyses Do NOT Prove — اللي التحليلات دي **مابتثبتوش**\n" + strip_rule(h3(s, "9.9")))
    # 6 M4
    m = h2(s, 10)
    out.append("## 6. The Real-Data Tier: M4 Monthly — البيانات الحقيقية\n" + intro(m))
    out.append("### 6.1 Representativeness: the Instance Space — فضاء الخصائص: هل سلاسلنا شبه الحقيقية؟\n" + h3(s, "9.2"))
    out.append("### 6.2 What Is M4 Anyway? — إيه هي بيانات M4 أصلاً؟\n" + h3(s, "10.1"))
    out.append("### 6.3 How We Picked the Series — إزاي اخترنا السلاسل بالظبط\n" + h3(s, "10.2"))
    out.append("### 6.4 ⭐ What Is an \"Origin\" and a \"Window\"? — يعني إيه \"origin\" و\"window\"؟\n" + h3(s, "10.3"))
    tail = body(m)[body(m).index("### 10.4"):]
    tail = strip_rule(tail).replace("### 10.4 ", "### 6.5 ", 1)
    out.append(demote_named(tail))
    out.append("### 6.6 ⭐ The Official M4 Test Period — فترة الاختبار الرسمية وأبطال المسابقة\n\n"
               + it[7].replace("**7) ⭐ اختبار M4 الرسمي — وقدام أبطال المسابقة نفسهم:** ", ""))
    out.append("### 6.7 ⭐ Truncated Histories — تجربة القصّ\n\n"
               + it[8].replace("**8) ⭐ تجربة القصّ (truncation) — نفس درس المحاكاة على بيانات حقيقية:** ", ""))
    # 7 Discussion
    out.append("## 7. Discussion — المناقشة\n\n" + FINDINGS)
    out.append("### 7.2 Robustness, Not Peak Accuracy — الموديل بيشتري **المتانة** مش الدقة القصوى\n" + h3(s, "8.4"))
    out.append(PRACTICAL)
    costs = body(h2(s, 11))
    costs = costs.replace("تقليل 26% في الخطأ على الطلب المتقطع **ملهوش أي معنى** لتاجر تجزئة **مش مسموح له قانونياً** ينشر الموديل ده.",
                          "أي ميزة في الدقة **ملهاش أي معنى** لتاجر تجزئة **مش مسموح له قانونياً** ينشر الموديل ده.")
    costs = re.sub(r"(?m)^### 11\.\d ", "#### ", costs)
    costs = re.sub(r"(?m)^### ", "#### ", costs)
    out.append(strip_rule(costs))
    out.append(THREATS)
    out.append(SUMMARY + "\n")
    # 9 Reproducibility (placed last, as in the paper)
    rep = h2(s, 15).replace("## 15. ", "## 9. ", 1)
    rep = re.sub(r"(?m)^### 15\.(\d) ", r"### 9.\1 ", rep)
    new = "".join(out).replace("## 8. الخلاصة الكبيرة", "## 8. الخلاصة الكبيرة", 1)
    # conclusion ends with the note; put reproducibility before the closing note
    note = "\n---\n\n*الملف ده شرح مصاحب للورقة."
    i = new.rindex(note)
    new = new[:i] + "\n\n" + strip_rule(rep) + new[i:]

    # cross-references to the companion's own sections
    for a, b in [("القسم 8.3", "القسم 4.4"), ("في 8.5.", "في 4.5."), ("من 8.3:", "من 4.4:"),
                 ("(اللي في 8.5 و8.6)", "(اللي في 4.5 و5.4)"), ("القسم 8.", "القسم 4."),
                 ("في القسم 8 ", "في القسم 4 "), ("نفس بتاعة القسم 10", "نفس بتاعة القسم 6"),
                 ("القسم 14", "القسم 7.4"), ("الملاحظة من القسم 5", "الملاحظة من القسم 3.3"),
                 ("تحليلات مراجعة المحكّمين في القسم 9", "التحليلات البعدية في القسم 5"),
                 ("بالتفصيل في 9.8", "بالتفصيل في 5.4"), ("(شرحناه في 7.2)", "(شرحناه في 3.5)"),
                 ("(من **D-10** لـ **D-12**)", "(من **D-10** لـ **D-14**)"), ("**D-04 لـ D-12:**", "**D-04 لـ D-14:**"),
                 ("آخرهم D-10 لـ D-12: دراسة المتانة، وخط الأساس Oracle ARIMA، و", "آخرهم D-10 لـ D-14: دراسة المتانة، وخط الأساس Oracle ARIMA، ومراجعة R، والأفق الأطول، و")]:
        new = new.replace(a, b)
    new = arabic_scenario(new)
    SRC.write_text(new, encoding="utf-8")
    print("companion restructured:", len(new.splitlines()), "lines")


def demote_named(t):
    """10.4 block keeps its ### heading; its own sub-headings (### النتيجة, ### ملاحظتين) become ####."""
    first, rest = t.split("\n", 1)
    return first + "\n" + re.sub(r"(?m)^### ", "#### ", rest)


if __name__ == "__main__":
    main()
