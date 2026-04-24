from virtue_bench.core.loader import parse_answer


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
