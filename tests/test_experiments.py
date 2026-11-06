"""Experimente der App: jedes Preset, jede Familie, jeder Schalter, jede Größe und alle Zählungen laufen ohne Fehler."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import mlk_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    return " ".join(m.value for kind in ("success", "info", "warning") for m in getattr(at, kind))


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_runs_and_shows_a_verdict(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, (name, [str(e) for e in at.exception])
    assert "Das Modell" in _texts(at)


def test_default_preset_shows_the_scheinersparnis():
    assert "**61,2 % billiger**" in _texts(_app())


@pytest.mark.parametrize("key", ["k_in_toggle", "b_in_toggle", "q_in_toggle", "w_in_toggle"])
def test_every_switch_runs(key):
    at = _app()
    at.sidebar.toggle(key=key).set_value(True).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "Das Modell mit " in _texts(at)


def test_all_switches_on_show_no_gap():
    at = _app()
    for key in ("k_in_toggle", "b_in_toggle", "q_in_toggle", "w_in_toggle"):
        at.sidebar.toggle(key=key).set_value(True)
    at.run()
    assert not at.exception and "keine Lücke" in _texts(at)


@pytest.mark.parametrize("family", range(len(C.FAMILIES)))
def test_every_family_runs(family):
    at = _app()
    at.sidebar.selectbox(key="family_select").set_value(family).run()
    assert not at.exception, [str(e) for e in at.exception]


@pytest.mark.parametrize("cap", [C.CAP_MIN, 150, C.CAP_MAX])
def test_capacity_extremes_run(cap):
    at = _app()
    at.sidebar.slider(key="cap_slider").set_value(cap).run()
    assert not at.exception, [str(e) for e in at.exception]


@pytest.mark.parametrize("n,m", [(2, 3), (2, 8), (5, 5), (3, 8)])
def test_sizes_run(n, m):
    at = _app()
    at.sidebar.slider(key="n_slider").set_value(n).run()
    at.sidebar.slider(key="m_slider").set_value(m).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "Das Modell" in _texts(at)


@pytest.mark.parametrize("mode", ["all", "one"])
def test_both_repair_modes_run(mode):
    at = _app()
    at.radio(key="repair_mode").set_value(mode).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert "Prüfen und Nachbessern ist das Optimum wirklich zulässig" in _texts(at)


def test_the_sweeps_run_when_switched_on():
    at = _app()
    for key in ("sweep_none", "sweep_omit", "sweep_cap", "sweep_repair", "sweep_flag", "sweep_pressure"):
        at.toggle(key=key).set_value(True).run()
        assert not at.exception, (key, [str(e) for e in at.exception])
    text = _texts(at)
    assert "Je Nebenbedingung als einzige ausgelassen" in text and "Prüfen und Nachbessern (Runden" in text and "Auffälligkeitstest (Last des Höchstbelasteten" in text and "Best-of-k im Modell ohne Nebenbedingung" in text
