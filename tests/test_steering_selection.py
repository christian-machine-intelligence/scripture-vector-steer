from virtue_bench.steering.extract import (
    _chunk_scripture_family_texts,
    _neutral_passage_splits,
    _pair_passage_windows,
    _passage_windows,
    _resolve_extraction_method,
    _scripture_comparison_targets,
    _split_scripture_chunks,
    _select_alpha,
    _select_layer,
    _top_candidates_within_tolerance,
    load_external_scripture_corpora,
)
from virtue_bench.steering.corpora import SteeringPair, SteeringText


def test_top_candidates_within_tolerance_keeps_near_best_scores():
    scores = {"a": 1.0, "b": 0.75, "c": 0.5}

    candidates = _top_candidates_within_tolerance(scores, 0.25)

    assert candidates == ["a", "b"]


def test_select_layer_prefers_specificity_within_one_accuracy_step():
    best_layer, selection, candidates = _select_layer(
        method_used="specific_pca_pairwise",
        layer_scores={20: 1.0, 29: 0.75, 31: 0.5},
        layer_pair_scores={20: 1.0, 29: 1.0, 31: 1.0},
        layer_specificity={20: -0.02, 29: 0.08, 31: 0.10},
        layer_margins={20: 0.04, 29: 0.03, 31: 0.02},
        midpoint=16,
        tolerance=0.25,
    )

    assert best_layer == 29
    assert selection == "specificity_within_accuracy_tolerance"
    assert candidates == [20, 29]


def test_select_alpha_prefers_larger_more_specific_candidate_within_tolerance():
    best_alpha, selection, candidates = _select_alpha(
        method_used="specific_pca_pairwise",
        alpha_scores={0.25: 1.0, 0.5: 0.75, 0.75: 0.75},
        alpha_specificity={0.25: 0.01, 0.5: 0.03, 0.75: 0.05},
        alpha_margins={0.25: 0.02, 0.5: 0.03, 0.75: 0.04},
        tolerance=0.25,
    )

    assert best_alpha == 0.75
    assert selection == "specificity_within_accuracy_tolerance"
    assert candidates == [0.25, 0.5, 0.75]


def test_passage_windows_expand_short_texts_without_changing_count():
    texts = [
        "Short prudence text one.",
        "Short prudence text two.",
        "Short prudence text three.",
    ]

    windows = _passage_windows(texts, min_words=6, max_items=2)

    assert len(windows) == len(texts)
    assert windows[0].count("\n\n") == 1


def test_pair_passage_windows_keep_positive_negative_alignment():
    pairs = [
        SteeringPair(
            pair_id="1",
            virtue="courage",
            split="train",
            positive=SteeringText("p1", "courage", "positive", "train", "src", "Short positive one.", "1"),
            negative=SteeringText("n1", "courage", "negative", "train", "src", "Short negative one.", "1"),
        ),
        SteeringPair(
            pair_id="2",
            virtue="courage",
            split="train",
            positive=SteeringText("p2", "courage", "positive", "train", "src", "Short positive two.", "2"),
            negative=SteeringText("n2", "courage", "negative", "train", "src", "Short negative two.", "2"),
        ),
    ]

    positive, negative = _pair_passage_windows(pairs, min_words=6, max_items=2)

    assert len(positive) == len(negative) == len(pairs)
    assert positive[0].count("\n\n") == 1
    assert negative[0].count("\n\n") == 1


def test_christian_auto_extraction_prefers_non_specific_pairwise_method():
    assert _resolve_extraction_method("auto", pair_count=10, target="christian") == "pca_pairwise"
    assert _resolve_extraction_method("auto", pair_count=1, target="christian") == "mean_centered"


def test_pooled_virtue_auto_extraction_prefers_non_specific_pairwise_method():
    assert _resolve_extraction_method("auto", pair_count=10, target="virtues") == "pca_pairwise"
    assert _resolve_extraction_method("auto", pair_count=1, target="virtues") == "mean_centered"


def test_scripture_family_auto_extraction_prefers_non_specific_methods():
    assert _resolve_extraction_method("auto", pair_count=6, target="psalms") == "scripture_contrast"
    assert _resolve_extraction_method("auto", pair_count=1, target="proverbs") == "scripture_contrast"
    assert _resolve_extraction_method("auto", pair_count=4, target="gospels") == "scripture_contrast"
    assert _resolve_extraction_method("auto", pair_count=1, target="romans") == "scripture_contrast"
    assert _resolve_extraction_method("auto", pair_count=1, target="petrine") == "scripture_contrast"
    assert _resolve_extraction_method("auto", pair_count=4, target="psalms[trust]") == "scripture_contrast"
    assert _resolve_extraction_method("auto", pair_count=4, target="justice_scripture") == "scripture_contrast"
    assert (
        _resolve_extraction_method(
            "scripture_subspace_contrast",
            pair_count=4,
            target="fortitude_scripture",
        )
        == "scripture_subspace_contrast"
    )


def test_external_scripture_corpus_loader_groups_jsonl_rows(tmp_path):
    path = tmp_path / "external.jsonl"
    path.write_text(
        '{"corpus":"justice_scripture","text":"Justice text one."}\n'
        '{"target":"justice_scripture","text":"Justice text two."}\n'
        '{"corpus":"prudence_scripture","text":"Prudence text."}\n',
        encoding="utf-8",
    )

    grouped = load_external_scripture_corpora(path)

    assert grouped == {
        "justice_scripture": ["Justice text one.", "Justice text two."],
        "prudence_scripture": ["Prudence text."],
    }


def test_chunk_scripture_family_texts_can_use_external_corpus_chunks():
    chunks = _chunk_scripture_family_texts(
        tokenizer=object(),
        target="justice_scripture",
        max_length=256,
        external_scripture_corpora={"justice_scripture": ["chunk one", "chunk two"]},
    )

    assert chunks == ["chunk one", "chunk two"]


def test_split_scripture_chunks_reserves_dev_and_test_examples():
    chunks = [f"chunk {index}" for index in range(12)]

    split = _split_scripture_chunks(chunks)

    assert len(split["train"]) == 10
    assert len(split["dev"]) == 1
    assert len(split["test"]) == 1


def test_scripture_comparison_targets_keep_reference_families_for_single_target_runs():
    assert _scripture_comparison_targets(["psalms"]) == ["psalms", "proverbs", "gospels"]


def test_chunk_scripture_family_texts_can_extract_romans_book_lane():
    class _FakeTokenizer:
        def encode(self, text, add_special_tokens=False):
            return text.split()

    chunks = _chunk_scripture_family_texts(
        _FakeTokenizer(),
        target="romans",
        max_length=80,
    )

    assert chunks
    assert all(chunk.startswith("Romans ") for chunk in chunks)


def test_chunk_scripture_family_texts_can_extract_combined_petrine_lane():
    class _FakeTokenizer:
        def encode(self, text, add_special_tokens=False):
            return text.split()

    chunks = _chunk_scripture_family_texts(
        _FakeTokenizer(),
        target="petrine",
        max_length=80,
    )

    assert chunks
    assert any(chunk.startswith("1 Peter ") for chunk in chunks)
    assert any(chunk.startswith("2 Peter ") for chunk in chunks)


def test_chunk_scripture_family_texts_can_focus_psalm_vector_on_named_set():
    class _FakeTokenizer:
        def encode(self, text, add_special_tokens=False):
            return text.split()

    chunks = _chunk_scripture_family_texts(
        _FakeTokenizer(),
        target="psalms",
        max_length=80,
        psalm_vector_sets=["popular"],
    )

    assert chunks
    allowed = {1, 23, 42, 51, 88, 100, 119}
    chapter_numbers = {
        int(chunk.split("\n", 1)[0].split(" ", 1)[1].split(":", 1)[0])
        for chunk in chunks
    }
    assert chapter_numbers <= allowed


def test_chunk_scripture_family_texts_can_extract_single_psalm_family_lane():
    class _FakeTokenizer:
        def encode(self, text, add_special_tokens=False):
            return text.split()

    chunks = _chunk_scripture_family_texts(
        _FakeTokenizer(),
        target="psalms[trust]",
        max_length=80,
    )

    assert chunks
    allowed = {23, 25, 27, 31, 42, 56, 57, 61, 62, 63, 84, 91, 121, 125, 131}
    chapter_numbers = {
        int(chunk.split("\n", 1)[0].split(" ", 1)[1].split(":", 1)[0])
        for chunk in chunks
    }
    assert chapter_numbers <= allowed


def test_chunk_scripture_family_texts_can_merge_selected_psalm_families():
    class _FakeTokenizer:
        def encode(self, text, add_special_tokens=False):
            return text.split()

    chunks = _chunk_scripture_family_texts(
        _FakeTokenizer(),
        target="psalms[trust+wisdom]",
        max_length=80,
    )

    assert chunks
    allowed = {
        1, 19, 23, 25, 27, 31, 37, 42, 49, 56, 57, 61, 62, 63,
        73, 84, 91, 112, 119, 121, 125, 127, 128, 131, 139,
    }
    chapter_numbers = {
        int(chunk.split("\n", 1)[0].split(" ", 1)[1].split(":", 1)[0])
        for chunk in chunks
    }
    assert chapter_numbers <= allowed


def test_neutral_passage_splits_expand_generic_background_texts():
    records = [
        SteeringText(f"n{index}", "neutral", "neutral", "train", "src", f"Neutral line {index}.", str(index))
        for index in range(3)
    ] + [
        SteeringText("d1", "neutral", "neutral", "dev", "src", "Dev neutral one.", "d1"),
        SteeringText("d2", "neutral", "neutral", "dev", "src", "Dev neutral two.", "d2"),
        SteeringText("t1", "neutral", "neutral", "test", "src", "Test neutral one.", "t1"),
        SteeringText("t2", "neutral", "neutral", "test", "src", "Test neutral two.", "t2"),
    ]

    splits = _neutral_passage_splits(records, min_words=4, max_items=2)

    assert set(splits) == {"train", "dev", "test"}
    assert len(splits["train"]) == 3
    assert all(text for text in splits["dev"])


def test_reasoning_compare_profile_keeps_baseline_and_both_steering_lanes():
    from virtue_bench.cli import ICONOCLAST_CONDITION_PROFILES

    assert ICONOCLAST_CONDITION_PROFILES["reasoning_compare"] == [
        "control",
        "virtue_steer",
        "scripture_steer",
        "null_control",
        "scripture_null_control",
    ]


def test_reasoning_primary_profile_stays_focused_on_main_three_lanes():
    from virtue_bench.cli import ICONOCLAST_CONDITION_PROFILES

    assert ICONOCLAST_CONDITION_PROFILES["reasoning_primary"] == [
        "control",
        "virtue_steer",
        "scripture_steer",
    ]


def test_psalm_reasoning_primary_profile_keeps_only_control_and_scripture_lane():
    from virtue_bench.cli import ICONOCLAST_CONDITION_PROFILES

    assert ICONOCLAST_CONDITION_PROFILES["psalm_reasoning_primary"] == [
        "control",
        "scripture_steer",
    ]


def test_scripture_reasoning_primary_profile_alias_keeps_only_control_and_scripture_lane():
    from virtue_bench.cli import ICONOCLAST_CONDITION_PROFILES

    assert ICONOCLAST_CONDITION_PROFILES["scripture_reasoning_primary"] == [
        "control",
        "scripture_steer",
    ]


def test_scripture_study2_profile_keeps_directional_scripture_controls():
    from virtue_bench.cli import ICONOCLAST_CONDITION_PROFILES

    assert ICONOCLAST_CONDITION_PROFILES["scripture_study2"] == [
        "control",
        "scripture_steer",
        "scripture_negative_alpha",
        "scripture_null_control",
    ]
