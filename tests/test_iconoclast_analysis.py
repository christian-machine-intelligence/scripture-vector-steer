from virtue_bench.analysis.iconoclast import (
    build_iconoclast_rows,
    build_paired_flip_rows,
    compare_paired_results,
    condition_base_name,
    condition_target,
)
from virtue_bench.core.schema import RunResult, SampleResult
from virtue_bench.stats.bootstrap import AggregatedResult


def test_condition_helpers_split_prefixed_labels():
    assert condition_base_name("virtue_steer:prudence") == "virtue_steer"
    assert condition_target("virtue_steer:prudence") == "prudence"
    assert condition_target("control") is None


def test_build_iconoclast_rows_includes_delta_vs_control():
    aggregated = [
        AggregatedResult(
            model="qwen",
            virtue="prudence",
            variant="ratio",
            condition="control",
            frame="ratio",
            n_runs=2,
            mean_accuracy=0.50,
            std_accuracy=0.01,
            ci_lower=0.49,
            ci_upper=0.51,
            accuracies=[0.49, 0.51],
        ),
        AggregatedResult(
            model="qwen",
            virtue="prudence",
            variant="ratio",
            condition="virtue_steer:prudence",
            frame="ratio",
            n_runs=2,
            mean_accuracy=0.65,
            std_accuracy=0.02,
            ci_lower=0.63,
            ci_upper=0.67,
            accuracies=[0.63, 0.67],
        ),
    ]

    rows = build_iconoclast_rows(aggregated)

    assert rows[0][3] == "control"
    assert rows[1][3] == "virtue_steer:prudence"
    assert rows[1][-1] == "+0.1500"


def test_compare_paired_results_counts_changes_improves_and_regressions():
    control = RunResult(
        model="qwen",
        virtue="courage",
        variant="ratio",
        condition="control",
        frame="ratio",
        run_index=0,
        seed=42,
        temperature=0.0,
        accuracy=0.5,
        stderr=None,
        samples=2,
        status="success",
        sample_details=[
            SampleResult(
                sample_id="one",
                variant="ratio",
                target="A",
                model_response="A",
                model_answer="A",
                correct=True,
                prompt="p1",
            ),
            SampleResult(
                sample_id="two",
                variant="ratio",
                target="A",
                model_response="B",
                model_answer="B",
                correct=False,
                prompt="p2",
            ),
        ],
    )
    candidate = RunResult(
        model="qwen",
        virtue="courage",
        variant="ratio",
        condition="virtue_steer:courage",
        frame="ratio",
        run_index=0,
        seed=42,
        temperature=0.0,
        accuracy=0.5,
        stderr=None,
        samples=2,
        status="success",
        sample_details=[
            SampleResult(
                sample_id="one",
                variant="ratio",
                target="A",
                model_response="B",
                model_answer="B",
                correct=False,
                prompt="p1",
            ),
            SampleResult(
                sample_id="two",
                variant="ratio",
                target="A",
                model_response="A",
                model_answer="A",
                correct=True,
                prompt="p2",
            ),
        ],
    )

    stats = compare_paired_results(control, candidate)

    assert stats["compared"] == 2
    assert stats["answer_changes"] == 2
    assert stats["correctness_changes"] == 2
    assert stats["improve"] == 1
    assert stats["regress"] == 1


def test_build_paired_flip_rows_aggregates_against_control():
    control = RunResult(
        model="qwen",
        virtue="prudence",
        variant="ratio",
        condition="control",
        frame="ratio",
        run_index=0,
        seed=42,
        temperature=0.0,
        accuracy=0.5,
        stderr=None,
        samples=1,
        status="success",
        sample_details=[
            SampleResult(
                sample_id="one",
                variant="ratio",
                target="A",
                model_response="B",
                model_answer="B",
                correct=False,
                prompt="p1",
            ),
        ],
    )
    steered = RunResult(
        model="qwen",
        virtue="prudence",
        variant="ratio",
        condition="virtue_steer:prudence",
        frame="ratio",
        run_index=0,
        seed=42,
        temperature=0.0,
        accuracy=1.0,
        stderr=None,
        samples=1,
        status="success",
        sample_details=[
            SampleResult(
                sample_id="one",
                variant="ratio",
                target="A",
                model_response="A",
                model_answer="A",
                correct=True,
                prompt="p1",
            ),
        ],
    )

    rows = build_paired_flip_rows([control, steered])

    assert rows == [[
        "ratio",
        "prudence",
        "ratio",
        "virtue_steer:prudence",
        "1",
        "1",
        "1",
        "1",
        "0",
        "+1",
        "0",
        "0",
    ]]
