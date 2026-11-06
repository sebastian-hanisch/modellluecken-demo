"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für jede Instanz gelten müssen, an festen Seeds und allen Familien."""

import itertools

import numpy as np
import pytest

import mlk_algorithm as A
import mlk_constants as C
import mlk_evaluation as ev
import mlk_scenario as S
from mlk_scenario import Instance

CASES = [(n, m, family, seed) for n, m in ((2, 4), (3, 5), (4, 6)) for family in (0, 1, 2) for seed in (3, 4)]
SUBSETS = [keys for r in range(5) for keys in itertools.combinations(C.KEYS, r)]


def _p(n, m, family, seed, cap=125):
    return A.build(S.make_instance(n, m, family, seed, cap))


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_the_model_optimum_is_never_more_expensive_than_the_real_one_and_the_saving_is_not_negative(n, m, family, seed):
    p = _p(n, m, family, seed)
    real = A.optimum(p, C.KEYS)
    if real is None:
        pytest.skip("mit allen Nebenbedingungen ist nichts zulässig")
    for keys in SUBSETS:
        res = A.optimum(p, keys)
        assert p.cost[res[0]] <= p.cost[real[0]] and A.saving(int(p.cost[real[0]]), int(p.cost[res[0]])) >= 0


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_more_constraints_in_the_model_never_make_the_optimum_cheaper(n, m, family, seed):
    p = _p(n, m, family, seed)
    for keys in SUBSETS:
        for extra in C.KEYS:
            if extra in keys:
                continue
            small, big = A.optimum(p, keys), A.optimum(p, keys + (extra,))
            if big is not None:
                assert p.cost[big[0]] >= p.cost[small[0]]
            else:
                assert A.optimum(p, C.KEYS) is None


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_a_model_with_all_four_constraints_has_no_gap_and_is_really_feasible(n, m, family, seed):
    p = _p(n, m, family, seed)
    res = A.optimum(p, C.KEYS)
    if res is None:
        pytest.skip("unlösbar")
    assert all(v == 0 for v in A.violated(p, res[0]).values()) and p.feasible(C.KEYS)[res[0]]


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_repair_ends_after_at_most_four_rounds_in_the_real_optimum_and_the_cost_never_falls(n, m, family, seed):
    p = _p(n, m, family, seed)
    real = A.optimum(p, C.KEYS)
    for mode in ("all", "one"):
        rounds = A.repair(p, mode)
        if real is None:
            assert rounds[-1]["idx"] is None
            continue
        costs = [r["cost"] for r in rounds]
        assert costs == sorted(costs) and costs[-1] == p.cost[real[0]] and len(rounds) - 1 <= 4 and rounds[-1]["feasible"]
    if real is not None:
        assert len(A.repair(p, "all")) <= len(A.repair(p, "one"))


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_the_costs_of_the_optima_do_not_depend_on_the_numbering_of_the_persons(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed)
    perm = np.random.default_rng(seed).permutation(n)
    inst2 = Instance(n, m, tuple(inst.a[i] for i in perm), tuple(inst.b[i] for i in perm), tuple(inst.forb[i] for i in perm), inst.pairs, inst.cap)
    p1, p2 = A.build(inst), A.build(inst2)
    for keys in SUBSETS:
        r1, r2 = A.optimum(p1, keys), A.optimum(p2, keys)
        assert (r1 is None) == (r2 is None)
        if r1 is not None:
            assert p1.cost[r1[0]] == p2.cost[r2[0]] and len(r1[1]) == len(r2[1])


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_a_larger_capacity_never_hurts_and_loosens_the_overload(n, m, family, seed):
    p = _p(n, m, family, seed)
    prev = None
    for cap in (6, 9, 12, 20, 40):
        q = A.with_cap(p, cap)
        res = A.optimum(q, ("K",))
        assert res is not None or prev is None
        if res is not None:
            c = int(q.cost[res[0]])
            assert prev is None or c <= prev
            prev = c
    assert A.optimum(A.with_cap(p, 10 ** 6), ("K",))[0] == A.optimum(p, ())[0]                 # unbegrenzte Kapazität: gleich dem Modell ohne K


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_best_of_k_weights_make_the_expected_cost_fall_and_k_one_is_the_mean(n, m, family, seed):
    p = _p(n, m, family, seed)
    out = A.best_of_k(p, (), [1, 2, 8, 64, None])
    assert out["cost"][0] == pytest.approx(p.cost.mean()) and (np.diff(out["cost"]) <= 1e-9).all() and out["cost"][-1] == p.cost[A.optimum(p, ())[0]]
    assert out["p_real"][0] == pytest.approx(p.feasible(C.KEYS).mean()) and all(0 <= v <= 1 for v in out["p_real"])


def test_everything_is_deterministic():
    a1, a2 = ev.analyse(ev.Settings(3, 5, 1, 9)), ev.analyse(ev.Settings(3, 5, 1, 9))
    assert (a1.p.cost == a2.p.cost).all() and ev.compare(a1)["saving"] == ev.compare(a2)["saving"] and ev.omit_rows(a1) == ev.omit_rows(a2)
