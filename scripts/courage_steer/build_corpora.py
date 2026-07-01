#!/usr/bin/env python3
"""Materialize the FROZEN courage-study corpora from data/bible_kjv.json.

Produces two JSONL corpora (format: {"corpus": <target>, "text": <passage>})
consumable by `iconoclast --external-scripture-corpus`:

  data/courage_steer/courage_passages.jsonl
      targets: courage_pool, courage_reassurance, courage_defiance
  data/courage_steer/whole_bible.jsonl
      target : whole_bible   (evenly sampled across all 66 books)

The pericope list below is FROZEN (plan Appendix A). Do not edit after the
pre-registration commit. Book references use the stable 3-letter `id`.

Parity rule (documented): the 22 imprecatory psalms are LONG and would swamp a
pooled "courage" average, so they belong ONLY to the defiance pole, NOT to
courage_pool. courage_pool = reassurance pericopes + Psalm 23 + defiance
*narrative* pericopes.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIBLE = ROOT / "data" / "bible_kjv.json"
OUT_DIR = ROOT / "data" / "courage_steer"

# (book_id, chapter, verse_start, verse_end) — verse_end=None means whole chapter
Ref = tuple

REASSURANCE = [
    ("DEU", 31, 1, 8), ("JOS", 1, 1, 9), ("1CH", 28, 9, 20), ("2CH", 32, 1, 8),
    ("PSA", 27, None, None), ("PSA", 46, None, None), ("PSA", 56, None, None),
    ("PSA", 118, 5, 14), ("ISA", 41, 8, 13), ("ISA", 43, 1, 7),
    ("MAT", 10, 26, 33), ("JHN", 14, 25, 31), ("JHN", 16, 31, 33),
    ("2TI", 1, 6, 14), ("HEB", 13, 1, 6), ("1PE", 3, 13, 17),
]
DEFIANCE_NARRATIVE = [
    ("1SA", 17, 32, 51), ("DAN", 3, 13, 30), ("DAN", 6, 10, 23),
    ("EST", 4, 10, 17), ("NEH", 6, 1, 16), ("2SA", 10, 8, 14),
    ("1CO", 16, 13, 14), ("EPH", 6, 10, 20), ("ACT", 4, 8, 31),
    ("ACT", 5, 27, 42), ("ACT", 7, 51, 60), ("ACT", 21, 10, 14),
    ("PHP", 1, 18, 26), ("HEB", 11, 32, 40), ("HEB", 12, 1, 4),
    ("LUK", 22, 39, 46), ("REV", 2, 8, 11), ("REV", 12, 10, 11),
]
PSALM_23 = ("PSA", 23, None, None)
IMPRECATORY = [("PSA", n, None, None) for n in
               (5, 6, 10, 12, 35, 37, 40, 52, 54, 55, 56, 57, 58, 59,
                69, 79, 83, 94, 109, 137, 139, 143)]

WHOLE_BIBLE_CHAPTERS_PER_BOOK = 3  # evenly spaced sample per book


def build_index(bible):
    idx = {}
    for b in bible["books"]:
        bid = b["id"]
        for ch in b["chapters"]:
            idx[(bid, ch["chapter"])] = {v["verse"]: v["text"] for v in ch["verses"]}
    return idx


def passage_text(idx, ref):
    bid, ch, vs, ve = ref
    verses = idx.get((bid, ch))
    if verses is None:
        raise KeyError(f"missing {bid} {ch}")
    keys = sorted(verses)
    if vs is None:
        chosen = keys
    else:
        chosen = [v for v in keys if vs <= v <= ve]
    if not chosen:
        raise KeyError(f"no verses for {ref}")
    return " ".join(verses[v].strip() for v in chosen)


def ref_label(ref):
    bid, ch, vs, ve = ref
    return f"{bid} {ch}" if vs is None else f"{bid} {ch}:{vs}-{ve}"


def main():
    bible = json.load(open(BIBLE))
    idx = build_index(bible)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- courage_passages.jsonl ----
    records = []

    def add(ref, targets):
        text = passage_text(idx, ref)
        for t in targets:
            records.append({"corpus": t, "text": text, "ref": ref_label(ref)})

    for ref in REASSURANCE:
        add(ref, ["courage_reassurance", "courage_pool"])
    add(PSALM_23, ["courage_reassurance", "courage_pool"])
    for ref in DEFIANCE_NARRATIVE:
        add(ref, ["courage_defiance", "courage_pool"])
    for ref in IMPRECATORY:
        add(ref, ["courage_defiance"])  # parity rule: NOT in pool

    cp = OUT_DIR / "courage_passages.jsonl"
    with open(cp, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # ---- whole_bible.jsonl (evenly sampled chapters per book) ----
    wb = OUT_DIR / "whole_bible.jsonl"
    n_wb = 0
    with open(wb, "w") as f:
        for b in bible["books"]:
            chs = [c["chapter"] for c in b["chapters"]]
            k = min(WHOLE_BIBLE_CHAPTERS_PER_BOOK, len(chs))
            # evenly spaced indices across the book
            picks = [chs[round(i * (len(chs) - 1) / max(1, k - 1))] for i in range(k)] if k > 1 else [chs[0]]
            picks = sorted(set(picks))
            for ch in picks:
                text = passage_text(idx, (b["id"], ch, None, None))
                f.write(json.dumps({"corpus": "whole_bible", "text": text,
                                    "ref": f"{b['id']} {ch}"}) + "\n")
                n_wb += 1

    # ---- validation summary ----
    from collections import Counter
    per_target = Counter(r["corpus"] for r in records)
    print("=== courage_passages.jsonl ===")
    for t, n in sorted(per_target.items()):
        print(f"  {t:22} {n} passages")
    print(f"=== whole_bible.jsonl ===\n  whole_bible            {n_wb} chapter-passages")
    print("\n=== spot-check: JOS 1:1-9 ===")
    print(passage_text(idx, ("JOS", 1, 1, 9))[:400], "...")
    print(f"\nwrote {cp}\nwrote {wb}")


if __name__ == "__main__":
    main()
