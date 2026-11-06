"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und was jedes Preset zeigen soll."""

import mlk_constants as C
import mlk_evaluation as ev
import mlk_presets as P

(P_NONE, P_STAR, P_K, P_Q, P_B, P_TIGHT, P_SMALL, P_ALL) = list(C.PRESETS)


def _settings(name):
    pr = C.PRESETS[name]
    return ev.Settings(n=pr["n"], m=pr["m"], family=pr["family"], seed=pr["seed"], cap=pr["cap"], k_in=pr["K"], b_in=pr["B"], q_in=pr["Q"], w_in=pr["W"])


def _all(name):
    a = ev.analyse(_settings(name))
    return a, ev.compare(a)


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.M_MIN <= preset["m"] <= C.M_MAX and 0 <= preset["family"] < len(C.FAMILIES) and 0 <= preset["seed"] <= C.SEED_MAX
        assert C.CAP_MIN <= preset["cap"] <= C.CAP_MAX and (preset["cap"] - C.CAP_MIN) % C.CAP_STEP == 0
        assert all(isinstance(preset[k], bool) for k in C.KEYS)


def test_default_preset_equals_the_default_settings():
    assert _settings(P_NONE) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_non_default_preset_equals_the_default_settings():
    """Lehre aus Stück 4: ein Preset, das den Voreinstellungen gleicht, wäre nicht von „nichts geklickt“ zu unterscheiden."""
    for name in C.PRESETS:
        if name != P_NONE:
            assert _settings(name) != ev.Settings(), name


def test_permalink_booleans_parse_one_zero_and_words():
    assert P.as_bool("1") and P.as_bool("True") and P.as_bool("true") and not P.as_bool("0") and not P.as_bool("False") and not P.as_bool("")


def test_default_preset_shows_the_big_gap():
    a, c = _all(P_NONE)
    assert (c["model"]["cost"], c["real"]["cost"], round(c["saving"] * 100, 1), c["n_real"], a.p.inst.cap) == (94, 242, 61.2, 495, 12) and c["model"]["violated"] == {"K": 16, "B": 1, "Q": 1, "W": 1}


def test_star_preset_puts_all_tasks_on_one_person():
    a, c = _all(P_STAR)
    assert list(c["model"]["counts"]) == [0, 8, 0, 0] and (c["model"]["cost"], c["real"]["cost"]) == (177, 551) and c["model"]["violated"] == {"K": 22, "B": 3, "Q": 2, "W": 3}


def test_missing_capacity_and_missing_qualification_use_the_same_instance():
    a, c = _all(P_K)
    b, d = _all(P_Q)
    assert _settings(P_K).seed == _settings(P_Q).seed and (c["model"]["cost"], d["model"]["cost"], c["real"]["cost"], d["real"]["cost"]) == (270, 212, 440, 440)
    assert c["model"]["violated"]["K"] == 12 and d["model"]["violated"]["Q"] == 4 and (round(c["saving"] * 100, 1), round(d["saving"] * 100, 1)) == (38.6, 51.8)


def test_missing_staffing_is_harmless_in_its_preset():
    a, c = _all(P_B)
    assert c["model"]["cost"] == c["real"]["cost"] == 146 and c["saving"] == 0 and all(v == 0 for v in c["model"]["violated"].values())


def test_tight_capacity_preset_has_a_cap_of_ten_and_an_overload_of_nine():
    a, c = _all(P_TIGHT)
    assert a.p.inst.cap == 10 and c["model"]["violated"]["K"] == 9 and (c["model"]["cost"], c["real"]["cost"]) == (139, 205) and round(c["saving"] * 100, 1) == 32.2


def test_smallest_example_has_eight_assignments_and_one_feasible():
    a, c = _all(P_SMALL)
    assert c["n_plans"] == 8 and c["n_real"] == 1 and (c["model"]["cost"], c["real"]["cost"]) == (63, 167) and list(c["model"]["counts"]) == [0, 3]


def test_all_in_model_has_no_gap():
    a, c = _all(P_ALL)
    assert c["saving"] == 0 and c["model"]["cost"] == c["real"]["cost"] == 242
