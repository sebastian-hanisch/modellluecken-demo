"""Randfälle: nichts zulässig, genau ein zulässiger Plan, sehr große Kapazität, kleinste und größte Instanz, jede Familie, jeder Schalter."""

import itertools

import numpy as np
import pytest

import mlk_algorithm as A
import mlk_constants as C
import mlk_evaluation as ev
import mlk_scenario as S
from mlk_scenario import Instance


def _inst(a, b, forb, pairs, cap):
    return Instance(len(a), len(a[0]), tuple(map(tuple, a)), tuple(map(tuple, b)), tuple(map(tuple, forb)), tuple(pairs), cap)


def test_nothing_is_feasible_when_the_capacity_is_too_small():
    inst = _inst([[1, 2], [3, 4]], [[5, 5], [5, 5]], [[0, 0], [0, 0]], [(0, 1)], 1)
    p = A.build(inst)
    assert A.optimum(p, C.KEYS) is None and A.optimum(p, ("K",)) is None and A.optimum(p, ()) is not None
    a = ev.Analysis(ev.Settings(2, 2, 0, 0, 100, True, True, True, True), p, None, None)
    c = ev.compare(a)
    assert c["real"] is None and c["model"] is None and c["saving"] is None
    kind, text = ev.verdict_compare(c)
    assert kind == "warning" and "keine** Zuordnung zulässig" in text
    rounds = A.repair(p, "all")
    assert rounds[-1]["idx"] is None and ev.verdict_repair(rounds)[0] == "warning"
    assert ev.omit_rows(a)[0]["saving"] is None and ev.omit_rows(a)[0]["cost"] is not None      # ohne Kapazität ist das Modell lösbar, die Wirklichkeit nicht


def test_exactly_one_feasible_plan_is_the_real_optimum_and_the_only_optimal_one():
    inst = _inst([[1, 9], [9, 1]], [[1, 1], [1, 1]], [[0, 1], [1, 0]], [], 1)
    p = A.build(inst)
    assert int(p.feasible(C.KEYS).sum()) == 1
    res = A.optimum(p, C.KEYS)
    assert list(p.X[res[0]]) == [0, 1] and p.cost[res[0]] == 2 and len(res[1]) == 1


def test_a_huge_capacity_makes_the_capacity_constraint_irrelevant():
    inst = S.make_instance(3, 5, 0, 5)
    p = A.with_cap(A.build(inst), 10 ** 6)
    assert (p.over == 0).all() and A.optimum(p, ("K",))[0] == A.optimum(p, ())[0]


def test_ties_in_the_model_choose_the_first_plan_and_report_the_optimal_set():
    inst = _inst([[2, 2], [2, 2]], [[1, 1], [1, 1]], [[0, 0], [0, 0]], [], 9)
    p = A.build(inst)
    res = A.optimum(p, ())
    assert res[0] == 0 and list(res[1]) == [0, 1, 2, 3] and A.optimum(p, ("B",))[0] == 1 and list(A.optimum(p, ("B",))[1]) == [1, 2]


def test_a_task_with_only_one_allowed_person_is_always_assigned_to_that_person():
    for seed in range(10):
        inst = S.make_instance(3, 6, 0, seed)
        a_, b_, forb = inst.arrays()
        p = A.build(inst)
        res = A.optimum(p, ("Q",))
        for j in range(6):
            assert not forb[p.X[res[0]][j], j]
        assert not forb.all(axis=0).any()


@pytest.mark.parametrize("family", range(3))
@pytest.mark.parametrize("flags", list(itertools.product([False, True], repeat=4)))
def test_every_family_and_every_switch_combination_runs_every_experiment(family, flags):
    a = ev.analyse(ev.Settings(3, 5, family, 2, 125, *flags))
    c = ev.compare(a)
    ev.verdict_compare(c)
    if a.real is not None:
        ev.verdict_omit(ev.omit_rows(a))
    ev.verdict_cap(ev.cap_rows(a))
    for mode in ("all", "one"):
        ev.verdict_repair(ev.repair_rows(a, mode))
    ev.verdict_flag(ev.flag_check(a))
    ev.verdict_pressure(ev.pressure(a))


def test_smallest_and_largest_instance_sizes_run():
    for n, m in ((2, 3), (2, 8), (5, 3), (5, 6)):
        a = ev.analyse(ev.Settings(n, m, 1, 4, 100))
        assert a.p.n_plans == n ** m and ev.compare(a)["n_plans"] == n ** m


def test_the_enumeration_limit_raises_a_clear_error():
    with pytest.raises(ValueError):
        A.assignments(5, 9)
    assert A.assignments(5, 8).shape == (390625, 8)


def test_the_model_text_and_names_helpers_handle_empty_and_full_sets():
    assert ev.names(C.KEYS) == "Kapazität, Mindestbesetzung, Qualifikation, Konflikt" and ev.model_text(C.KEYS).startswith("mit ")
    assert ev.Settings().keys == () and ev.Settings(k_in=True, w_in=True).keys == ("K", "W")


def test_zero_cost_instance_has_zero_saving():
    inst = _inst([[0, 0], [0, 0]], [[1, 1], [1, 1]], [[0, 0], [0, 0]], [], 9)
    assert A.saving(0, 0) == 0.0 and A.optimum(A.build(inst), C.KEYS)[0] == 1 and np.isfinite(A.best_of_k(A.build(inst), ())["cost"]).all()
