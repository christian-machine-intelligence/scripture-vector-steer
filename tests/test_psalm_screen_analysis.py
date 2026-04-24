from virtue_bench.analysis.psalm_screen import choose_representative_scale, representative_scale_key


def test_representative_scale_key_prefers_fewer_regressions_then_more_improvements():
    a = {
        "delta_vs_control": 0.05,
        "regressions": 3,
        "improvements": 5,
        "diagnostics": {"steered_test_margin": 0.2},
    }
    b = {
        "delta_vs_control": 0.05,
        "regressions": 2,
        "improvements": 4,
        "diagnostics": {"steered_test_margin": 0.1},
    }

    assert representative_scale_key(b) > representative_scale_key(a)


def test_choose_representative_scale_uses_steered_test_margin_as_last_tiebreak():
    summaries = [
        {
            "family_label": "trust",
            "alpha_scale": 0.75,
            "delta_vs_control": 0.0,
            "regressions": 2,
            "improvements": 2,
            "diagnostics": {"steered_test_margin": 0.10},
        },
        {
            "family_label": "trust",
            "alpha_scale": 1.5,
            "delta_vs_control": 0.0,
            "regressions": 2,
            "improvements": 2,
            "diagnostics": {"steered_test_margin": 0.25},
        },
    ]

    chosen = choose_representative_scale(summaries)

    assert chosen is not None
    assert chosen["alpha_scale"] == 1.5
