from pathlib import Path

from virtue_bench.core.psalms import load_psalm_text


def test_load_psalm_text_falls_back_to_bundled_bible():
    text = load_psalm_text(psalm_numbers=[23], source_path=Path("/tmp/virtue-bench-missing-psalms.json"))

    assert "23" in text
    assert "shepherd" in text.lower()
