"""Build external Scripture corpora for canon-wide ScriptureVec discovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections import defaultdict
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
BIBLE_PATH = REPO_ROOT / "data" / "bible_kjv.json"

CANON_GROUPS: dict[str, list[str]] = {
    "canon_torah": ["GEN", "EXO", "LEV", "NUM", "DEU"],
    "canon_history": ["JOS", "JDG", "RUT", "1SA", "2SA", "1KI", "2KI", "1CH", "2CH", "EZR", "NEH", "EST"],
    "canon_wisdom": ["JOB", "PSA", "PRO", "ECC", "SNG"],
    "canon_major_prophets": ["ISA", "JER", "LAM", "EZK", "DAN"],
    "canon_minor_prophets": ["HOS", "JOL", "AMO", "OBA", "JON", "MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL"],
    "canon_gospels": ["MAT", "MRK", "LUK", "JHN"],
    "canon_acts": ["ACT"],
    "canon_pauline": ["ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL", "1TH", "2TH", "1TI", "2TI", "TIT", "PHM"],
    "canon_general_epistles": ["HEB", "JAS", "1PE", "2PE", "1JN", "2JN", "3JN", "JUD"],
    "canon_revelation": ["REV"],
}


def _load_bible() -> list[dict]:
    with BIBLE_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["books"]


def _chapter_text(book: dict, chapter: dict) -> str:
    verses = " ".join(
        f"{verse['verse']}. {verse['text']}"
        for verse in chapter["verses"]
    )
    return f"{book['book']} {chapter['chapter']}\n{verses}"


def _iter_group_rows(books: Iterable[dict]) -> Iterable[dict]:
    group_by_book = {
        book_id: group
        for group, book_ids in CANON_GROUPS.items()
        for book_id in book_ids
    }
    for book in books:
        group = group_by_book[book["id"]]
        for chapter in book["chapters"]:
            yield {
                "corpus": group,
                "target": group,
                "source": f"{book['book']} {chapter['chapter']}",
                "book_id": book["id"],
                "book": book["book"],
                "chapter": chapter["chapter"],
                "text": _chapter_text(book, chapter),
            }


def _book_target(book_id: str) -> str:
    return f"book_{book_id.lower()}"


def _chapter_target(book_id: str, chapter_no: int) -> str:
    return f"chapter_{book_id.lower()}_{chapter_no:02d}"


def _iter_book_rows(books: Iterable[dict]) -> Iterable[dict]:
    for book in books:
        target = _book_target(book["id"])
        for chapter in book["chapters"]:
            yield {
                "corpus": target,
                "target": target,
                "source": f"{book['book']} {chapter['chapter']}",
                "book_id": book["id"],
                "book": book["book"],
                "chapter": chapter["chapter"],
                "text": _chapter_text(book, chapter),
            }


def _iter_chapter_rows(books: Iterable[dict], *, window_verses: int) -> Iterable[dict]:
    if window_verses < 1:
        raise ValueError("--chapter-window-verses must be at least 1")
    for book in books:
        for chapter in book["chapters"]:
            chapter_no = int(chapter["chapter"])
            target = _chapter_target(book["id"], chapter_no)
            verses = chapter["verses"]
            for start_index in range(0, len(verses), window_verses):
                window = verses[start_index:start_index + window_verses]
                if not window:
                    continue
                verse_start = int(window[0]["verse"])
                verse_end = int(window[-1]["verse"])
                source = f"{book['book']} {chapter_no}:{verse_start}-{verse_end}"
                verse_text = " ".join(
                    f"{verse['verse']}. {verse['text']}"
                    for verse in window
                )
                yield {
                    "corpus": target,
                    "target": target,
                    "source": source,
                    "book_id": book["id"],
                    "book": book["book"],
                    "chapter": chapter_no,
                    "verse_start": verse_start,
                    "verse_end": verse_end,
                    "text": f"{source}\n{verse_text}",
                }


def _write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")
            count += 1
    return count


def _sample_rows_by_target(rows: list[dict], max_rows_per_target: int | None) -> list[dict]:
    if max_rows_per_target is None:
        return rows
    if max_rows_per_target < 1:
        raise ValueError("--max-rows-per-target must be at least 1")

    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["target"]].append(row)

    sampled: list[dict] = []
    for target in sorted(grouped):
        target_rows = grouped[target]
        if len(target_rows) <= max_rows_per_target:
            sampled.extend(target_rows)
            continue
        if max_rows_per_target == 1:
            sampled.append(target_rows[len(target_rows) // 2])
            continue
        last_index = len(target_rows) - 1
        selected_indices = {
            round(index * last_index / (max_rows_per_target - 1))
            for index in range(max_rows_per_target)
        }
        sampled.extend(target_rows[index] for index in sorted(selected_indices))
    return sampled


def _write_manifest(path: Path, rows: list[dict], *, mode: str) -> None:
    targets: dict[str, dict] = {}
    for row in rows:
        target = row["target"]
        target_info = targets.setdefault(
            target,
            {
                "rows": 0,
                "chapters": [],
                "books": [],
                "book_ids": [],
            },
        )
        target_info["rows"] += 1
        if row["chapter"] not in target_info["chapters"]:
            target_info["chapters"].append(row["chapter"])
        if row["book"] not in target_info["books"]:
            target_info["books"].append(row["book"])
        if row["book_id"] not in target_info["book_ids"]:
            target_info["book_ids"].append(row["book_id"])
    unique_chapters = {
        (row["book_id"], row["chapter"])
        for row in rows
    }
    payload = {
        "mode": mode,
        "source": str(BIBLE_PATH.relative_to(REPO_ROOT)),
        "target_count": len(targets),
        "row_count": len(rows),
        "chapter_count": len(unique_chapters),
        "targets": targets,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _parse_book_ids(raw_book_ids: str | None) -> list[str] | None:
    if not raw_book_ids:
        return None
    return [
        item.strip().upper()
        for item in raw_book_ids.replace(" ", ",").split(",")
        if item.strip()
    ]


def _filter_books(books: list[dict], book_ids: list[str] | None) -> list[dict]:
    if book_ids is None:
        return books
    requested = set(book_ids)
    filtered = [book for book in books if book["id"] in requested]
    found = {book["id"] for book in filtered}
    missing = sorted(requested - found)
    if missing:
        raise ValueError(f"Unknown book ids: {', '.join(missing)}")
    return filtered


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["groups", "books", "chapters"],
        default="groups",
        help="Build broad canon divisions, one target per book, or one target per chapter.",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    parser.add_argument(
        "--book-ids",
        default=None,
        help="Optional comma-separated OSIS book ids to include, such as DEU,NUM,ACT,HEB.",
    )
    parser.add_argument(
        "--chapter-window-verses",
        type=int,
        default=6,
        help="For chapter mode, split each chapter into verse windows of this size.",
    )
    parser.add_argument(
        "--max-rows-per-target",
        type=int,
        default=None,
        help="Deterministically spread-sample up to this many chapter rows per target.",
    )
    args = parser.parse_args()

    books = _filter_books(_load_bible(), _parse_book_ids(args.book_ids))
    if args.mode == "groups":
        rows = list(_iter_group_rows(books))
    elif args.mode == "books":
        rows = list(_iter_book_rows(books))
    else:
        rows = list(_iter_chapter_rows(books, window_verses=args.chapter_window_verses))
    rows = _sample_rows_by_target(rows, args.max_rows_per_target)
    count = _write_jsonl(args.out, rows)
    _write_manifest(args.manifest_out, rows, mode=args.mode)
    print(f"Wrote {count} rows across {len({row['target'] for row in rows})} targets to {args.out}")


if __name__ == "__main__":
    main()
