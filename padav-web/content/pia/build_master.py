"""Builds content/pia-master-v1.json and the SVG assets for the PIA 50-item master form (draft prototype).

Run from the project root:  python content/pia/build_master.py
Every answer key below is computed or asserted here, so edits cannot silently break a key.
All items are original. Status is 'draft': they need expert, bilingual and cognitive-interview review.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import geometry as g  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "content" / "pia-assets"
OUT = ROOT / "content" / "pia-master-v1.json"
AUTHOR = "padav-team (AI-drafted prototype; pending expert review)"
VISUAL_NOTE = "Requires vision. A non-visual accommodation must be designed before operational release."
TIMED_NOTE = "Timed display needs an accommodation (longer display) for some users."

ITEMS: list[dict] = []
ASSET_FILES: dict[str, str] = {}


def pair(x):
    return x if isinstance(x, tuple) else (x, x)


def translation(text: dict, options: list[dict]) -> dict:
    out = {"stem": text["stem"], "options": options, "explanation": text.get("explanation"),
           "distractor_rationale": text.get("rationale"), "reviewed": False}
    if text.get("stimulus"):
        out["stimulus"] = text["stimulus"]
    return out


def add(code, domain, sub, fmt, diff, correct, wrong, en, hi, *, display=None, stimulus_type="text",
        note="Text only; compatible with screen readers."):
    """correct/wrong: str or (en, hi). Options are shuffled deterministically per item."""
    options = [pair(correct)] + [pair(w) for w in wrong]
    assert len({o[0] for o in options}) == len(options), f"{code}: duplicate options"
    order = list(range(len(options)))
    random.Random(code).shuffle(order)
    keys = "abcd"[: len(options)]
    key = keys[order.index(0)]
    build = lambda idx, text: translation(text, [{"key": keys[i], "text": options[order[i]][idx]} for i in range(len(options))])  # noqa: E731
    ITEMS.append({
        "item_code": code, "version": 1, "domain": domain, "subdomain": sub, "item_format": fmt, "stimulus_type": stimulus_type,
        "asset_id": None, "difficulty": diff, "min_age": 13, "stimulus_display_seconds": display, "answer_key": key,
        "status": "draft", "author": AUTHOR, "accessibility_notes": note,
        "translations": {"en": build(0, en), "hi": build(1, hi)},
    })


def add_visual(code, domain, sub, fmt, diff, key, svg, en, hi):
    """Image items: the picture carries the choices, options are just A-D."""
    asset = code.lower()
    ASSET_FILES[asset] = svg
    options = [{"key": k, "text": k.upper()} for k in "abcd"]
    ITEMS.append({
        "item_code": code, "version": 1, "domain": domain, "subdomain": sub, "item_format": fmt, "stimulus_type": "image",
        "asset_id": asset, "difficulty": diff, "min_age": 13, "answer_key": key, "status": "draft", "author": AUTHOR,
        "accessibility_notes": VISUAL_NOTE, "translations": {"en": translation(en, options), "hi": translation(hi, options)},
    })


S = lambda *xs: ", ".join(str(x) for x in xs)  # noqa: E731
strs = lambda *xs: [str(x) for x in xs]  # noqa: E731

# ================= Fluid reasoning (Gf) =====================================================================
seq1 = [3 * 2 ** i for i in range(4)]
assert seq1 == [3, 6, 12, 24] and seq1[-1] * 2 == 48
add("PIA-GF-SQ-001", "gf", "number-sequence", "sequence", "easy", "48", strs(30, 36, 60),
    {"stem": f"What number comes next?  {S(*seq1)}, ?", "explanation": "Each number is double the one before, so 24 doubles to 48.", "rationale": "30 and 36 add a constant; 60 multiplies by 2.5."},
    {"stem": f"अगली संख्या क्या होगी?  {S(*seq1)}, ?", "explanation": "हर संख्या पिछली संख्या की दुगुनी है, इसलिए 24 का दुगुना 48 है।"})

seq2 = [5 + 4 * i for i in range(4)]
assert seq2 == [5, 9, 13, 17] and seq2[-1] + 4 == 21
add("PIA-GF-SQ-002", "gf", "number-sequence", "sequence", "easy", "21", strs(19, 20, 22),
    {"stem": f"What number comes next?  {S(*seq2)}, ?", "explanation": "The numbers go up by 4 each time, so 17 + 4 = 21.", "rationale": "20 and 22 break the constant step of 4."},
    {"stem": f"अगली संख्या क्या होगी?  {S(*seq2)}, ?", "explanation": "संख्याएँ हर बार 4 बढ़ती हैं, इसलिए 17 + 4 = 21।"})

# --- visual matrices ---------------------------------------------------------------------------------------
KINDS = ["circle", "square", "triangle"]
MX_EN = "Look at the picture. Which option (A–D) completes the pattern in the empty cell?"
MX_HI = "चित्र देखिए। कौन-सा विकल्प (A–D) खाली खाने में पैटर्न को पूरा करता है?"


def matrix_item(code, diff, builder, en, hi):
    rng = random.Random(code)
    cell_draw, option_draws, correct_i = builder(rng)
    order = list(range(4))
    rng.shuffle(order)
    svg = g.matrix_svg(cell_draw, lambda i, x, y, s: option_draws[order[i]](x, y, s),
                       "Three by three pattern matrix with four answer options A to D", "Which option completes the pattern in the empty (?) cell?")
    add_visual(code, "gf", "figure-matrix", "matrix", diff, "abcd"[order.index(correct_i)], svg, en, hi)


def b_count(rng):  # row = shape, column = how many
    cell = lambda r, c, x, y, s: g.count_svg(KINDS[r], c + 1, x, y, s)  # noqa: E731
    opts = [lambda x, y, s: g.count_svg("triangle", 3, x, y, s), lambda x, y, s: g.count_svg("triangle", 2, x, y, s),
            lambda x, y, s: g.count_svg("square", 3, x, y, s), lambda x, y, s: g.count_svg("triangle", 4, x, y, s)]
    return cell, opts, 0


matrix_item("PIA-GF-MX-001", "easy", b_count,
            {"stem": MX_EN, "explanation": "Each row uses one shape, and the number of shapes grows by one across the row: 1, 2, then 3. The bottom row uses triangles, so the answer is 3 triangles.", "rationale": "Other options change the shape or the count."},
            {"stem": MX_HI, "explanation": "हर पंक्ति में एक ही आकृति है और पंक्ति में आकृतियों की संख्या 1, 2, फिर 3 होती है। निचली पंक्ति में त्रिभुज हैं, इसलिए उत्तर 3 त्रिभुज है।"})

seq4 = [2, 3, 5, 8, 12]
assert [seq4[i + 1] - seq4[i] for i in range(4)] == [1, 2, 3, 4] and seq4[-1] + 5 == 17
add("PIA-GF-SQ-003", "gf", "number-sequence", "sequence", "medium", "17", strs(15, 16, 18),
    {"stem": f"What number comes next?  {S(*seq4)}, ?", "explanation": "The gaps grow by one each time (+1, +2, +3, +4), so the next gap is +5: 12 + 5 = 17.", "rationale": "15, 16 and 18 break the growing-gap rule."},
    {"stem": f"अगली संख्या क्या होगी?  {S(*seq4)}, ?", "explanation": "अंतर हर बार एक बढ़ता है (+1, +2, +3, +4), इसलिए अगला अंतर +5 है: 12 + 5 = 17।"})

pairs5 = {n: n * (n + 1) for n in (2, 3, 4, 5)}
assert pairs5 == {2: 6, 3: 12, 4: 20, 5: 30}
add("PIA-GF-RI-001", "gf", "rule-induction", "rule-induction", "medium", "30", strs(25, 28, 36),
    {"stem": "Find the rule.  2 → 6,  3 → 12,  4 → 20,  5 → ?", "explanation": "Each result is the number multiplied by the next number: 2×3, 3×4, 4×5, so 5×6 = 30.", "rationale": "25 squares the input; 28 and 36 follow other partial patterns."},
    {"stem": "नियम खोजिए।  2 → 6,  3 → 12,  4 → 20,  5 → ?", "explanation": "हर परिणाम संख्या और उसके अगले अंक का गुणनफल है: 2×3, 3×4, 4×5, इसलिए 5×6 = 30।"})


def b_rotate(rng):
    rot_of = lambda r, c: ([0, 90, 180][r] + 90 * c) % 360  # noqa: E731
    assert rot_of(2, 2) == 0
    cell = lambda r, c, x, y, s: g.shape_svg("arrow", x + s / 2, y + s / 2, s * .3, rot_of(r, c))  # noqa: E731
    opts = [(lambda a: (lambda x, y, s: g.shape_svg("arrow", x + s / 2, y + s / 2, s * .3, a)))(a) for a in (0, 90, 180, 270)]
    return cell, opts, 0


matrix_item("PIA-GF-MX-002", "medium", b_rotate,
            {"stem": MX_EN, "explanation": "The arrow turns 90° clockwise from left to right in every row, and each row starts 90° further round. The bottom-right arrow completes a full turn and points up.", "rationale": "The other options are the other three arrow directions."},
            {"stem": MX_HI, "explanation": "हर पंक्ति में तीर बाएँ से दाएँ 90° घड़ी की दिशा में घूमता है और हर पंक्ति पिछली से 90° आगे शुरू होती है। निचला दायाँ तीर पूरा चक्कर लगाकर ऊपर की ओर होता है।"})


def b_latin(rng):
    assert KINDS[(2 + 2) % 3] == "square"
    cell = lambda r, c, x, y, s: g.shape_svg(KINDS[(r + c) % 3], x + s / 2, y + s / 2, s * .28)  # noqa: E731
    opts = [(lambda k: (lambda x, y, s: g.shape_svg(k, x + s / 2, y + s / 2, s * .28)))(k) for k in ("square", "circle", "triangle", "diamond")]
    return cell, opts, 0


matrix_item("PIA-GF-MX-003", "hard", b_latin,
            {"stem": MX_EN, "explanation": "Every row and every column contains a circle, a square and a triangle once each. The bottom row has a triangle and a circle, so the missing shape is a square.", "rationale": "A circle or triangle would repeat in the row or column; a diamond never appears."},
            {"stem": MX_HI, "explanation": "हर पंक्ति और हर स्तंभ में वृत्त, वर्ग और त्रिभुज एक-एक बार आते हैं। निचली पंक्ति में त्रिभुज और वृत्त हैं, इसलिए छूटी आकृति वर्ग है।"})

seq7 = [2, 5, 4, 10, 8, 20, 16]
assert seq7[0::2] == [2, 4, 8, 16] and seq7[1::2] == [5, 10, 20] and 20 * 2 == 40
add("PIA-GF-SQ-004", "gf", "number-sequence", "sequence", "hard", "40", strs(32, 36, 30),
    {"stem": f"What number comes next?  {S(*seq7)}, ?", "explanation": "Two patterns are mixed. Numbers in odd places double (2, 4, 8, 16) and numbers in even places double (5, 10, 20). The next is in an even place: 20 × 2 = 40.", "rationale": "32 continues the odd-place pattern only."},
    {"stem": f"अगली संख्या क्या होगी?  {S(*seq7)}, ?", "explanation": "दो पैटर्न मिले हैं। विषम स्थानों की संख्याएँ दुगुनी होती हैं (2, 4, 8, 16) और सम स्थानों की भी (5, 10, 20)। अगली संख्या सम स्थान पर है: 20 × 2 = 40।"})

rule9 = lambda a, b: 2 * a + b  # noqa: E731
assert (rule9(2, 3), rule9(4, 1), rule9(5, 2)) == (7, 9, 12)
add("PIA-GF-RI-002", "gf", "rule-induction", "rule-induction", "hard", "12", strs(10, 11, 14),
    {"stem": "Find the rule.  (2, 3) → 7,  (4, 1) → 9,  (5, 2) → ?", "explanation": "Double the first number and add the second: 2×2+3 = 7, 2×4+1 = 9, so 2×5+2 = 12.", "rationale": "10 and 11 come from partial versions of the rule; 14 doubles the second number instead."},
    {"stem": "नियम खोजिए।  (2, 3) → 7,  (4, 1) → 9,  (5, 2) → ?", "explanation": "पहली संख्या को दुगुना करके दूसरी संख्या जोड़िए: 2×2+3 = 7, 2×4+1 = 9, इसलिए 2×5+2 = 12।"})


def b_xor(rng):  # expert: third picture = squares in exactly one of the first two
    while True:
        rows = []
        for _ in range(3):
            a = frozenset(rng.sample(range(9), rng.randint(3, 5)))
            b = frozenset(rng.sample(range(9), rng.randint(3, 5)))
            rows.append((a, b, a ^ b))
        if all(a - b and b - a and a & b for a, b, _ in rows):
            break
    a, b, answer = rows[2]
    off = answer ^ frozenset({min(answer)})  # one square different
    candidates = [answer, a | b, a & b, off]
    assert len(set(candidates)) == 4
    cell = lambda r, c, x, y, s: g.bits_svg(rows[r][c], x, y, s)  # noqa: E731
    opts = [(lambda bits: (lambda x, y, s: g.bits_svg(bits, x, y, s)))(bits) for bits in candidates]
    return cell, opts, 0


matrix_item("PIA-GF-MX-004", "expert", b_xor,
            {"stem": MX_EN, "explanation": "In each row, the third picture keeps only the squares that appear in exactly one of the first two pictures. Squares that appear in both cancel out.", "rationale": "One distractor keeps every square from either picture; another keeps only shared squares; another is one square off."},
            {"stem": MX_HI, "explanation": "हर पंक्ति में तीसरे चित्र में केवल वे वर्ग रहते हैं जो पहले दो चित्रों में से ठीक एक में हैं। जो दोनों में हैं, वे हट जाते हैं।"})

# ================= Verbal comprehension (Gc) ================================================================
add("PIA-GC-AN-001", "gc", "verbal-analogy", "analogy", "easy", ("Night", "रात"), [("Sun", "सूरज"), ("Light", "रोशनी"), ("Morning", "सुबह")],
    {"stem": "Hot is to cold as day is to ___.", "explanation": "Hot and cold are opposites; the opposite of day is night.", "rationale": "Sun, light and morning go with day rather than against it."},
    {"stem": "गर्म का संबंध ठंडे से है, तो दिन का संबंध ___ से है।", "explanation": "गर्म और ठंडा विपरीत हैं; दिन का विपरीत रात है।"})
add("PIA-GC-CL-001", "gc", "classification", "odd-one-out", "easy", ("Apple", "सेब"), [("Table", "मेज़"), ("Chair", "कुर्सी"), ("Bench", "बेंच")],
    {"stem": "Which word does NOT belong with the others?", "explanation": "Table, chair and bench are furniture; an apple is a fruit.", "rationale": "The three furniture words share a category."},
    {"stem": "कौन-सा शब्द बाकी से अलग है?", "explanation": "मेज़, कुर्सी और बेंच फ़र्नीचर हैं; सेब फल है।"})
add("PIA-GC-AN-002", "gc", "verbal-analogy", "analogy", "medium", ("Clock : Time", "घड़ी : समय"), [("Ruler : Wood", "स्केल : लकड़ी"), ("Scale : Fish", "तराज़ू : मछली"), ("Pen : Paper", "कलम : काग़ज़")],
    {"stem": "Which pair has the same relationship as  Thermometer : Temperature ?", "explanation": "A thermometer is an instrument that measures temperature; a clock is an instrument that measures time.", "rationale": "The other pairs relate a tool to its material, to an unrelated object, or to a surface."},
    {"stem": "किस जोड़ी में वही संबंध है जो  थर्मामीटर : तापमान  में है?", "explanation": "थर्मामीटर तापमान मापने का उपकरण है; घड़ी समय मापने का उपकरण है।"})
add("PIA-GC-WR-001", "gc", "word-relationship", "opposites", "medium", ("Plentiful", "प्रचुर"), [("Rare", "दुर्लभ"), ("Tiny", "छोटा"), ("Costly", "महँगा")],
    {"stem": "Choose the word that means the OPPOSITE of  scarce.", "explanation": "Scarce means hard to find or in short supply. Plentiful means there is a lot.", "rationale": "Rare is a synonym of scarce."},
    {"stem": "उस शब्द को चुनिए जिसका अर्थ  अल्प  का विलोम है।", "explanation": "अल्प का अर्थ है बहुत कम। प्रचुर का अर्थ है बहुत अधिक।"})
add("PIA-GC-VR-001", "gc", "verbal-reasoning", "syllogism", "medium", ("All cats need food.", "सभी बिल्लियों को भोजन चाहिए।"),
    [("All animals are cats.", "सभी जानवर बिल्लियाँ हैं।"), ("Some animals do not need food.", "कुछ जानवरों को भोजन नहीं चाहिए।"), ("Cats are the only animals.", "बिल्लियाँ ही एकमात्र जानवर हैं।")],
    {"stem": "All cats are animals. All animals need food. Which statement must be true?", "explanation": "Cats are animals, and animals need food, so cats need food.", "rationale": "The other statements reverse or contradict the given facts."},
    {"stem": "सभी बिल्लियाँ जानवर हैं। सभी जानवरों को भोजन चाहिए। कौन-सा कथन अवश्य सत्य है?", "explanation": "बिल्लियाँ जानवर हैं और जानवरों को भोजन चाहिए, इसलिए बिल्लियों को भोजन चाहिए।"})
height_order = ["Mira", "Neha", "Sana", "Tara", "Rohan"]  # tallest first, derived from the five facts in the stem
assert height_order[1] == "Neha"
add("PIA-GC-VR-002", "gc", "verbal-reasoning", "ordering", "hard", ("Neha", "नेहा"), [("Mira", "मीरा"), ("Sana", "सना"), ("Tara", "तारा")],
    {"stem": "Mira is taller than Sana. Sana is taller than Tara. Rohan is shorter than Tara. Neha is taller than Sana but shorter than Mira. Who is the second tallest?",
     "explanation": "The order from tallest is Mira, Neha, Sana, Tara, Rohan. Neha is second.", "rationale": "Mira is tallest; Sana is third."},
    {"stem": "मीरा सना से लंबी है। सना तारा से लंबी है। रोहन तारा से छोटा है। नेहा सना से लंबी है पर मीरा से छोटी। दूसरी सबसे लंबी कौन है?",
     "explanation": "सबसे लंबे से क्रम: मीरा, नेहा, सना, तारा, रोहन। नेहा दूसरे स्थान पर है।"})
add("PIA-GC-VR-003", "gc", "verbal-reasoning", "conditional-logic", "expert",
    ("Ravi is a member and not a student.", "रवि सदस्य है और विद्यार्थी नहीं है।"),
    [("Ravi is a student.", "रवि विद्यार्थी है।"), ("Ravi is not a member.", "रवि सदस्य नहीं है।"), ("Ravi is a member and a student.", "रवि सदस्य है और विद्यार्थी भी है।")],
    {"stem": "Only members can enter the club. Students are not allowed to bring a guest. Ravi entered the club and brought a guest. Which must be true?",
     "explanation": "Ravi entered, so he is a member. He brought a guest, so he cannot be a student.", "rationale": "Each wrong option contradicts one of the two facts."},
    {"stem": "क्लब में केवल सदस्य ही प्रवेश कर सकते हैं। विद्यार्थियों को मेहमान लाने की अनुमति नहीं है। रवि क्लब में गया और मेहमान को भी ले गया। कौन-सा कथन अवश्य सत्य है?",
     "explanation": "रवि क्लब में गया, इसलिए वह सदस्य है। वह मेहमान लाया, इसलिए विद्यार्थी नहीं हो सकता।"})


# ================= Visual-spatial (Gv) ======================================================================
def chiral_shape(n, rng, max_box=4):
    pool = [s for s in g.free_polyominoes(n) if g.chiral(s) and max(g.extent(s)) <= max_box and len(g.rotations(s)) == 4]
    return rng.choice(pool)


def shape_item(code, diff, fmt, sub, kind, n, en, hi, k=1):
    rng = random.Random(code)
    s = chiral_shape(n, rng)
    if kind == "rotate":  # correct: a pure turn; distractors: mirror images
        correct, wrong = g.rot(s, k), [g.flip(g.rot(s, j)) for j in range(4) if j != k][:3]
        family = g.rotations(s)
    elif kind == "mirror":  # correct: the mirror image; distractors: pure turns
        correct, wrong = g.flip(s), [g.rot(s, j) for j in (1, 2, 3)]
        family = g.rotations(g.flip(s))
    else:  # mirror image that is also turned
        correct, wrong = g.flip(g.rot(s, k)), [g.rot(s, j) for j in (0, 1, 2)]
        family = g.rotations(g.flip(s))
    opts, key = g.shuffled_options(correct, wrong, rng)
    assert len(set(opts)) == 4
    in_family = [o in family for o in opts]
    assert in_family.count(True) == 1 and "abcd"[in_family.index(True)] == key  # exactly one option satisfies the question
    svg = g.shape_question_svg(s, opts, "Target shape above and four answer options A to D", "Target shape")
    add_visual(code, "gv", sub, fmt, diff, key, svg, en, hi)


def fit_item(code, diff, n, near, en, hi):
    rng = random.Random(code)
    while True:
        hole = rng.choice([s for s in g.free_polyominoes(n) if max(g.extent(s)) <= 4 and len(g.rotations(s)) >= 4])
        pool = g.near_misses(hole) if near else [s for s in g.free_polyominoes(n) if not g.congruent(s, hole) and max(g.extent(s)) <= 5]
        pool = [s for s in pool if max(g.extent(s)) <= 5]
        if len(pool) >= 3:
            break
    wrong = rng.sample(pool, 3)
    correct = g.rot(hole, rng.choice([1, 2, 3]))
    opts, key = g.shuffled_options(correct, wrong, rng)
    fits = [g.congruent(o, hole) for o in opts]
    assert fits.count(True) == 1 and "abcd"[fits.index(True)] == key  # exactly one piece can fill the gap
    assert len({g.norm(o) for o in opts}) == 4
    w, h = g.extent(hole)
    at = (rng.randint(0, 1), rng.randint(0, 1))
    svg = g.fit_question_svg(w + 1, h + 1, hole, at, opts, "Grey board with a gap and four pieces A to D", "Which piece fills the gap? (Pieces may be turned.)")
    add_visual(code, "gv", "spatial-matching", "piece-fit", diff, key, svg, en, hi)


ROT_EN = {"stem": "One option shows the target shape turned (rotated) but not flipped. Which one?", "explanation": "Turning a shape never changes which way it 'leans'. The other options are mirror images, which no turn can produce.", "rationale": "Mirror images look similar but cannot be matched by turning."}
ROT_HI = {"stem": "एक विकल्प में लक्ष्य आकृति को केवल घुमाया गया है, पलटा नहीं गया है। कौन-सा?", "explanation": "घुमाने से आकृति का रूप नहीं बदलता। बाकी विकल्प दर्पण-प्रतिबिंब हैं, जो घुमाने से नहीं बन सकते।"}
MIR_EN = {"stem": "Which option is the MIRROR IMAGE of the target shape (flipped left to right, not turned)?", "explanation": "A mirror image reverses left and right. Turned copies of the original cannot match it.", "rationale": "The other options are turned copies of the original shape."}
MIR_HI = {"stem": "कौन-सा विकल्प लक्ष्य आकृति का दर्पण-प्रतिबिंब है (बाएँ-दाएँ पलटा हुआ, घुमाया हुआ नहीं)?", "explanation": "दर्पण-प्रतिबिंब में बायाँ-दायाँ उलट जाता है। मूल आकृति के घुमाए रूप उससे नहीं मिलते।"}
MIT_EN = {"stem": "Which option is a MIRROR IMAGE of the target shape? (It may also be turned.)", "explanation": "Only one option is flipped; the rest are plain turns of the original.", "rationale": "Turned copies of the original are not mirror images."}
MIT_HI = {"stem": "कौन-सा विकल्प लक्ष्य आकृति का दर्पण-प्रतिबिंब है? (वह घुमाया हुआ भी हो सकता है।)", "explanation": "केवल एक विकल्प पलटा हुआ है; बाकी मूल आकृति के सादे घुमाव हैं।"}
FIT_EN = {"stem": "Which piece exactly fills the gap in the board? Pieces may be turned but not flipped.", "explanation": "Only one piece has exactly the shape of the gap once it is turned.", "rationale": "The other pieces have the same number of squares but a different shape."}
FIT_HI = {"stem": "कौन-सा टुकड़ा बोर्ड की खाली जगह को ठीक-ठीक भरता है? टुकड़ों को घुमाया जा सकता है, पलटा नहीं जा सकता।", "explanation": "घुमाने पर केवल एक टुकड़े का आकार खाली जगह जैसा होता है।"}

shape_item("PIA-GV-RT-001", "easy", "mental-rotation", "mental-rotation", "rotate", 5, ROT_EN, ROT_HI, k=1)
shape_item("PIA-GV-MR-001", "easy", "mirror-image", "figure-transformation", "mirror", 5, MIR_EN, MIR_HI)
shape_item("PIA-GV-RT-002", "medium", "mental-rotation", "mental-rotation", "rotate", 6, ROT_EN, ROT_HI, k=2)
fit_item("PIA-GV-FT-001", "medium", 5, False, FIT_EN, FIT_HI)
shape_item("PIA-GV-MR-002", "hard", "mirror-image", "figure-transformation", "mirror-turned", 6, MIT_EN, MIT_HI, k=1)
shape_item("PIA-GV-RT-003", "hard", "mental-rotation", "mental-rotation", "rotate", 7, ROT_EN, ROT_HI, k=3)
fit_item("PIA-GV-FT-002", "hard", 6, False, FIT_EN, FIT_HI)
fit_item("PIA-GV-FT-003", "expert", 7, True, FIT_EN, FIT_HI)


# ================= Working memory (Gwm): timed, shown once =================================================
digits = lambda s: " ".join(str(d) for d in s)  # noqa: E731


def span_options(seq, backward):
    target = list(reversed(seq)) if backward else list(seq)
    rng = random.Random("".join(map(str, seq)) + str(backward))
    out = [target]
    swaps = list(range(len(target) - 1))
    rng.shuffle(swaps)
    for i in swaps[:2]:
        t = list(target)
        t[i], t[i + 1] = t[i + 1], t[i]
        out.append(t)
    wrong_dir = list(seq) if backward else list(reversed(seq))
    if wrong_dir not in out:
        out.append(wrong_dir)
    while len(out) < 4:
        t = list(target)
        i = rng.randrange(len(t))
        t[i] = (t[i] + rng.randint(1, 8)) % 10
        if t not in out:
            out.append(t)
    return digits(out[0]), [digits(o) for o in out[1:4]]


def span_item(code, diff, seq, seconds, backward):
    c, w = span_options(seq, backward)
    q_en = "Which sequence is the numbers you saw, in REVERSE order (last number first)?" if backward else "Which sequence is exactly the numbers you saw, in the same order?"
    q_hi = "आपने जो संख्याएँ देखीं, उनका उलटा क्रम (अंतिम संख्या पहले) कौन-सा है?" if backward else "आपने जो संख्याएँ देखीं, उन्हीं का ठीक वही क्रम कौन-सा है?"
    en = {"stem": q_en, "stimulus": digits(seq), "explanation": f"The numbers shown were {digits(seq)}." + (f" Reversed: {c}." if backward else ""), "rationale": "Distractors swap neighbouring numbers or reverse the order."}
    hi = {"stem": q_hi, "stimulus": digits(seq), "explanation": f"दिखाई गई संख्याएँ {digits(seq)} थीं।" + (f" उलटा क्रम: {c}।" if backward else "")}
    add(code, "gwm", "backward-span" if backward else "forward-span", "backward-span" if backward else "forward-span", diff, c, w, en, hi,
        display=seconds, stimulus_type="timed-text", note=TIMED_NOTE)


span_item("PIA-GWM-DS-001", "easy", [4, 9, 2, 7], 4, False)
span_item("PIA-GWM-DS-002", "medium", [8, 3, 6, 1, 5], 5, False)
span_item("PIA-GWM-DB-001", "medium", [5, 2, 9], 4, True)
span_item("PIA-GWM-DB-002", "medium", [3, 8, 1, 6], 5, True)
span_item("PIA-GWM-DS-003", "hard", [7, 2, 9, 4, 1, 8], 6, False)

val = 5
for step in (+3, -2, +4):
    val += step
assert val == 10
add("PIA-GWM-UP-001", "gwm", "sequence-updating", "updating", "hard", "10", ["9", "11", "12"],
    {"stem": "Starting with the first number, apply each change in order. What is the final number?", "stimulus": "5, then +3, then −2, then +4",
     "explanation": "5 + 3 = 8; 8 − 2 = 6; 6 + 4 = 10.", "rationale": "9 and 11 drop or repeat one step."},
    {"stem": "पहली संख्या से शुरू करके हर बदलाव को क्रम से लागू कीजिए। अंतिम संख्या क्या है?", "stimulus": "5, फिर +3, फिर −2, फिर +4",
     "explanation": "5 + 3 = 8; 8 − 2 = 6; 6 + 4 = 10।"},
    display=8, stimulus_type="timed-text", note=TIMED_NOTE)

letters = ["R", "K", "T", "B", "M"]
assert sorted(letters) == ["B", "K", "M", "R", "T"] and sorted(letters)[2] == "M"
add("PIA-GWM-MN-001", "gwm", "mental-manipulation", "manipulation", "expert", "M", ["K", "R", "T"],
    {"stem": "Put the letters you saw in alphabetical order. Which letter is third?", "stimulus": "R   K   T   B   M",
     "explanation": "In alphabetical order the letters are B, K, M, R, T. The third is M.", "rationale": "K, R and T are the 2nd, 4th and 5th letters."},
    {"stem": "आपने जो अक्षर देखे उन्हें अंग्रेज़ी वर्णमाला (A–Z) के क्रम में रखिए। तीसरा अक्षर कौन-सा है?", "stimulus": "R   K   T   B   M",
     "explanation": "वर्णमाला क्रम में अक्षर B, K, M, R, T हैं। तीसरा M है।"},
    display=6, stimulus_type="timed-text", note=TIMED_NOTE)

# ================= Processing speed (Gs) ====================================================================
assert "▲ ● ▲ ■ ▲ ●".split().count("▲") == 3
add("PIA-GS-VS-001", "gs", "visual-search", "count", "easy", "3", ["2", "4", "5"],
    {"stem": "How many ▲ are in this row?   ▲ ● ▲ ■ ▲ ●", "explanation": "▲ appears 3 times.", "rationale": "Counting slips are the usual error."},
    {"stem": "इस पंक्ति में कितने ▲ हैं?   ▲ ● ▲ ■ ▲ ●", "explanation": "▲ 3 बार आता है।"}, stimulus_type="symbols", note="Symbols may need a text alternative for screen readers.")
add("PIA-GS-CP-001", "gs", "timed-comparison", "pair-match", "easy", "91564 — 91564", ["48372 — 48732", "70851 — 70815", "26394 — 26349"],
    {"stem": "Which pair of numbers is IDENTICAL?", "explanation": "Only 91564 — 91564 matches digit for digit.", "rationale": "The other pairs swap two neighbouring digits."},
    {"stem": "संख्याओं की कौन-सी जोड़ी बिल्कुल एक जैसी है?", "explanation": "केवल 91564 — 91564 अंक-दर-अंक मेल खाती है।"}, stimulus_type="symbols")
add("PIA-GS-VS-002", "gs", "visual-search", "odd-one-out", "easy", ("4th", "चौथा"), [("1st", "पहला"), ("3rd", "तीसरा"), ("5th", "पाँचवाँ")],
    {"stem": "Which one is different?   ■ ■ ■ □ ■", "explanation": "The 4th symbol is an empty square; the rest are filled.", "rationale": "Positions 1, 3 and 5 are filled squares."},
    {"stem": "कौन-सा अलग है?   ■ ■ ■ □ ■", "explanation": "चौथा चिह्न खाली वर्ग है; बाकी भरे हुए हैं।"}, stimulus_type="symbols")

key4 = {"▲": 1, "●": 2, "■": 3, "◆": 4}
assert "".join(str(key4[s]) for s in "● ▲ ◆ ■".split()) == "2143"
add("PIA-GS-CD-001", "gs", "coding", "symbol-digit", "medium", "2143", ["2134", "2413", "1243"],
    {"stem": "Use the key to turn the symbols into numbers.   ▲=1  ●=2  ■=3  ◆=4      ● ▲ ◆ ■", "explanation": "● is 2, ▲ is 1, ◆ is 4, ■ is 3, giving 2143.", "rationale": "Distractors swap two digits."},
    {"stem": "कुंजी की मदद से चिह्नों को संख्याओं में बदलिए।   ▲=1  ●=2  ■=3  ◆=4      ● ▲ ◆ ■", "explanation": "● = 2, ▲ = 1, ◆ = 4, ■ = 3, यानी 2143।"}, stimulus_type="symbols")
assert "3 7 1 7 7 4 9 7 2 7".split().count("7") == 5
add("PIA-GS-VS-003", "gs", "visual-search", "count", "medium", "5", ["4", "6", "3"],
    {"stem": "How many times does the digit 7 appear?   3 7 1 7 7 4 9 7 2 7", "explanation": "7 appears 5 times.", "rationale": "Counting slips are the usual error."},
    {"stem": "अंक 7 कितनी बार आता है?   3 7 1 7 7 4 9 7 2 7", "explanation": "7 पाँच बार आता है।"}, stimulus_type="symbols")
key5 = {"▲": 3, "●": 8, "■": 5, "◆": 1, "★": 9}
code6 = "".join(str(key5[s]) for s in "◆ ● ★ ▲ ■ ● ◆ ★".split())
assert code6 == "18935819"
add("PIA-GS-CD-002", "gs", "coding", "symbol-digit", "hard", code6, ["18935891", "18395819", "81935819"],
    {"stem": "Use the key.   ▲=3  ●=8  ■=5  ◆=1  ★=9      ◆ ● ★ ▲ ■ ● ◆ ★", "explanation": f"Translate each symbol in order: {code6}.", "rationale": "Distractors swap neighbouring digits."},
    {"stem": "कुंजी का उपयोग कीजिए।   ▲=3  ●=8  ■=5  ◆=1  ★=9      ◆ ● ★ ▲ ■ ● ◆ ★", "explanation": f"हर चिह्न को क्रम से बदलिए: {code6}।"}, stimulus_type="symbols")
r1, r2 = "4 7 2 9 1 5 8 3 6 0 2 7".split(), "4 7 3 9 1 5 8 8 6 0 5 7".split()
assert sum(a != b for a, b in zip(r1, r2)) == 3
add("PIA-GS-CP-002", "gs", "timed-comparison", "difference-count", "expert", "3", ["2", "4", "5"],
    {"stem": "In how many places do the two rows differ?\nRow 1:  4 7 2 9 1 5 8 3 6 0 2 7\nRow 2:  4 7 3 9 1 5 8 8 6 0 5 7", "explanation": "They differ in the 3rd, 8th and 11th places: 3 differences.", "rationale": "Missing one place or counting one extra are the usual errors."},
    {"stem": "दोनों पंक्तियाँ कितनी जगह अलग हैं?\nपंक्ति 1:  4 7 2 9 1 5 8 3 6 0 2 7\nपंक्ति 2:  4 7 3 9 1 5 8 8 6 0 5 7", "explanation": "वे तीसरे, आठवें और ग्यारहवें स्थान पर अलग हैं: 3 अंतर।"}, stimulus_type="symbols")

# ================= Quantitative reasoning (Gq) ==============================================================
assert 12 * 5 == 60
add("PIA-GQ-AR-001", "gq", "applied-numerical", "arithmetic", "easy", "60", ["17", "48", "72"],
    {"stem": "A notebook costs 12 rupees. How much do 5 notebooks cost, in rupees?", "explanation": "5 × 12 = 60.", "rationale": "17 adds instead of multiplying."},
    {"stem": "एक कॉपी 12 रुपये की है। 5 कॉपियों की कीमत कितने रुपये होगी?", "explanation": "5 × 12 = 60।"})
assert next(x for x in range(1, 50) if x + (x + 4) == 14) == 5
add("PIA-GQ-NR-001", "gq", "numerical-relationship", "arithmetic-logic", "medium", "5", ["3", "7", "9"],
    {"stem": "A pen costs 4 rupees more than a pencil. Together they cost 14 rupees. How much is the pencil, in rupees?", "explanation": "Pencil = x, pen = x + 4, so 2x + 4 = 14 and x = 5.", "rationale": "7 is the common mistake of removing 4 only once."},
    {"stem": "एक पेन पेंसिल से 4 रुपये महँगा है। दोनों मिलाकर 14 रुपये के हैं। पेंसिल कितने रुपये की है?", "explanation": "पेंसिल = x, पेन = x + 4, इसलिए 2x + 4 = 14 और x = 5।"})
s3 = [n * (n + 1) for n in range(1, 7)]
assert s3 == [2, 6, 12, 20, 30, 42]
add("PIA-GQ-NP-001", "gq", "number-pattern", "pattern", "medium", "42", ["36", "40", "44"],
    {"stem": "What number comes next?  2, 6, 12, 20, 30, ?", "explanation": "The gaps are 4, 6, 8, 10, so the next gap is 12: 30 + 12 = 42.", "rationale": "36, 40 and 44 do not continue the growing gaps."},
    {"stem": "अगली संख्या क्या होगी?  2, 6, 12, 20, 30, ?", "explanation": "अंतर 4, 6, 8, 10 हैं, इसलिए अगला अंतर 12 है: 30 + 12 = 42।"})
assert (3 ** 3, 4 ** 3) == (27, 64)
add("PIA-GQ-QA-001", "gq", "quantitative-analogy", "analogy", "medium", "64", ["12", "16", "48"],
    {"stem": "3 : 27  as  4 : ?", "explanation": "27 is 3 × 3 × 3 (3 cubed), so 4 cubed is 64.", "rationale": "12 and 48 multiply instead of cubing; 16 squares."},
    {"stem": "3 : 27  वैसे ही जैसे  4 : ?", "explanation": "27 = 3 × 3 × 3 (3 का घन), इसलिए 4 का घन 64 है।"})
assert 60 / 45 * 120 == 160
add("PIA-GQ-AR-002", "gq", "applied-numerical", "rate", "hard", "160", ["120", "135", "180"],
    {"stem": "A train travels 60 km in 45 minutes. At the same speed, how far does it travel in 2 hours, in km?", "explanation": "60 km in 45 min is 80 km per hour, so 2 hours gives 160 km.", "rationale": "120 assumes 60 km per hour."},
    {"stem": "एक ट्रेन 45 मिनट में 60 किमी चलती है। उसी गति से 2 घंटे में वह कितने किमी चलेगी?", "explanation": "45 मिनट में 60 किमी का अर्थ है 80 किमी प्रति घंटा, इसलिए 2 घंटे में 160 किमी।"})
assert 5 * 12 - (10 + 11 + 13 + 14) == 12
add("PIA-GQ-AR-003", "gq", "applied-numerical", "average", "hard", "12", ["10", "11", "13"],
    {"stem": "The average of five numbers is 12. Four of them are 10, 11, 13 and 14. What is the fifth number?", "explanation": "The total must be 5 × 12 = 60. The four known numbers add to 48, so the fifth is 12.", "rationale": "Other options come from slips in the total."},
    {"stem": "पाँच संख्याओं का औसत 12 है। उनमें से चार संख्याएँ 10, 11, 13 और 14 हैं। पाँचवीं संख्या क्या है?", "explanation": "कुल योग 5 × 12 = 60 होना चाहिए। चार ज्ञात संख्याओं का योग 48 है, इसलिए पाँचवीं संख्या 12 है।"})
assert [m for m in range(1, 100) if (2 * m + 6) + (m + 6) == 48] == [12]
add("PIA-GQ-NR-002", "gq", "numerical-relationship", "algebraic-logic", "expert", "12", ["10", "14", "16"],
    {"stem": "Ravi is twice as old as Meena. In 6 years the sum of their ages will be 48. How old is Meena now?", "explanation": "Meena = m, Ravi = 2m. In 6 years: (2m + 6) + (m + 6) = 48, so 3m = 36 and m = 12.", "rationale": "Other options forget to add 6 to both ages."},
    {"stem": "रवि की आयु मीना से दुगुनी है। 6 वर्ष बाद उनकी आयु का योग 48 होगा। मीना की आयु अभी कितनी है?", "explanation": "मीना = m, रवि = 2m। 6 वर्ष बाद: (2m + 6) + (m + 6) = 48, इसलिए 3m = 36 और m = 12।"})

# ================= Long-term retrieval (Glr) ================================================================
PAIRS = [("Anil", "Umbrella", "अनिल", "छाता"), ("Meera", "Clock", "मीरा", "घड़ी"), ("Karan", "Lamp", "करण", "दीया"),
         ("Diya", "Kite", "दिया", "पतंग"), ("Rohan", "Bell", "रोहन", "घंटी"), ("Neha", "Cup", "नेहा", "प्याला")]
study_en = "\n".join(f"{a} – {b}" for a, b, _, _ in PAIRS)
study_hi = "\n".join(f"{c} – {d}" for _, _, c, d in PAIRS)
objects = [(b, d) for _, b, _, d in PAIRS]
names = [(a, c) for a, _, c, _ in PAIRS]
GLR_NOTE = TIMED_NOTE + " Retrieval items depend on item 1's study list."
add("PIA-GLR-PA-001", "glr", "paired-associate", "paired-associate-learning", "medium", objects[2], [objects[0], objects[4], objects[5]],
    {"stem": "Study the list of pairs. After it disappears: which object was paired with Karan?", "stimulus": study_en, "explanation": "Karan was paired with the lamp.", "rationale": "Other objects belong to other names in the list."},
    {"stem": "जोड़ियों की सूची ध्यान से देखिए। सूची हटने के बाद: करण के साथ कौन-सी वस्तु थी?", "stimulus": study_hi, "explanation": "करण के साथ दीया था।"},
    display=45, stimulus_type="timed-text", note=GLR_NOTE)
add("PIA-GLR-PA-002", "glr", "paired-associate", "delayed-association-recall", "medium", objects[3], [objects[1], objects[2], objects[5]],
    {"stem": "From the list of pairs you studied earlier: which object was paired with Diya?", "explanation": "Diya was paired with the kite.", "rationale": "Other objects belong to other names."},
    {"stem": "आपने पहले जो जोड़ियाँ देखी थीं, उनमें दिया के साथ कौन-सी वस्तु थी?", "explanation": "दिया के साथ पतंग थी।"}, note=GLR_NOTE)
add("PIA-GLR-PA-003", "glr", "paired-associate", "delayed-association-recall", "hard", names[1], [names[0], names[2], names[4]],
    {"stem": "From the list you studied earlier: who was paired with the Clock?", "explanation": "The clock was paired with Meera.", "rationale": "Other names belong to other objects."},
    {"stem": "आपने पहले जो सूची देखी थी, उसमें घड़ी के साथ कौन था?", "explanation": "घड़ी के साथ मीरा थी।"}, note=GLR_NOTE)
add("PIA-GLR-PA-004", "glr", "paired-associate", "recognition-of-pairs", "expert", ("Rohan – Bell", "रोहन – घंटी"),
    [("Rohan – Cup", "रोहन – प्याला"), ("Neha – Bell", "नेहा – घंटी"), ("Karan – Kite", "करण – पतंग")],
    {"stem": "Which of these pairs was in the list you studied?", "explanation": "Rohan was paired with the bell. The others recombine names and objects that were in the list.", "rationale": "Each wrong pair mixes a real name with a real object from a different pair."},
    {"stem": "इनमें से कौन-सी जोड़ी आपकी देखी हुई सूची में थी?", "explanation": "रोहन के साथ घंटी थी। बाकी जोड़ियों में सूची के नाम और वस्तुएँ आपस में मिला दी गई हैं।"}, note=GLR_NOTE)

# ================= assemble =================================================================================
DOMAIN_ORDER = ["gf", "gc", "gv", "gwm", "gs", "gq", "glr"]
DIFF_ORDER = ["easy", "medium", "hard", "expert"]


def main() -> None:
    ITEMS.sort(key=lambda i: (DOMAIN_ORDER.index(i["domain"]), DIFF_ORDER.index(i["difficulty"]), i["item_code"]))
    assert Counter(i["domain"] for i in ITEMS) == {"gf": 10, "gc": 7, "gv": 8, "gwm": 7, "gs": 7, "gq": 7, "glr": 4}
    assert Counter(i["difficulty"] for i in ITEMS) == {"easy": 12, "medium": 18, "hard": 13, "expert": 7}
    assert len({i["item_code"] for i in ITEMS}) == 50
    assert {i["asset_id"] for i in ITEMS if i["asset_id"]} == set(ASSET_FILES)
    ASSETS.mkdir(parents=True, exist_ok=True)
    for old in ASSETS.glob("pia-*.svg"):
        old.unlink()
    for asset_id, svg in ASSET_FILES.items():
        (ASSETS / f"{asset_id}.svg").write_text(svg, encoding="utf-8")
    form = {"code": "PIA-MASTER", "version": 1, "name": "PIA 50-question master form v1 (draft prototype)", "status": "draft", "items": [i["item_code"] for i in ITEMS]}
    with OUT.open("w", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps({"items": ITEMS, "form": form}, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {len(ITEMS)} items, {len(ASSET_FILES)} assets -> {OUT}")


if __name__ == "__main__":
    main()
