"""Gemeinsame Fixtures: das Handbeispiel (2 Personen, 3 Aufgaben), an dem jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mlk_algorithm as A  # noqa: E402
import mlk_evaluation as ev  # noqa: E402
from mlk_scenario import Instance  # noqa: E402


def make_hand() -> Instance:
    return Instance(n=2, m=3, a=((1, 2, 3), (5, 4, 6)), b=((2, 2, 2), (2, 2, 2)), forb=((0, 0, 0), (0, 1, 0)), pairs=((0, 2),), cap=4)


@pytest.fixture
def hand() -> Instance:
    """Handbeispiel: Kosten P0 (1, 2, 3), P1 (5, 4, 6); alle Zeiten 2; Kapazität 4 Stunden; verboten ist (P1, A2); Konflikt A1 und A3; je Person mindestens eine Aufgabe.
    Zuordnungen (Person je Aufgabe) in der Reihenfolge von itertools.product mit (Kosten, Überlast, ohne Aufgabe, verboten, Konflikt):
    (0,0,0): (6, 2, 1, 0, 1); (0,0,1): (9, 0, 0, 0, 0); (0,1,0): (8, 0, 0, 1, 1); (0,1,1): (11, 0, 0, 1, 0);
    (1,0,0): (10, 0, 0, 0, 0); (1,0,1): (13, 0, 0, 0, 1); (1,1,0): (12, 0, 0, 1, 0); (1,1,1): (15, 2, 1, 1, 1)."""
    return make_hand()


@pytest.fixture
def hand_problem(hand) -> A.Problem:
    return A.build(hand)


@pytest.fixture
def hand_analysis(hand_problem) -> ev.Analysis:
    return ev.Analysis(ev.Settings(2, 3, 0, 0, 125), hand_problem, A.optimum(hand_problem, ()), A.optimum(hand_problem, ("K", "B", "Q", "W")))
