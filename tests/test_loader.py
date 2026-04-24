import pytest

from virtue_bench.core.loader import parse_answer, prepare_samples
from virtue_bench.core.schema import Scenario


def _scenario(index: int) -> Scenario:
    return Scenario(
        base_id=f"PRU-{index:03d}",
        variant="ratio",
        scenario_a=f"Virtuous action {index}",
        scenario_b=f"Tempting action {index}",
        virtue="prudence",
        source="test",
    )


def test_parse_answer_reads_plain_ab_answer():
    assert parse_answer("A\nBecause...") == "A"
    assert parse_answer("B") == "B"


def test_parse_answer_ignores_leading_think_block():
    response = "<think>\nI should reason this through.\n</think>\nB\nBecause..."

    assert parse_answer(response) == "B"


def test_parse_answer_handles_multiple_leading_think_blocks():
    response = "<think>first</think>\n<think>second</think>\nA"

    assert parse_answer(response) == "A"


def test_parse_answer_finds_final_answer_after_visible_reasoning():
    response = (
        "Thinking Process:\n"
        "I should weigh both sides carefully.\n"
        "Final Answer: B — The delayed choice is wiser."
    )

    assert parse_answer(response) == "B"


def test_parse_answer_reads_ab_line_after_visible_reasoning():
    response = (
        "Thinking Process:\n"
        "This is hard.\n"
        "A — I would accept the short-term cost."
    )

    assert parse_answer(response) == "A"


def test_prepare_samples_offset_matches_full_run_window():
    scenarios = [_scenario(index) for index in range(1, 8)]

    full = prepare_samples(scenarios, seed=123, limit=7)
    window = prepare_samples(scenarios, seed=123, limit=3, offset=2)

    assert [sample.scenario.base_id for sample in window] == [
        sample.scenario.base_id for sample in full[2:5]
    ]
    assert [sample.target for sample in window] == [sample.target for sample in full[2:5]]


def test_prepare_samples_rejects_negative_offset():
    with pytest.raises(ValueError, match="offset"):
        prepare_samples([_scenario(1)], offset=-1)
