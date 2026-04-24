from virtue_bench.steering.corpora import (
    build_contrast_pairs,
    build_length_matched_control,
    list_steering_targets,
    load_steering_corpus,
)


def test_load_steering_corpus_has_expected_labels():
    records = load_steering_corpus()
    assert len(records) >= 120
    positive_labels = {record.virtue for record in records if record.polarity == "positive"}
    assert {
        "prudence",
        "justice",
        "courage",
        "temperance",
        "christian",
        "psalms",
        "proverbs",
        "gospels",
    }.issubset(positive_labels)


def test_list_steering_targets_includes_christian_track():
    records = load_steering_corpus()
    assert list_steering_targets(records) == [
        "prudence",
        "justice",
        "courage",
        "temperance",
        "christian",
        "psalms",
        "proverbs",
        "gospels",
    ]


def test_build_contrast_pairs_matches_positive_and_negative_records():
    records = load_steering_corpus()
    pairs = build_contrast_pairs(records, virtue="courage", split="train")

    assert len(pairs) >= 10
    assert all(pair.positive.pair_id == pair.negative.pair_id for pair in pairs)
    assert all(pair.positive.virtue == "courage" for pair in pairs)


def test_targets_share_standardized_pair_counts():
    records = load_steering_corpus()

    for virtue in ["prudence", "justice", "courage", "temperance"]:
        assert len(build_contrast_pairs(records, virtue=virtue, split="train")) == 10
        assert len(build_contrast_pairs(records, virtue=virtue, split="dev")) == 2
        assert len(build_contrast_pairs(records, virtue=virtue, split="test")) == 2

    assert len(build_contrast_pairs(records, virtue="christian", split="train")) >= 14
    assert len(build_contrast_pairs(records, virtue="christian", split="dev")) == 2
    assert len(build_contrast_pairs(records, virtue="christian", split="test")) == 2

    assert len(build_contrast_pairs(records, virtue="psalms", split="train")) == 5
    assert len(build_contrast_pairs(records, virtue="psalms", split="dev")) == 1
    assert len(build_contrast_pairs(records, virtue="psalms", split="test")) == 1

    assert len(build_contrast_pairs(records, virtue="proverbs", split="train")) == 6
    assert len(build_contrast_pairs(records, virtue="proverbs", split="dev")) == 1
    assert len(build_contrast_pairs(records, virtue="proverbs", split="test")) == 1

    assert len(build_contrast_pairs(records, virtue="gospels", split="train")) == 6
    assert len(build_contrast_pairs(records, virtue="gospels", split="dev")) == 1
    assert len(build_contrast_pairs(records, virtue="gospels", split="test")) == 1


def test_christian_track_has_broader_source_coverage():
    records = load_steering_corpus()
    christian_train = build_contrast_pairs(records, virtue="christian", split="train")
    sources = {pair.positive.source for pair in christian_train}

    assert any("Psalm" in source for source in sources)
    assert any("Proverbs" in source for source in sources)
    assert any(source.startswith(("Matthew", "Mark", "Luke", "John")) for source in sources)


def test_scripture_family_tracks_are_derived_from_christian_pairs():
    records = load_steering_corpus()

    psalm_sources = {pair.positive.source for pair in build_contrast_pairs(records, virtue="psalms", split="train")}
    proverb_sources = {pair.positive.source for pair in build_contrast_pairs(records, virtue="proverbs", split="train")}
    gospel_sources = {pair.positive.source for pair in build_contrast_pairs(records, virtue="gospels", split="train")}

    assert all(source.startswith("Psalm") for source in psalm_sources)
    assert all(source.startswith("Proverbs") for source in proverb_sources)
    assert all(source.startswith(("Matthew", "Mark", "Luke", "John")) for source in gospel_sources)


def test_build_length_matched_control_reaches_reference_length():
    records = load_steering_corpus()
    neutral = [record for record in records if record.virtue == "neutral"]
    reference = "Psalm 23\nThe Lord is my shepherd; I shall not want."
    control = build_length_matched_control(reference, neutral)

    assert len(control) >= len(reference)
    assert "observatory" in control.lower() or "gardener" in control.lower()
