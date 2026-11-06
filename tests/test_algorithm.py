"""Handwerte: jede Einheit des Kerns an einem Beispiel, das von Hand nachgerechnet ist (DEMO-PLAYBOOK §1b)."""

import itertools

import numpy as np
import pytest

import mlk_algorithm as A
import mlk_constants as C
import mlk_evaluation as ev
import mlk_scenario as S

PLANS = list(itertools.product(range(2), repeat=3))
HAND = {(0, 0, 0): (6, 2, 1, 0, 1), (0, 0, 1): (9, 0, 0, 0, 0), (0, 1, 0): (8, 0, 0, 1, 1), (0, 1, 1): (11, 0, 0, 1, 0),
        (1, 0, 0): (10, 0, 0, 0, 0), (1, 0, 1): (13, 0, 0, 0, 1), (1, 1, 0): (12, 0, 0, 1, 0), (1, 1, 1): (15, 2, 1, 1, 1)}


def _plan(idx):
    return tuple(int(x) for x in A.assignments(2, 3)[idx])


def test_assignments_follow_the_order_of_itertools_product():
    for n, m in ((2, 3), (3, 4), (4, 3)):
        assert (A.assignments(n, m) == np.array(list(itertools.product(range(n), repeat=m)))).all()
    with pytest.raises(ValueError):
        A.assignments(5, 9)


def test_hand_example_all_eight_assignments(hand_problem):
    p = hand_problem
    for k, plan in enumerate(PLANS):
        assert (int(p.cost[k]), int(p.over[k]), int(p.idle[k]), int(p.forbid[k]), int(p.conf[k])) == HAND[plan]


def test_hand_example_optima_for_the_interesting_models(hand_problem):
    p = hand_problem
    assert _plan(A.optimum(p, ())[0]) == (0, 0, 0) and p.cost[A.optimum(p, ())[0]] == 6
    real = A.optimum(p, C.KEYS)
    assert _plan(real[0]) == (0, 0, 1) and p.cost[real[0]] == 9 and list(real[1]) == [1]
    for keys in (("K",), ("B",)):
        assert _plan(A.optimum(p, keys)[0]) == (0, 1, 0) and p.cost[A.optimum(p, keys)[0]] == 8
    for omit in C.KEYS:
        keys = tuple(k for k in C.KEYS if k != omit)
        assert _plan(A.optimum(p, keys)[0]) == (0, 0, 1)
    assert int(p.feasible(C.KEYS).sum()) == 2 and [_plan(i) for i in np.flatnonzero(p.feasible(C.KEYS))] == [(0, 0, 1), (1, 0, 0)]


def test_hand_example_saving_and_violations(hand_problem):
    p = hand_problem
    j = A.optimum(p, ())[0]
    assert A.violated(p, j) == {"K": 2, "B": 1, "Q": 0, "W": 1}
    assert A.saving(9, 6) == pytest.approx(1 / 3) and A.saving(9, 8) == pytest.approx(1 / 9) and A.saving(0, 0) == 0.0


def test_hand_example_repair_all_and_one(hand_problem):
    rounds = A.repair(hand_problem, "all")
    assert [(r["keys"], r["cost"], r["add"], r["feasible"]) for r in rounds] == [((), 6, ("K", "B", "W"), False), (("K", "B", "W"), 9, (), True)]
    rounds = A.repair(hand_problem, "one")
    assert [(r["keys"], r["cost"], r["add"], r["feasible"]) for r in rounds] == [((), 6, ("K",), False), (("K",), 8, ("Q",), False), (("K", "Q"), 9, (), True)]
    assert rounds[1]["violated"] == {"K": 0, "B": 0, "Q": 1, "W": 1}


def test_hand_example_best_of_k_with_the_model_without_constraints(hand_problem):
    out = A.best_of_k(hand_problem, (), [1, 2, None])
    costs = sorted([6, 9, 8, 11, 10, 13, 12, 15])                      # Rangfolge nach Kosten
    real_flag = {6: 0, 8: 0, 9: 1, 10: 1, 11: 0, 12: 0, 13: 0, 15: 0}
    assert out["cost"][0] == pytest.approx(sum(costs) / 8) and out["p_real"][0] == pytest.approx(2 / 8)
    w2 = [((8 - r + 1) / 8) ** 2 - ((8 - r) / 8) ** 2 for r in range(1, 9)]
    assert out["cost"][1] == pytest.approx(sum(w * c for w, c in zip(w2, costs))) and out["p_real"][1] == pytest.approx(sum(w * real_flag[c] for w, c in zip(w2, costs)))
    assert out["cost"][2] == 6 and out["p_real"][2] == 0.0


def test_flagged_and_pressure_on_the_hand_example(hand_problem):
    assert A.flagged(np.array([6, 0])) and not A.flagged(np.array([4, 2])) and not A.flagged(np.array([0, 0]))
    assert A.flagged(hand_problem.loads[0]) and not A.flagged(hand_problem.loads[1])           # (0,0,0): Last (6, 0); (0,0,1): Last (4, 2)


def test_capacity_and_instance_are_deterministic_and_shaped():
    a = S.make_instance(4, 8, 0, 7)
    assert a == S.make_instance(4, 8, 0, 7) and a != S.make_instance(4, 8, 0, 8)
    ar, br, fr = a.arrays()
    assert ar.shape == br.shape == fr.shape == (4, 8) and not fr.all(axis=0).any() and len(a.pairs) == 3 and len({t for p in a.pairs for t in p}) == 6
    assert a.cap == S.capacity(br, 4, 125) and S.capacity(br, 4, 100) <= S.capacity(br, 4, 150) <= S.capacity(br, 4, 200)
    assert len(S.make_instance(2, 3, 0, 1).pairs) == 1 and len(S.make_instance(3, 5, 1, 1).pairs) == 2


def test_with_cap_changes_only_the_overload(hand_problem):
    p2 = A.with_cap(hand_problem, 6)
    assert (p2.over == 0).all() and (p2.cost == hand_problem.cost).all() and p2.inst.cap == 6
    assert A.optimum(p2, ("K",))[0] == 0                                                         # bei Kapazität 6 ist (0,0,0) zulässig


def test_evaluation_summaries_of_the_hand_example(hand_analysis):
    c = ev.compare(hand_analysis)
    assert (c["model"]["cost"], c["real"]["cost"], c["n_real"], c["n_plans"], c["n_model"]) == (6, 9, 2, 8, 8) and c["saving"] == pytest.approx(1 / 3)
    assert c["model"]["violated"] == {"K": 2, "B": 1, "Q": 0, "W": 1} and not c["model"]["first_ok"] and c["model"]["n_opt"] == 1 and list(c["model"]["counts"]) == [3, 0]
    rows = ev.omit_rows(hand_analysis)
    assert [(r["omit"], r["cost"], r["violated"]) for r in rows] == [("K", 9, False), ("B", 9, False), ("Q", 9, False), ("W", 9, False)] and all(r["saving"] == 0 for r in rows)
    assert ev.names(("K", "Q")) == "Kapazität, Qualifikation" and ev.names(()) == "keine" and ev.model_text(()) == "ohne Nebenbedingung" and ev.model_text(("W",)) == "mit Konflikt"
    assert ev.de(3.14159, 2) == "3,14" and ev.pct(0.3338) == "33,4 %"
    f = ev.flag_check(hand_analysis)
    assert f["model"]["flagged"] and f["model"]["overload"] == 2 and not f["real"]["flagged"]
