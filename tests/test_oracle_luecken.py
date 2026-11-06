"""Orakel-Test modellluecken-demo: der Kern gegen einen ANDEREN Rechenweg (ORACLE-PLAYBOOK §2, DEMO-PLAYBOOK §12).

Reines Python (itertools.product, Schleifen, keine numpy-Zeile im Referenzweg) gegen die Vektorrechnung: Verletzungen je Zuordnung, Optimum je Teilmenge der Nebenbedingungen,
Prüfen und Nachbessern und Best-of-k gegen die Aufzählung aller Ziehungen."""

import itertools
from fractions import Fraction

import pytest

import mlk_algorithm as A
import mlk_constants as C
import mlk_scenario as S

CASES = [(n, m, family, seed) for n, m in ((2, 3), (2, 5), (3, 4), (3, 5), (4, 4)) for family in (0, 1, 2) for seed in (1, 2)]


def _plain(inst):
    """Alle Zuordnungen mit (Kosten, Überlast, Personen ohne Aufgabe, verbotene Paare, Konflikte) in reinem Python."""
    out = []
    for x in itertools.product(range(inst.n), repeat=inst.m):
        cost = sum(inst.a[x[j]][j] for j in range(inst.m))
        loads = [sum(inst.b[i][j] for j in range(inst.m) if x[j] == i) for i in range(inst.n)]
        over = sum(max(0, load - inst.cap) for load in loads)
        idle = sum(1 for i in range(inst.n) if x.count(i) == 0)
        forbid = sum(inst.forb[x[j]][j] for j in range(inst.m))
        conf = sum(1 for p, q in inst.pairs if x[p] == x[q])
        out.append((x, cost, {"K": over, "B": idle, "Q": forbid, "W": conf}))
    return out


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_violations_and_costs_match_the_plain_python_enumeration(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed)
    p = A.build(inst)
    plain = _plain(inst)
    assert p.n_plans == len(plain)
    for k, (x, cost, viol) in enumerate(plain):
        assert tuple(int(v) for v in p.X[k]) == x and int(p.cost[k]) == cost
        assert {key: int(p.viol[key][k]) for key in C.KEYS} == viol


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_the_optimum_for_every_subset_of_constraints_matches_plain_python(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed)
    p = A.build(inst)
    plain = _plain(inst)
    for r in range(5):
        for keys in itertools.combinations(C.KEYS, r):
            feasible = [(cost, k) for k, (x, cost, viol) in enumerate(plain) if all(viol[key] == 0 for key in keys)]
            got = A.optimum(p, keys)
            if not feasible:
                assert got is None
                continue
            best = min(c for c, _ in feasible)
            expected = [k for c, k in feasible if c == best]
            assert got[0] == expected[0] and list(got[1]) == expected, keys


@pytest.mark.parametrize("n,m,family,seed", CASES)
def test_repair_matches_an_independent_loop_and_ends_in_the_real_optimum(n, m, family, seed):
    inst = S.make_instance(n, m, family, seed)
    p = A.build(inst)
    plain = _plain(inst)

    def solve(keys):
        feas = [(cost, k) for k, (x, cost, viol) in enumerate(plain) if all(viol[key] == 0 for key in keys)]
        return min(feas) if feas else None

    for mode in ("all", "one"):
        keys, ref = [], []
        while True:
            sol = solve(keys)
            if sol is None:
                break
            cost, k = sol
            bad = [key for key in C.KEYS if plain[k][2][key] > 0]
            ref.append((tuple(keys), cost, tuple(bad) if mode == "all" else tuple(bad[:1])))
            if not bad:
                break
            keys += list(ref[-1][2])
        got = A.repair(p, mode)
        if solve(C.KEYS) is None:
            assert got[-1]["idx"] is None
            continue
        assert [(r["keys"], r["cost"], r["add"]) for r in got] == ref
        assert got[-1]["cost"] == solve(C.KEYS)[0] and got[-1]["feasible"]
        assert len(got) - 1 <= 4


@pytest.mark.parametrize("keys", [(), ("K",), ("B", "W"), C.KEYS])
@pytest.mark.parametrize("k", [1, 2, 3])
def test_best_of_k_matches_the_enumeration_of_all_draws(keys, k):
    inst = S.make_instance(2, 3, 0, 4)
    p = A.build(inst)
    plain = _plain(inst)
    feas = [i for i, (x, cost, viol) in enumerate(plain) if all(viol[key] == 0 for key in keys)]
    if not feas:
        pytest.skip("das Modell hat keine zulässige Zuordnung")
    real = [all(plain[i][2][key] == 0 for key in C.KEYS) for i in range(len(plain))]
    total_c = total_r = Fraction(0)
    for draw in itertools.product(feas, repeat=k):
        win = min(draw, key=lambda i: (plain[i][1], i))
        total_c += plain[win][1]
        total_r += 1 if real[win] else 0
    got = A.best_of_k(p, keys, [k])
    assert got["cost"][0] == pytest.approx(float(total_c / len(feas) ** k), rel=1e-12)
    assert got["p_real"][0] == pytest.approx(float(total_r / len(feas) ** k), rel=1e-12)


def test_the_cap_formula_matches_a_ceiling_in_exact_fractions():
    import math
    for seed in range(8):
        inst = S.make_instance(4, 6, 0, seed)
        for pct in (100, 125, 150, 175, 200):
            ref = math.ceil(Fraction(pct, 100) * sum(Fraction(sum(inst.b[i][j] for i in range(4)), 4) for j in range(6)) / 4)
            assert S.capacity(inst.arrays()[1], 4, pct) == ref
