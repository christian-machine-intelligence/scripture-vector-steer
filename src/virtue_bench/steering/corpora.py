"""Bundled virtue corpora and prompt controls for activation steering."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


CORPUS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "steering" / "corpora.jsonl"
DEFAULT_VIRTUE_TARGETS = ["prudence", "justice", "courage", "temperance"]
POOLED_VIRTUE_TARGET = "virtues"
SCRIPTURE_FAMILY_TARGETS = ["psalms", "proverbs", "gospels"]


@dataclass(frozen=True)
class SteeringText:
    """A labeled text snippet used for vector extraction or control prompts."""

    text_id: str
    virtue: str
    polarity: str
    split: str
    source: str
    text: str
    pair_id: Optional[str] = None


@dataclass(frozen=True)
class SteeringPair:
    """A matched positive/negative pair for contrastive steering extraction."""

    pair_id: str
    virtue: str
    split: str
    positive: SteeringText
    negative: SteeringText


_PAIR_SUFFIX_RE = re.compile(r"-(\d+)$")


def classify_scripture_family(source: str) -> Optional[str]:
    """Map a biblical source label onto a scripture-family steering target."""
    if source.startswith("Psalm"):
        return "psalms"
    if source.startswith("Proverbs"):
        return "proverbs"
    if source.startswith(("Matthew", "Mark", "Luke", "John")):
        return "gospels"
    return None


def _family_split_plan(pair_ids: List[str]) -> dict[str, str]:
    """Create small, deterministic train/dev/test splits for scripture families."""
    total = len(pair_ids)
    if total <= 0:
        return {}
    if total == 1:
        return {pair_ids[0]: "train"}
    if total == 2:
        return {
            pair_ids[0]: "train",
            pair_ids[1]: "dev",
        }
    if total == 3:
        return {
            pair_ids[0]: "train",
            pair_ids[1]: "dev",
            pair_ids[2]: "test",
        }

    split_by_pair: dict[str, str] = {}
    for pair_id in pair_ids[:-2]:
        split_by_pair[pair_id] = "train"
    split_by_pair[pair_ids[-2]] = "dev"
    split_by_pair[pair_ids[-1]] = "test"
    return split_by_pair


def infer_pair_id(text_id: str) -> str:
    """Infer a lightweight pair identifier from the record id when none is supplied."""
    match = _PAIR_SUFFIX_RE.search(text_id)
    if match:
        return match.group(1)
    return text_id


def load_steering_corpus(path: Optional[Path] = None) -> List[SteeringText]:
    """Load the bundled steering corpus."""
    corpus_path = path or CORPUS_FILE
    records: List[SteeringText] = []
    raw_rows = []
    with open(corpus_path, encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            raw_rows.append(row)
            records.append(
                SteeringText(
                    text_id=row["id"],
                    virtue=row["virtue"],
                    polarity=row["polarity"],
                    split=row["split"],
                    source=row["source"],
                    text=row["text"],
                    pair_id=row.get("pair_id", infer_pair_id(row["id"])),
                )
            )

    christian_rows = [row for row in raw_rows if row["virtue"] == "christian"]
    family_by_pair: dict[str, str] = {}
    for row in christian_rows:
        if row["polarity"] != "positive":
            continue
        family = classify_scripture_family(row["source"])
        if family is None:
            continue
        pair_id = row.get("pair_id", infer_pair_id(row["id"]))
        family_by_pair[pair_id] = family

    pair_ids_by_family: dict[str, List[str]] = defaultdict(list)
    for pair_id, family in family_by_pair.items():
        pair_ids_by_family[family].append(pair_id)

    split_by_family_and_pair = {
        family: _family_split_plan(pair_ids)
        for family, pair_ids in pair_ids_by_family.items()
    }

    for row in christian_rows:
        pair_id = row.get("pair_id", infer_pair_id(row["id"]))
        family = family_by_pair.get(pair_id)
        if family is None:
            continue
        family_split = split_by_family_and_pair[family][pair_id]
        records.append(
            SteeringText(
                text_id=f"{row['id']}::{family}",
                virtue=family,
                polarity=row["polarity"],
                split=family_split,
                source=row["source"],
                text=row["text"],
                pair_id=pair_id,
            )
        )
    return records


def select_corpus_texts(
    records: Iterable[SteeringText],
    *,
    virtue: Optional[str] = None,
    polarity: Optional[str] = None,
    split: Optional[str] = None,
) -> List[SteeringText]:
    """Filter steering records by virtue, polarity, and split."""
    items = list(records)
    if virtue is not None:
        items = [item for item in items if item.virtue == virtue]
    if polarity is not None:
        items = [item for item in items if item.polarity == polarity]
    if split is not None:
        items = [item for item in items if item.split == split]
    return items


def list_steering_targets(records: Iterable[SteeringText]) -> List[str]:
    """Return non-neutral steering targets that have both positive and negative examples."""
    polarity_by_target: dict[str, set[str]] = defaultdict(set)
    ordered_targets: List[str] = []

    for item in records:
        if item.virtue == "neutral":
            continue
        polarity_by_target[item.virtue].add(item.polarity)
        if item.virtue not in ordered_targets:
            ordered_targets.append(item.virtue)

    return [
        target
        for target in ordered_targets
        if {"positive", "negative"}.issubset(polarity_by_target[target])
    ]


def pooled_virtue_members(records: Iterable[SteeringText]) -> List[str]:
    """Return the cardinal virtues available for pooled virtue extraction."""
    available = set(list_steering_targets(records))
    return [virtue for virtue in DEFAULT_VIRTUE_TARGETS if virtue in available]


def build_contrast_pairs(
    records: Iterable[SteeringText],
    *,
    virtue: str,
    split: str,
) -> List[SteeringPair]:
    """Build matched positive/negative pairs for a virtue and split."""
    grouped: dict[str, dict[str, SteeringText]] = defaultdict(dict)
    for item in select_corpus_texts(records, virtue=virtue, split=split):
        if item.polarity not in {"positive", "negative"}:
            continue
        pair_key = item.pair_id or infer_pair_id(item.text_id)
        grouped[pair_key][item.polarity] = item

    pairs: List[SteeringPair] = []
    for pair_key in sorted(grouped, key=lambda value: (len(value), value)):
        bucket = grouped[pair_key]
        positive = bucket.get("positive")
        negative = bucket.get("negative")
        if positive is None or negative is None:
            continue
        pairs.append(
            SteeringPair(
                pair_id=pair_key,
                virtue=virtue,
                split=split,
                positive=positive,
                negative=negative,
            )
        )
    return pairs


def _count_reference_units(text: str, tokenizer=None) -> int:
    if tokenizer is None:
        return len(text)
    return len(tokenizer.encode(text, add_special_tokens=False))


def build_length_matched_control(
    reference_text: str,
    neutral_records: Iterable[SteeringText],
    tokenizer=None,
) -> str:
    """Build a secular prompt control with roughly the same length as the reference text."""
    neutral_texts = [item.text for item in neutral_records]
    if not neutral_texts:
        raise ValueError("At least one neutral corpus record is required for length-matched controls.")

    target_units = max(1, _count_reference_units(reference_text, tokenizer=tokenizer))
    chunks: List[str] = []
    total_units = 0
    index = 0

    while total_units < target_units:
        chunk = neutral_texts[index % len(neutral_texts)]
        chunks.append(chunk)
        total_units += _count_reference_units(chunk, tokenizer=tokenizer)
        index += 1

    return "\n\n".join(chunks)
