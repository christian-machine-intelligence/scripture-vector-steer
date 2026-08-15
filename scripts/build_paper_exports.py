from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

# python-docx is needed only for the DOCX export; figure rebuilding (and
# --figures-only) works without it.
try:
    from docx import Document
    from docx.enum.section import WD_SECTION
    from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    HAVE_DOCX = True
except ModuleNotFoundError:  # pragma: no cover - environment dependent
    HAVE_DOCX = False


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "results/paper/scripturevec_justice"
KEY_DATA = PACKET / "key_data"
FIG_DIR = PACKET / "figures"

# The paper markdown is the canonical, hand-maintained source. This script
# renders it (figures + DOCX) and can refresh the generated Table 3 block in
# place; it never rewrites the prose.
PAPER_MD = ROOT / "paper/search_out_a_matter_scripturevec_justice.md"
PAPER_DOCX = ROOT / "paper/search_out_a_matter_scripturevec_justice.docx"
PAPER_PDF = ROOT / "paper/search_out_a_matter_scripturevec_justice.pdf"

TABLE3_BEGIN = "<!-- TABLE3:BEGIN"
TABLE3_END = "<!-- TABLE3:END -->"
EXPANDED_SUMMARY = (
    ROOT
    / "results/experiments/scripturevec14/"
    / "scripturevec14_qwen3_14b_confirmed_chapter_layerloc_expandedgrid2_v1_summary.json"
)

FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_ITALIC = "/System/Library/Fonts/Supplemental/Arial Italic.ttf"

NAVY = "#172033"
BLUE = "#2563eb"
LIGHT_BLUE = "#dbeafe"
TEAL = "#0f766e"
AMBER = "#b45309"
GREEN = "#15803d"
RED = "#b91c1c"
GRAY = "#64748b"
LIGHT_GRAY = "#e5e7eb"
PAPER = "#fbfbf8"
INK = "#1f2937"


def read_csv(name: str) -> list[dict[str, str]]:
    with (KEY_DATA / name).open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with (KEY_DATA / name).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt_num(value: object, digits: int = 4) -> str:
    if value is None:
        return ""
    try:
        out = f"{float(value):.{digits}f}".rstrip("0").rstrip(".")
        return out if out else "0"
    except (TypeError, ValueError):
        return str(value)


def fmt_alpha(value: object) -> str:
    return str(int(float(value)))


def paired_text(paired: dict[str, object] | None) -> str:
    if not paired:
        return ""
    improve = int(paired.get("improve", 0))
    regress = int(paired.get("regress", 0))
    changes = int(paired.get("answer_changes", 0))
    return f"{changes} chg / {improve - regress:+d} net"


def target_metadata() -> dict[str, dict[str, str]]:
    rows = read_csv("chapter_confirmation_l40_survivors.csv")
    return {r["target"]: r for r in rows}


def refresh_localization_key_data() -> None:
    """Refresh paper-facing localization CSVs from the completed expanded grid."""
    if not EXPANDED_SUMMARY.exists():
        return
    data = json.loads(EXPANDED_SUMMARY.read_text())
    meta = target_metadata()

    cells = sorted(
        data["by_cell"],
        key=lambda r: (
            -int(r["paired_rescues"]),
            -float(r["mean_positive_delta"]),
            int(r["center"]),
            float(r["alpha"]),
        ),
    )
    cell_rows = [
        {
            "center_layer": int(r["center"]),
            "alpha": fmt_alpha(r["alpha"]),
            "rows": int(r["row_count"]),
            "accuracy_rescues": int(r["accuracy_rescues"]),
            "paired_rescues": int(r["paired_rescues"]),
            "mean_positive_delta": fmt_num(r["mean_positive_delta"]),
            "rescued_targets": ";".join(r["targets"]),
        }
        for r in cells
    ]
    write_csv(
        "layer_alpha_cells.csv",
        [
            "center_layer",
            "alpha",
            "rows",
            "accuracy_rescues",
            "paired_rescues",
            "mean_positive_delta",
            "rescued_targets",
        ],
        cell_rows,
    )

    expected = sorted(data["by_cell"], key=lambda r: (int(r["center"]), float(r["alpha"])))
    expected_rows = [
        {
            "center_layer": int(r["center"]),
            "alpha": fmt_alpha(r["alpha"]),
            "status": "completed",
            "paired_rescues": int(r["paired_rescues"]),
            "mean_positive_delta": fmt_num(r["mean_positive_delta"]),
            "rescued_targets": ";".join(r["targets"]),
        }
        for r in expected
    ]
    write_csv(
        "layer_alpha_expected_grid.csv",
        ["center_layer", "alpha", "status", "paired_rescues", "mean_positive_delta", "rescued_targets"],
        expected_rows,
    )

    target_rows = []
    for r in sorted(data["by_target"], key=lambda r: (-int(r["paired_rescues"]), r["target"])):
        m = meta[r["target"]]
        best = r["best_cell"]
        target_rows.append(
            {
                "target": r["target"],
                "book": m["book"],
                "chapter": m["chapter"],
                "reference": m["reference"],
                "paired_rescue_count": int(r["paired_rescues"]),
                "accuracy_rescue_count": int(r["accuracy_rescues"]),
                "best_center_layer": int(best["center"]),
                "best_alpha": fmt_alpha(best["alpha"]),
                "best_control_accuracy": fmt_num(best["control_accuracy"]),
                "best_positive_accuracy": fmt_num(best["positive_accuracy"]),
                "best_negative_accuracy": fmt_num(best["negative_accuracy"]),
                "best_null_accuracy": fmt_num(best["null_accuracy"]),
                "best_positive_paired": paired_text(best.get("positive_paired")),
            }
        )
    write_csv(
        "chapter_stability_by_localization.csv",
        [
            "target",
            "book",
            "chapter",
            "reference",
            "paired_rescue_count",
            "accuracy_rescue_count",
            "best_center_layer",
            "best_alpha",
            "best_control_accuracy",
            "best_positive_accuracy",
            "best_negative_accuracy",
            "best_null_accuracy",
            "best_positive_paired",
        ],
        target_rows,
    )

    detail_rows = []
    for r in sorted(data["rows"], key=lambda r: (int(r["center"]), float(r["alpha"]), r["target"])):
        m = meta[r["target"]]
        detail_rows.append(
            {
                "target": r["target"],
                "book": m["book"],
                "chapter": m["chapter"],
                "reference": m["reference"],
                "center_layer": int(r["center"]),
                "alpha": fmt_alpha(r["alpha"]),
                "control_accuracy": fmt_num(r["control_accuracy"]),
                "positive_accuracy": fmt_num(r["positive_accuracy"]),
                "positive_delta": fmt_num(r["positive_delta"]),
                "negative_accuracy": fmt_num(r["negative_accuracy"]),
                "null_accuracy": fmt_num(r["null_accuracy"]),
                "positive_paired": paired_text(r.get("positive_paired")),
                "paired_rescue": "yes" if r.get("is_paired_rescue") else "no",
            }
        )
    write_csv(
        "layer_alpha_target_rows.csv",
        [
            "target",
            "book",
            "chapter",
            "reference",
            "center_layer",
            "alpha",
            "control_accuracy",
            "positive_accuracy",
            "positive_delta",
            "negative_accuracy",
            "null_accuracy",
            "positive_paired",
            "paired_rescue",
        ],
        detail_rows,
    )

    cell_headers = [f"L{int(r['center'])}_a{int(float(r['alpha'])):03d}" for r in expected]
    rescue_lookup = {
        (r["target"], f"L{int(r['center'])}_a{int(float(r['alpha'])):03d}"): "1"
        for r in data["rows"]
        if r.get("is_paired_rescue")
    }
    matrix_rows = []
    for r in target_rows:
        row = {
            "target": r["target"],
            "book": r["book"],
            "chapter": r["chapter"],
            "reference": r["reference"],
        }
        for head in cell_headers:
            row[head] = rescue_lookup.get((r["target"], head), "0")
        matrix_rows.append(row)
    write_csv(
        "chapter_x_layer_alpha_rescue_matrix.csv",
        ["target", "book", "chapter", "reference"] + cell_headers,
        matrix_rows,
    )

    rollup = json.loads((KEY_DATA / "scripturevec_key_results_rollup.json").read_text())
    rollup.update(
        {
            "created_from": str(EXPANDED_SUMMARY.relative_to(ROOT)),
            "layer_localization_completed_cells": int(data["result_file_count"]),
            "layer_localization_expected_cells": int(data["result_file_count"]),
            "layer_localization_missing_cells": [],
            "layer_localization_rows": int(data["row_count"]),
            "layer_localization_paired_rescue_count": int(data["paired_rescue_count"]),
            "top_layer_alpha_cells": cell_rows[:12],
            "chapter_stability": target_rows,
        }
    )
    (KEY_DATA / "scripturevec_key_results_rollup.json").write_text(json.dumps(rollup, indent=2) + "\n")

    readme = f"""# ScriptureVec Paper Key Data Guide

This folder contains compact, AI-readable data extracts for drafting the ScriptureVec Justice paper. The files are derived from local experiment artifacts under `results/experiments/scripturevec14`.

## Topline Counts

- book_discovery_l10_candidate_count: `19`
- book_confirmation_l40_candidate_count: `19`
- book_confirmation_l40_survivor_count: `7`
- chapter_discovery_l10_clean_hit_count: `38`
- chapter_confirmation_l40_candidate_count: `38`
- chapter_confirmation_l40_survivor_count: `16`
- layer_localization_completed_cells: `{data["result_file_count"]}`
- layer_localization_expected_cells: `{data["result_file_count"]}`
- layer_localization_rows: `{data["row_count"]}`
- layer_localization_paired_rescue_count: `{data["paired_rescue_count"]}`

## Files

- `book_discovery_l10_candidates.csv`: The 19 preliminary book-level Justice candidates from the all-66-book discovery atlas.
- `book_confirmation_l40_all_candidates.csv`: All 19 preliminary book candidates retested at limit 40, including survivors and failures.
- `book_confirmation_l40_survivors.csv`: The seven book-level candidates that survived limit-40 confirmation.
- `chapter_discovery_l10_clean_hits.csv`: The 38 clean preliminary chapter hits from the seven confirmed book sources.
- `chapter_confirmation_l40_all_candidates.csv`: All 38 chapter candidates retested at limit 40.
- `chapter_confirmation_l40_survivors.csv`: The 16 confirmed chapter movers used for layer localization.
- `layer_alpha_cells.csv`: Completed layer/alpha localization cells, ranked by rescue count.
- `layer_alpha_expected_grid.csv`: The completed expanded localization grid in planned order.
- `chapter_stability_by_localization.csv`: How often each confirmed chapter was rescued across completed localization cells.
- `layer_alpha_target_rows.csv`: One row per chapter per completed layer/alpha cell.
- `chapter_x_layer_alpha_rescue_matrix.csv`: Plot-ready binary matrix for chapter-by-cell rescue heatmaps.
- `scripturevec_key_results_rollup.json`: One-file structured summary of the packet.

## Important Note

The expanded localization grid is complete. The strongest broad-coverage cell is `L30 / alpha 96`, with 13 paired rescues out of 16 confirmed chapter vectors and mean positive delta 0.0875. The strongest high-movement cell remains `L24 / alpha 32`, with 9 paired rescues and mean positive delta 0.1687. The most efficient low-alpha cell is `L28 / alpha 16`, with 11 paired rescues at a much gentler steering strength. This supports the paper's central claim that specific biblical chapter vectors form a structured layer-and-strength map rather than a flat Scripture effect.
"""
    (KEY_DATA / "README.md").write_text(readme)


def font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_REG
    if bold:
        path = FONT_BOLD
    if italic:
        path = FONT_ITALIC
    return ImageFont.truetype(path, size=size)


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        test = " ".join(cur + [word])
        if text_size(draw, test, fnt)[0] <= max_width or not cur:
            cur.append(word)
        else:
            lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    fnt: ImageFont.FreeTypeFont,
    fill: str,
    max_width: int,
    line_gap: int = 8,
    anchor: str = "la",
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, fnt, max_width)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill, anchor=anchor)
        y += fnt.size + line_gap
    return y


def clean_md_inline(text: str) -> str:
    text = text.replace("—", "—")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def axis(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int) -> None:
    draw.line((x0, y0, x1, y0), fill="#94a3b8", width=2)
    draw.line((x0, y0, x0, y1), fill="#94a3b8", width=2)


def title(draw: ImageDraw.ImageDraw, text: str, subtitle: str, w: int) -> None:
    draw.text((70, 45), text, font=font(44, bold=True), fill=NAVY)
    if subtitle:
        draw.text((72, 103), subtitle, font=font(24), fill=GRAY)


def save_img(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)


def figure_1() -> Path:
    """The search pipeline: every gate, and what each one removed."""
    roll = json.loads((KEY_DATA / "scripturevec_key_results_rollup.json").read_text())
    b_disc = roll["book_discovery_l10_candidate_count"]
    b_conf = roll["book_confirmation_l40_survivor_count"]
    c_hits = roll["chapter_discovery_l10_clean_hit_count"]
    c_conf = roll["chapter_confirmation_l40_survivor_count"]
    cells = roll["layer_localization_completed_cells"]

    # (count, unit, caption) for each surviving population, and the gate above it
    stages = [
        (66, "books", "the whole Protestant canon", None),
        (b_disc, "books", "survived the canon-wide screen",
         ("Gate 1 · Book discovery", "10 benchmark items · α = 32", f"66 → {b_disc}")),
        (b_conf, "books", "survived the wider retest",
         ("Gate 2 · Book confirmation", "40 benchmark items · α = 32", f"{b_disc} → {b_conf}")),
        (170, "chapters", f"every chapter of those {b_conf} books",
         ("Search region re-opened", "no test applied at this step", "")),
        (c_hits, "chapters", "survived the chapter screen",
         ("Gate 3 · Chapter discovery", "10 benchmark items · α = 32", f"170 → {c_hits}")),
        (c_conf, "chapters", "survived the wider retest",
         ("Gate 4 · Chapter confirmation", "40 benchmark items · α = 32", f"{c_hits} → {c_conf}")),
    ]

    # wide canvas so the right-hand control panel never crowds the row captions
    w = 2000
    bar_h, gate_h, top0 = 72, 96, 232
    funnel_bottom = top0 + len(stages) * (bar_h + gate_h) - gate_h + 20 + 108
    h = funnel_bottom + 150
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    title(d, "Figure 1. The Search Pipeline",
          "Four gates narrow the canon; every gate applies the same four-condition test", w)

    cx = 640
    min_w, max_w = 250, 900

    def bar_w(count: int) -> int:
        return int(min_w + (count / 170) ** 0.55 * (max_w - min_w))

    y = top0
    for i, (count, unit, caption, gate) in enumerate(stages):
        if gate:
            label, detail, delta = gate
            gy = y - gate_h + 18
            d.line((cx, gy - 16, cx, gy + 52), fill="#94a3b8", width=4)
            for dx in (-11, 11):  # arrowhead
                d.line((cx + dx, gy + 40, cx, gy + 56), fill="#94a3b8", width=4)
            d.text((cx + 34, gy + 4), label, font=font(23, bold=True), fill=NAVY, anchor="lm")
            d.text((cx + 34, gy + 36), detail, font=font(20), fill=GRAY, anchor="lm")
            if delta:
                d.text((cx - 34, gy + 20), delta, font=font(22, bold=True), fill=RED, anchor="rm")

        bw = bar_w(count)
        x0, x1 = cx - bw // 2, cx + bw // 2
        final = i == len(stages) - 1
        d.rounded_rectangle((x0, y, x1, y + bar_h), radius=18,
                            fill="#1d4ed8" if final else LIGHT_BLUE,
                            outline=NAVY if final else "#93c5fd", width=3 if final else 2)
        d.text((cx, y + 36), f"{count} {unit}", font=font(31, bold=True),
               fill="white" if final else NAVY, anchor="mm")
        d.text((x1 + 26, y + 36), caption, font=font(21), fill=GRAY, anchor="lm")
        y += bar_h + gate_h

    # the localization stage sits outside the funnel: it maps, it does not filter
    y = y - gate_h + 20
    d.line((cx, y - 30, cx, y + 8), fill="#94a3b8", width=4)
    d.rounded_rectangle((cx - 470, y + 16, cx + 470, y + 108), radius=18,
                        fill="#f0fdfa", outline=TEAL, width=3)
    d.text((cx, y + 48), f"Localization · {c_conf} chapters × {cells} layer/α cells",
           font=font(25, bold=True), fill=TEAL, anchor="mm")
    d.text((cx, y + 84), "maps where each chapter acts; filters nothing",
           font=font(20), fill=GRAY, anchor="mm")

    # what every gate actually tests
    px, py = 1500, top0 - 20
    d.rounded_rectangle((px, py, px + 440, py + 372), radius=18,
                        fill="#fffbeb", outline="#fcd34d", width=3)
    d.text((px + 24, py + 30), "At every gate, steering must", font=font(22, bold=True), fill=NAVY, anchor="lm")
    d.text((px + 24, py + 58), "beat all three controls:", font=font(22, bold=True), fill=NAVY, anchor="lm")
    for j, (name, gloss) in enumerate([
        ("the unsteered model", "does it help at all?"),
        ("the direction reversed", "or is any push enough?"),
        ("the same vector shuffled", "or is any nudge enough?"),
    ]):
        ly = py + 104 + j * 76
        d.ellipse((px + 26, ly - 7, px + 40, ly + 7), fill=AMBER)
        d.text((px + 56, ly), name, font=font(21, bold=True), fill=INK, anchor="lm")
        d.text((px + 56, ly + 28), gloss, font=font(19, italic=True), fill=GRAY, anchor="lm")
    d.text((px + 24, py + 336), "and move more answers right than wrong.",
           font=font(19, bold=True), fill=NAVY, anchor="lm")

    note = ("No passage is chosen by hand at any point: every book enters at the top, "
            "and all narrowing is by measured behavior.")
    d.rounded_rectangle((185, h - 122, w - 185, h - 42), radius=16,
                        fill="#eef6ff", outline="#bfdbfe", width=2)
    d.text((w // 2, h - 82), note, font=font(23, bold=True), fill=NAVY, anchor="mm")

    out = FIG_DIR / "figure_1_pipeline.png"
    save_img(img, out)
    return out


def figure_2() -> Path:
    rows = read_csv("book_confirmation_l40_all_candidates.csv")
    rows.sort(key=lambda r: (r["survived"] != "yes", -float(r["positive_delta"]), r["reference"]))
    w, h = 1800, 1180
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    title(d, "Figure 2. Book Confirmation", "Limit-40 retest of 19 preliminary book candidates; blue rows are the seven survivors", w)
    left, right, top, bottom = 260, 1660, 185, 1060
    min_x, max_x = 0.34, 0.46
    def sx(v: float) -> int:
        return int(left + (v - min_x) / (max_x - min_x) * (right - left))
    for tick in [0.35, 0.375, 0.40, 0.425, 0.45]:
        x = sx(tick)
        d.line((x, top, x, bottom), fill="#e2e8f0", width=2)
        d.text((x, bottom + 18), f"{tick:.3f}".rstrip("0").rstrip("."), font=font(20), fill=GRAY, anchor="ma")
    d.line((sx(0.4), top, sx(0.4), bottom), fill="#334155", width=3)
    n = len(rows)
    row_h = (bottom - top) / n
    for i, r in enumerate(rows):
        y = int(top + row_h * (i + 0.5))
        survived = r["survived"] == "yes"
        color = BLUE if survived else "#94a3b8"
        label_color = NAVY if survived else GRAY
        d.text((left - 22, y), r["reference"], font=font(21, bold=survived), fill=label_color, anchor="rm")
        c = sx(float(r["control_accuracy"]))
        p = sx(float(r["positive_accuracy"]))
        d.line((c, y, p, y), fill=color, width=5 if survived else 3)
        d.ellipse((c - 7, y - 7, c + 7, y + 7), fill="white", outline="#475569", width=3)
        d.ellipse((p - 10, y - 10, p + 10, y + 10), fill=color, outline=color)
        if survived:
            d.text((p + 18, y), "+", font=font(22, bold=True), fill=color, anchor="lm")
    d.text((sx(0.4), top - 25), "control baseline", font=font(20, bold=True), fill="#334155", anchor="ma")
    out = FIG_DIR / "figure_2_book_confirmation.png"
    save_img(img, out)
    return out


def figure_3() -> Path:
    disc = read_csv("chapter_discovery_l10_clean_hits.csv")
    conf = read_csv("chapter_confirmation_l40_survivors.csv")
    books = ["Acts", "Hebrews", "Numbers", "1 Chronicles", "Judges", "Amos", "Deuteronomy"]
    disc_counts = {b: 0 for b in books}
    conf_counts = {b: 0 for b in books}
    for r in disc:
        disc_counts[r["book"]] = disc_counts.get(r["book"], 0) + 1
    for r in conf:
        conf_counts[r["book"]] = conf_counts.get(r["book"], 0) + 1
    w, h = 1600, 950
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    title(d, "Figure 3. Chapter Hits by Confirmed Book", "Preliminary chapter hits and limit-40 survivors by source book", w)
    left, right, top, bottom = 180, 1490, 190, 790
    max_v = max(disc_counts.values())
    for tick in range(0, max_v + 2, 2):
        y = int(bottom - tick / (max_v + 1) * (bottom - top))
        d.line((left, y, right, y), fill="#e2e8f0", width=2)
        d.text((left - 20, y), str(tick), font=font(20), fill=GRAY, anchor="rm")
    group_w = (right - left) / len(books)
    for i, b in enumerate(books):
        x0 = int(left + i * group_w + 28)
        base = bottom
        bw = 46
        for j, (value, color, label) in enumerate([(disc_counts[b], "#93c5fd", "prelim"), (conf_counts[b], BLUE, "confirmed")]):
            x = x0 + j * (bw + 14)
            y = int(bottom - value / (max_v + 1) * (bottom - top))
            d.rounded_rectangle((x, y, x + bw, base), radius=8, fill=color)
            d.text((x + bw / 2, y - 16), str(value), font=font(21, bold=True), fill=NAVY, anchor="ma")
        lines = wrap_text(d, b, font(21, bold=True), int(group_w - 18))
        y_label = bottom + 35
        for line in lines:
            d.text((x0 + 50, y_label), line, font=font(21, bold=True), fill=NAVY, anchor="ma")
            y_label += 25
    d.rounded_rectangle((1160, 130, 1490, 220), radius=12, fill="white", outline="#cbd5e1")
    d.rectangle((1190, 158, 1225, 188), fill="#93c5fd")
    d.text((1240, 173), "preliminary hits", font=font(21), fill=NAVY, anchor="lm")
    d.rectangle((1190, 193, 1225, 223), fill=BLUE)
    d.text((1240, 208), "confirmed movers", font=font(21), fill=NAVY, anchor="lm")
    out = FIG_DIR / "figure_3_chapter_hits_by_book.png"
    save_img(img, out)
    return out


def heat_color(v: int, max_v: int = 13) -> str:
    if v <= 0:
        return "#f8fafc"
    # Blend from pale blue to navy.
    t = v / max_v
    r1, g1, b1 = (219, 234, 254)
    r2, g2, b2 = (30, 64, 175)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def figure_4() -> Path:
    rows = read_csv("layer_alpha_expected_grid.csv")
    vals = {(int(r["center_layer"]), int(float(r["alpha"]))): int(r["paired_rescues"]) for r in rows}
    centers = [24, 28, 29, 30, 31, 32, 33, 36]
    alphas = [16, 24, 32, 48, 64, 96]
    w, h = 1400, 950
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    title(d, "Figure 4. Layer/α Rescue Heatmap", "Cell value is paired rescues out of 16 confirmed chapter vectors", w)
    left, top = 250, 245
    cell_w, cell_h = 145, 78
    d.text((left + len(alphas) * cell_w / 2, top - 84), "Runtime α", font=font(25, bold=True), fill=NAVY, anchor="ma")
    for j, a in enumerate(alphas):
        d.text((left + j * cell_w + cell_w / 2, top - 25), str(a), font=font(24, bold=True), fill=NAVY, anchor="ma")
    d.text((115, top + len(centers) * cell_h / 2), "Center layer", font=font(25, bold=True), fill=NAVY, anchor="mm")
    for i, c in enumerate(centers):
        y = top + i * cell_h
        d.text((left - 35, y + cell_h / 2), str(c), font=font(24, bold=True), fill=NAVY, anchor="rm")
        for j, a in enumerate(alphas):
            x = left + j * cell_w
            if (c, a) in vals:
                v = vals[(c, a)]
                fill = heat_color(v)
                d.rounded_rectangle((x + 4, y + 4, x + cell_w - 4, y + cell_h - 4), radius=10, fill=fill, outline="#cbd5e1")
                txt = f"{v}/16"
                txt_color = "white" if v >= 9 else NAVY
                d.text((x + cell_w / 2, y + cell_h / 2), txt, font=font(27, bold=True), fill=txt_color, anchor="mm")
                if (c, a) in [(30, 96), (31, 96), (28, 16), (24, 32)]:
                    d.rounded_rectangle((x + 1, y + 1, x + cell_w - 1, y + cell_h - 1), radius=12, outline=AMBER, width=5)
            else:
                d.rounded_rectangle((x + 4, y + 4, x + cell_w - 4, y + cell_h - 4), radius=10, fill="#f1f5f9", outline="#e2e8f0")
                d.text((x + cell_w / 2, y + cell_h / 2), "not run", font=font(18), fill="#94a3b8", anchor="mm")
    out = FIG_DIR / "figure_4_layer_alpha_heatmap.png"
    save_img(img, out)
    return out


def figure_5() -> Path:
    rows = read_csv("layer_alpha_cells.csv")
    values = {
        (int(r["center_layer"]), int(float(r["alpha"]))): int(r["paired_rescues"])
        for r in rows
    }
    layers = [24, 28, 30, 31, 32, 33]
    alphas = [16, 24, 32, 48, 64, 96]
    colors = {
        24: AMBER,
        28: TEAL,
        30: BLUE,
        31: NAVY,
        32: GREEN,
        33: "#7c3aed",
    }
    w, h = 1650, 980
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    title(d, "Figure 5. Alpha Trajectories by Layer", "Different layers respond to steering strength in different ways", w)
    left, right, top, bottom = 190, 1375, 190, 790
    max_y = 13
    def sx(alpha: int) -> int:
        return int(left + (alphas.index(alpha) / (len(alphas) - 1)) * (right - left))
    def sy(v: int) -> int:
        return int(bottom - v / max_y * (bottom - top))
    for tick in [0, 3, 6, 9, 12, 13]:
        y = sy(tick)
        d.line((left, y, right, y), fill="#e2e8f0", width=2)
        d.text((left - 18, y), str(tick), font=font(20), fill=GRAY, anchor="rm")
    for a in alphas:
        x = sx(a)
        d.line((x, top, x, bottom), fill="#eef2f7", width=2)
        d.text((x, bottom + 24), str(a), font=font(21, bold=True), fill=NAVY, anchor="ma")
    axis(d, left, bottom, right, top)
    d.text(((left + right) / 2, bottom + 72), "Runtime α", font=font(24, bold=True), fill=NAVY, anchor="ma")
    d.text((left, top - 36), "Paired rescues out of 16", font=font(24, bold=True), fill=NAVY, anchor="la")
    for layer in layers:
        pts = [(sx(a), sy(values.get((layer, a), 0))) for a in alphas]
        color = colors[layer]
        d.line(pts, fill=color, width=5)
        for x, y in pts:
            d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=color, outline="white", width=3)
        lx, ly = pts[-1]
        d.text((lx + 16, ly), f"L{layer}", font=font(22, bold=True), fill=color, anchor="lm")
    note = "L24 spikes then collapses; L28 is strongest at gentle α; L30 rises into the broadest high-α rescue."
    d.rounded_rectangle((185, 845, 1465, 920), radius=16, fill="#eef6ff", outline="#bfdbfe", width=2)
    d.text((220, 882), note, font=font(24, bold=True), fill=NAVY, anchor="lm")
    out = FIG_DIR / "figure_5_alpha_trajectories.png"
    save_img(img, out)
    return out


BOOK_COLORS = {
    "Acts": BLUE,
    "Hebrews": TEAL,
    "Numbers": AMBER,
    "1 Chronicles": GREEN,
    "Judges": "#7c3aed",
    "Deuteronomy": RED,
}


def figure_6() -> Path:
    rows = read_csv("chapter_stability_by_localization.csv")
    w, h = 1500, 1120
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    title(d, "Figure 6. Chapter Stability Across Localization Cells", "Number of completed layer/α cells in which each chapter was rescued", w)
    left, right, top, bottom = 350, 1360, 180, 1020
    max_v = 43
    for tick in [0, 10, 20, 30, 40, 43]:
        x = int(left + tick / max_v * (right - left))
        d.line((x, top, x, bottom), fill="#e2e8f0", width=2)
        d.text((x, bottom + 18), str(tick), font=font(20), fill=GRAY, anchor="ma")
    row_h = (bottom - top) / len(rows)
    for i, r in enumerate(rows):
        y = int(top + row_h * i + row_h * 0.5)
        val = int(r["paired_rescue_count"])
        x = int(left + val / max_v * (right - left))
        color = BOOK_COLORS.get(r["book"], BLUE)
        d.text((left - 22, y), r["reference"], font=font(23, bold=i < 4), fill=NAVY, anchor="rm")
        d.rounded_rectangle((left, y - 13, x, y + 13), radius=9, fill=color)
        d.text((x + 14, y), str(val), font=font(22, bold=True), fill=NAVY, anchor="lm")
    out = FIG_DIR / "figure_6_chapter_stability.png"
    save_img(img, out)
    return out


def figure_7() -> Path:
    rows = read_csv("chapter_x_layer_alpha_rescue_matrix.csv")
    headers = [h for h in rows[0].keys() if h.startswith("L")]
    w, h = 2600, 1280
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    title(d, "Figure 7. Chapter × Layer/α Rescue Matrix", "Blue cells mark a paired rescue for that chapter at that layer and steering strength", w)
    left, top = 390, 230
    cell_w, cell_h = 49, 47
    for j, head in enumerate(headers):
        x = left + j * cell_w + cell_w / 2
        layer, alpha = head[1:].split("_a")
        d.text((x, top - 67), f"L{layer}", font=font(13, bold=True), fill=NAVY, anchor="ma")
        d.text((x, top - 43), f"α{int(alpha)}", font=font(12), fill=GRAY, anchor="ma")
    last_layer = None
    for j, head in enumerate(headers):
        layer = head[1:].split("_a")[0]
        if last_layer is not None and layer != last_layer:
            x = left + j * cell_w
            d.line((x, top - 80, x, top + len(rows) * cell_h), fill="#94a3b8", width=3)
        last_layer = layer
    for i, r in enumerate(rows):
        y = top + i * cell_h
        d.text((left - 24, y + cell_h / 2), r["reference"], font=font(22, bold=i < 4), fill=NAVY, anchor="rm")
        for j, head in enumerate(headers):
            x = left + j * cell_w
            v = r[head] == "1"
            fill = BLUE if v else "#f8fafc"
            outline = "#cbd5e1"
            d.rectangle((x + 4, y + 4, x + cell_w - 4, y + cell_h - 4), fill=fill, outline=outline)
    out = FIG_DIR / "figure_7_rescue_matrix.png"
    save_img(img, out)
    return out


def build_figures() -> dict[str, Path]:
    for stale in FIG_DIR.glob("figure_*.png"):
        stale.unlink()
    figs = {
        "Figure 1": figure_1(),
        "Figure 2": figure_2(),
        "Figure 3": figure_3(),
        "Figure 4": figure_4(),
        "Figure 5": figure_5(),
        "Figure 6": figure_6(),
        "Figure 7": figure_7(),
    }
    build_contact_sheet(list(figs.values()))
    return figs


def build_contact_sheet(paths: list[Path]) -> None:
    thumb_w, thumb_h = 520, 360
    pad, label_h = 34, 42
    cols = 2
    rows = math.ceil(len(paths) / cols)
    img = Image.new("RGB", (cols * thumb_w + (cols + 1) * pad, rows * (thumb_h + label_h) + (rows + 1) * pad), PAPER)
    d = ImageDraw.Draw(img)
    for idx, path in enumerate(paths):
        thumb = Image.open(path).convert("RGB")
        thumb.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        col = idx % cols
        row = idx // cols
        x0 = pad + col * (thumb_w + pad)
        y0 = pad + row * (thumb_h + label_h + pad)
        x = x0 + (thumb_w - thumb.width) // 2
        img.paste(thumb, (x, y0))
        label = path.stem.replace("_", " ")
        d.text((x0, y0 + thumb_h + 8), label, font=font(24, bold=True), fill=NAVY)
    save_img(img, FIG_DIR / "figures_contact_sheet.png")


def table_1_rows() -> list[list[str]]:
    return [
        ["Stage", "Input", "Slice", "α", "Controls", "Output"],
        ["Book discovery", "66 biblical books", "Justice ratio, limit 10", "32", "control, +Scripture, -α, null", "19 book candidates"],
        ["Book confirmation", "19 book candidates", "Justice ratio, limit 40", "32", "same four-condition battery", "7 confirmed book sources"],
        ["Chapter discovery", "170 chapters from confirmed books", "Justice ratio, limit 10", "32", "same four-condition battery", "38 preliminary chapter hits"],
        ["Chapter confirmation", "38 chapter hits", "Justice ratio, limit 40", "32", "same four-condition battery", "16 confirmed chapter movers"],
        ["Layer/α localization", "16 confirmed chapter movers", "Justice ratio, limit 10", "16-96", "same four-condition battery", "43 completed behavior cells"],
    ]


def parse_md_table(block: str) -> list[list[str]]:
    """Parse a GitHub-flavoured markdown table into a list of cell rows."""
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue  # alignment row
        rows.append(cells)
    return rows


def existing_motifs() -> dict[str, str]:
    """Read the motif column out of the paper's current Table 3 block.

    The motifs are prose belonging to the paper, so the paper -- not a
    side-car scaffolding file -- is where they live. Refreshing the table
    recomputes every measured column and carries the motifs through.
    """
    md = PAPER_MD.read_text()
    rows = parse_md_table(extract_table3_block(md))
    return {r[0]: r[-1] for r in rows[1:] if len(r) >= 2}


def table_3_rows() -> list[list[str]]:
    """Build Table 3 from the curated CSVs, ranked by localization stability."""
    conf = {r["target"]: r for r in read_csv("chapter_confirmation_l40_survivors.csv")}
    stab = read_csv("chapter_stability_by_localization.csv")
    motifs = existing_motifs()
    rows = [[
        "Chapter",
        "Limit-40 confirmation (control → +Scripture)",
        "Δ",
        "Localization stability",
        "Peak-accuracy cell",
        "Biblical justice motif",
    ]]
    for r in stab:
        c = conf[r["target"]]
        rows.append([
            r["reference"],
            f"{c['control_accuracy']} → {c['positive_accuracy']}",
            c["positive_delta"],
            f"{r['paired_rescue_count']}/43",
            f"L{r['best_center_layer']} / α{r['best_alpha']}",
            motifs.get(r["reference"], ""),
        ])
    return rows


def extract_table3_block(md: str) -> str:
    start = md.index(TABLE3_BEGIN)
    start = md.index("\n", start) + 1
    return md[start:md.index(TABLE3_END)]


def refresh_table_3() -> None:
    """Regenerate the Table 3 block inside the paper markdown, in place."""
    rows = table_3_rows()
    aligns = ["---", "---", "---:", "---:", "---", "---"]
    lines = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(aligns) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    md = PAPER_MD.read_text()
    head = md[:md.index("\n", md.index(TABLE3_BEGIN)) + 1]
    tail = md[md.index(TABLE3_END):]
    PAPER_MD.write_text(head + "\n".join(lines) + "\n" + tail)
    print(f"refreshed Table 3 ({len(rows) - 1} chapters) in {PAPER_MD.relative_to(ROOT)}")


def add_table(doc: Document, rows: list[list[str]], widths: list[float], font_size: float = 8.5) -> None:
    table = doc.add_table(rows=0, cols=len(rows[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        for ci, txt in enumerate(row):
            cell = cells[ci]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=100, start=105, bottom=100, end=105)
            if ri == 0:
                shade_cell(cell, "EAF2FF")
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci in [2, 3] else WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(txt)
            run.font.name = "Times New Roman"
            run.font.size = Pt(font_size)
            if ri == 0:
                run.bold = True
                run.font.color.rgb = RGBColor(23, 32, 51)
            else:
                run.font.color.rgb = RGBColor(31, 41, 55)
            cell.width = Inches(widths[ci])
    doc.add_paragraph()


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in("w:tcMar")
    if tcMar is None:
        tcMar = OxmlElement("w:tcMar")
        tcPr.append(tcMar)
    for m, v in [("top", top), ("start", start), ("bottom", bottom), ("end", end)]:
        node = tcMar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tcMar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def shade_cell(cell, fill: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcPr.append(shd)
    shd.set(qn("w:fill"), fill)


def add_caption(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.italic = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(71, 85, 105)


def add_inline_runs(paragraph, text: str) -> None:
    # Conservative inline markdown support for paper prose.
    pattern = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            run = paragraph.add_run(text[pos:m.start()])
            format_run(run)
        token = m.group(0)
        content = token.strip("*`")
        run = paragraph.add_run(content)
        format_run(run)
        if token.startswith("**"):
            run.bold = True
        elif token.startswith("*"):
            run.italic = True
        elif token.startswith("`"):
            run.font.name = "Courier New"
        pos = m.end()
    if pos < len(text):
        run = paragraph.add_run(text[pos:])
        format_run(run)


def format_run(run) -> None:
    run.font.name = "Times New Roman"
    run.font.size = Pt(10.5)
    run.font.color.rgb = RGBColor(31, 41, 55)


def set_styles(doc: Document) -> None:
    styles = doc.styles
    styles["Normal"].font.name = "Times New Roman"
    styles["Normal"].font.size = Pt(10.5)
    styles["Title"].font.name = "Times New Roman"
    styles["Title"].font.size = Pt(20)
    styles["Title"].font.bold = True
    for name, size in [("Heading 1", 15), ("Heading 2", 13), ("Heading 3", 11)]:
        styles[name].font.name = "Times New Roman"
        styles[name].font.size = Pt(size)
        styles[name].font.bold = True
        styles[name].font.color.rgb = RGBColor(23, 32, 51)


def add_header_footer(doc: Document) -> None:
    section = doc.sections[0]
    header = section.header
    p = header.paragraphs[0]
    p.text = "ScriptureVec Justice Paper"
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.runs[0].font.name = "Times New Roman"
    p.runs[0].font.size = Pt(8.5)
    p.runs[0].font.color.rgb = RGBColor(100, 116, 139)
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.text = "Draft generated from completed ScriptureVec Justice result packet"
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.runs[0].font.name = "Times New Roman"
    fp.runs[0].font.size = Pt(8)
    fp.runs[0].font.color.rgb = RGBColor(100, 116, 139)


def make_docx(md: str, figs: dict[str, Path]) -> None:
    if not HAVE_DOCX:
        raise SystemExit(
            "python-docx is required for the DOCX export.\n"
            "  pip install -r requirements.txt   (or: pip install python-docx)\n"
            "Use --figures-only to rebuild just the figures without it."
        )
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.82)
    section.right_margin = Inches(0.82)
    set_styles(doc)
    add_header_footer(doc)

    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped == "---":
            doc.add_paragraph()
            i += 1
            continue
        if stripped.startswith("# "):
            p = doc.add_paragraph(style="Title")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_inline_runs(p, stripped[2:].strip())
        elif stripped.startswith("## "):
            doc.add_paragraph(clean_md_inline(stripped[3:].strip()), style="Heading 1")
        elif stripped.startswith("### "):
            doc.add_paragraph(clean_md_inline(stripped[4:].strip()), style="Heading 2")
        elif stripped.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.35)
            p.paragraph_format.right_indent = Inches(0.35)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(8)
            r = p.add_run(clean_md_inline(stripped[2:].strip()))
            format_run(r)
            r.italic = True
            r.font.color.rgb = RGBColor(71, 85, 105)
        elif stripped.startswith("<!--"):
            i += 1
            continue  # generation markers are markdown-only
        elif stripped.startswith("!["):
            # ![caption](relative/path.png) -- render the image, caption beneath
            match = re.match(r"!\[(.*)\]\((.+)\)$", stripped)
            if match:
                caption, rel = match.group(1), match.group(2)
                img = (PAPER_MD.parent / rel).resolve()
                if img.exists():
                    doc.add_picture(str(img), width=Inches(6.85))
                    add_caption(doc, clean_md_inline(caption))
                else:
                    print(f"  warning: missing figure {rel}")
        elif stripped.startswith("|"):
            # consume a whole markdown table and render it as a real docx table
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            rows = parse_md_table("\n".join(block))
            if rows:
                ncols = len(rows[0])
                # last column of Table 2 is long prose; give it the slack
                widths = ([0.95, 1.35, 0.5, 0.85, 0.95, 2.35] if ncols == 6
                          else [6.9 / ncols] * ncols)
                add_table(doc, rows, widths, font_size=7.6 if ncols >= 6 else 8.3)
            continue
        elif stripped.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline_runs(p, stripped[2:].strip())
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            add_inline_runs(p, stripped)
        i += 1
    PAPER_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(PAPER_DOCX)


# Strips the `alt=` attribute pandoc emits on \includegraphics, which older
# graphicx releases reject, and keeps the markdown caption as body text.
# Rendered with `-f markdown-implicit_figures`, so a lone `![cap](img)` stays a
# paragraph holding an Image rather than becoming a LaTeX float. This filter
# splits it into the image followed by its caption as italic body text. Two
# reasons: our markdown captions already carry their own "Figure N." numbering
# (so LaTeX's would double it), and an image with no caption emits no `alt=`
# attribute -- which older graphicx releases reject outright. It also keeps each
# figure where the prose puts it instead of floating onto a page of its own.
PANDOC_IMAGE_FILTER = """\
function Para(el)
  if #el.content == 1 and el.content[1].t == "Image" then
    local img = el.content[1]
    local caption = img.caption
    img.caption = {}
    img.attributes = pandoc.AttributeList{}
    if caption and #caption > 0 then
      return {pandoc.Para{img}, pandoc.Para{pandoc.Emph(caption)}}
    end
    return pandoc.Para{img}
  end
end

-- Pandoc infers LaTeX column widths from how wide each cell is in the markdown
-- source, which starves Table 2's long motif column. Set the widths explicitly.
local WIDTHS = {
  [6] = {0.10, 0.15, 0.05, 0.10, 0.11, 0.49},  -- Table 2 (ranked inventory)
  [5] = {0.14, 0.22, 0.16, 0.08, 0.40},        -- Table 1 (pipeline design)
}

function Table(el)
  local widths = WIDTHS[#el.colspecs]
  if widths then
    for i, spec in ipairs(el.colspecs) do
      spec[2] = widths[i]
    end
  end
  return el
end
"""


def make_pdf() -> bool:
    """Render the canonical markdown to PDF via pandoc + xelatex.

    Returns False (without raising) when the toolchain is unavailable, so the
    figure and DOCX steps still succeed on a machine without LaTeX.
    """
    if not (shutil.which("pandoc") and shutil.which("xelatex")):
        return False
    with tempfile.TemporaryDirectory() as tmp:
        lua = Path(tmp) / "inline_figures.lua"
        lua.write_text(PANDOC_IMAGE_FILTER)
        cmd = [
            "pandoc",
            PAPER_MD.name,
            "-o", str(PAPER_PDF),
            "--pdf-engine=xelatex",
            "-f", "markdown-implicit_figures",
            f"--lua-filter={lua}",
            "-V", "geometry:margin=1in",
            "-V", "colorlinks=true",
            # Times New Roman is the only widely available macOS/Windows face
            # that covers the paper's Greek, polytonic accents, and math signs.
            "-V", "mainfont=Times New Roman",
        ]
        result = subprocess.run(cmd, cwd=PAPER_MD.parent, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr.strip()[:2000])
        return False
    for line in result.stderr.splitlines():
        if "Missing character" in line:
            print(f"  warning: {line.strip()}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Render the ScriptureVec Justice paper: rebuild Figures 1-7 from the "
            "curated CSVs and export the DOCX from the canonical markdown."
        )
    )
    parser.add_argument(
        "--refresh-tables",
        action="store_true",
        help="regenerate the generated Table 3 block inside the paper markdown from the CSVs",
    )
    parser.add_argument(
        "--figures-only",
        action="store_true",
        help="rebuild figures and skip the DOCX export (no python-docx needed)",
    )
    args = parser.parse_args()

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    refresh_localization_key_data()

    if args.refresh_tables:
        refresh_table_3()

    figs = build_figures()
    print(f"wrote {len(figs)} figures to {FIG_DIR.relative_to(ROOT)}")

    if args.figures_only:
        return

    make_docx(PAPER_MD.read_text(), figs)
    print(f"wrote {PAPER_DOCX.relative_to(ROOT)}")

    if make_pdf():
        print(f"wrote {PAPER_PDF.relative_to(ROOT)}")
    else:
        print(
            "skipped PDF: needs pandoc + a LaTeX engine (xelatex) on PATH. "
            "Install both, or export paper/*.docx to PDF from Word/LibreOffice."
        )


if __name__ == "__main__":
    main()
