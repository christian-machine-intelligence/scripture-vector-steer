"""Filter an external Scripture corpus to a locked target set."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _load_targets(path: Path) -> list[str]:
    targets: list[str] = []
    seen: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        target = raw_line.strip()
        if not target or target.startswith("#"):
            continue
        if target in seen:
            raise ValueError(f"Duplicate target in {path}: {target}")
        targets.append(target)
        seen.add(target)
    if not targets:
        raise ValueError(f"No targets found in {path}")
    return targets


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(row)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def _write_manifest(path: Path, *, source: Path, target_file: Path, rows: list[dict[str, Any]], targets: list[str]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["target"])].append(row)

    target_payload: dict[str, dict[str, Any]] = {}
    for target in targets:
        target_rows = grouped[target]
        books = sorted({str(row.get("book")) for row in target_rows if row.get("book")})
        book_ids = sorted({str(row.get("book_id")) for row in target_rows if row.get("book_id")})
        chapters = sorted({int(row["chapter"]) for row in target_rows if "chapter" in row})
        verse_spans = [
            {
                "source": row.get("source"),
                "verse_start": row.get("verse_start"),
                "verse_end": row.get("verse_end"),
            }
            for row in target_rows
        ]
        target_payload[target] = {
            "rows": len(target_rows),
            "books": books,
            "book_ids": book_ids,
            "chapters": chapters,
            "verse_spans": verse_spans,
        }

    payload = {
        "source_corpus": str(source),
        "target_file": str(target_file),
        "target_count": len(targets),
        "row_count": len(rows),
        "targets": target_payload,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-corpus", type=Path, required=True)
    parser.add_argument("--targets-file", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manifest-out", type=Path, required=True)
    args = parser.parse_args()

    targets = _load_targets(args.targets_file)
    wanted = set(targets)
    rows = _load_jsonl(args.in_corpus)
    filtered = [row for row in rows if str(row.get("target")) in wanted]

    found = {str(row.get("target")) for row in filtered}
    missing = [target for target in targets if target not in found]
    if missing:
        raise ValueError(f"Missing targets in {args.in_corpus}: {', '.join(missing)}")

    filtered.sort(key=lambda row: (targets.index(str(row["target"])), int(row.get("verse_start") or 0)))
    _write_jsonl(args.out, filtered)
    _write_manifest(
        args.manifest_out,
        source=args.in_corpus,
        target_file=args.targets_file,
        rows=filtered,
        targets=targets,
    )
    print(f"Wrote {len(filtered)} rows across {len(targets)} targets to {args.out}")


if __name__ == "__main__":
    main()
