"""Kern der Demo (numpy): alle Zuordnungen von m Aufgaben auf n Personen, vier Nebenbedingungen der Wirklichkeit und ein Modell, das nur einige davon kennt.

  * `assignments`: alle n^m Zuordnungen (Zeile = Person je Aufgabe), in der Reihenfolge von itertools.product.
  * `Problem`: Kosten, Last und Aufgabenzahl je Person sowie die vier Verletzungsgrößen je Zuordnung (Überlast in Stunden, Personen ohne Aufgabe, verbotene Paare, Konflikte).
  * `optimum`: das Optimum unter einer Auswahl von Nebenbedingungen (bei Gleichstand der kleinste Index der Aufzählung) und die ganze Optimalmenge.
  * `repair`: Prüfen und Nachbessern (Nebenbedingungserzeugung): Modell lösen, gegen die Wirklichkeit prüfen, verletzte Nebenbedingungen aufnehmen, bis das Optimum wirklich zulässig ist.
  * `best_of_k`: Erwartung der Kosten und Wahrscheinlichkeit einer wirklich zulässigen Wahl, wenn man unter k zufällig gezogenen (modellzulässigen) Zuordnungen die billigste wählt;
    die Formel der Ordnungsstatistik stammt aus Stück 8 der Linie (goodhart-kurve-demo).
"""

from dataclasses import dataclass

import numpy as np

import mlk_constants as C
from mlk_scenario import Instance

_BIG = np.iinfo(np.int64).max


def assignments(n: int, m: int) -> np.ndarray:
    """Alle n^m Zuordnungen (Zeile = Person je Aufgabe), in der Reihenfolge von itertools.product (die erste Aufgabe ist die höchste Stelle)."""
    if n < 1 or m < 1 or n ** m > 400_000:
        raise ValueError(f"n = {n}, m = {m}: Aufzählung nur bis 400 000 Zuordnungen")
    return ((np.arange(n ** m)[:, None] // n ** np.arange(m - 1, -1, -1)[None, :]) % n).astype(np.int8)


@dataclass
class Problem:
    inst: Instance
    X: np.ndarray             # Zuordnungen
    cost: np.ndarray          # Kosten je Zuordnung
    loads: np.ndarray         # Zeitsumme je Person (N x n)
    counts: np.ndarray        # Aufgaben je Person (N x n)
    over: np.ndarray          # Überlast in Stunden (Summe über die Personen)
    idle: np.ndarray          # Personen ohne Aufgabe
    forbid: np.ndarray        # verbotene Paare
    conf: np.ndarray          # verletzte Konflikte

    @property
    def n_plans(self) -> int:
        return len(self.cost)

    @property
    def viol(self) -> dict:
        return {"K": self.over, "B": self.idle, "Q": self.forbid, "W": self.conf}

    def feasible(self, keys) -> np.ndarray:
        """Welche Zuordnungen erfüllen alle Nebenbedingungen in keys?"""
        ok = np.ones(self.n_plans, dtype=bool)
        for k in keys:
            ok &= self.viol[k] == 0
        return ok


def build(inst: Instance) -> Problem:
    n, m = inst.n, inst.m
    a, b, forb = inst.arrays()
    X = assignments(n, m)
    idx = np.arange(m)
    cost = a[X, idx].sum(axis=1)
    loads = np.zeros((len(X), n), dtype=np.int64)
    counts = np.zeros((len(X), n), dtype=np.int64)
    for i in range(n):
        mask = X == i
        loads[:, i] = (mask * b[i]).sum(axis=1)
        counts[:, i] = mask.sum(axis=1)
    over = np.maximum(0, loads - inst.cap).sum(axis=1)
    idle = (counts == 0).sum(axis=1)
    forbid = forb[X, idx].sum(axis=1)
    conf = np.zeros(len(X), dtype=np.int64)
    for j1, j2 in inst.pairs:
        conf += (X[:, j1] == X[:, j2])
    return Problem(inst, X, cost, loads, counts, over, idle, forbid, conf)


def with_cap(p: Problem, cap: int) -> Problem:
    """Dieselbe Instanz mit anderer Kapazität (nur die Überlast ändert sich)."""
    from dataclasses import replace
    inst = replace(p.inst, cap=int(cap))
    return Problem(inst, p.X, p.cost, p.loads, p.counts, np.maximum(0, p.loads - int(cap)).sum(axis=1), p.idle, p.forbid, p.conf)


def optimum(p: Problem, keys) -> tuple[int, np.ndarray] | None:
    """Optimum unter den Nebenbedingungen in keys: (Index des ersten Optimalplans, alle Optimalpläne); None, wenn keine Zuordnung zulässig ist."""
    feas = p.feasible(keys)
    if not feas.any():
        return None
    c = np.where(feas, p.cost, _BIG)
    best = c.min()
    opt = np.flatnonzero(c == best)
    return int(opt[0]), opt


def violated(p: Problem, idx: int) -> dict:
    """Verletzungsgrößen einer Zuordnung je Nebenbedingung (0 = erfüllt)."""
    return {k: int(v[idx]) for k, v in p.viol.items()}


def saving(real_cost: float, model_cost: float) -> float:
    """Scheinersparnis: wie viel billiger das Modell-Optimum aussieht als das wirkliche (in Anteilen der wirklichen Kosten)."""
    return (real_cost - model_cost) / real_cost if real_cost else 0.0


def repair(p: Problem, mode: str = "all") -> list[dict]:
    """Prüfen und Nachbessern ab dem Modell ohne Nebenbedingung. Je Runde: Modell (Nebenbedingungen), Optimum, Kosten, verletzte Nebenbedingungen und welche dazukommen.
    mode "all": alle verletzten auf einmal; "one": die erste verletzte in der Reihenfolge K, B, Q, W. Endet, wenn das Optimum wirklich zulässig ist (oder nichts zulässig ist)."""
    keys: list[str] = []
    rounds = []
    while True:
        res = optimum(p, tuple(keys))
        if res is None:
            rounds.append({"keys": tuple(keys), "idx": None, "cost": None, "violated": {}, "add": (), "feasible": False})
            return rounds
        idx = res[0]
        bad = [k for k in C.KEYS if int(p.viol[k][idx]) > 0]
        add = tuple(bad) if mode == "all" else tuple(bad[:1])
        rounds.append({"keys": tuple(keys), "idx": idx, "cost": int(p.cost[idx]), "violated": violated(p, idx), "add": add, "feasible": not bad})
        if not bad:
            return rounds
        keys += list(add)


def flagged(loads_row: np.ndarray) -> bool:
    """Auffälligkeitstest: trägt die am stärksten belastete Person mindestens das FLAG_RATIO-fache der mittleren Last?"""
    mean = float(np.mean(loads_row))
    return bool(mean > 0 and float(np.max(loads_row)) >= C.FLAG_RATIO * mean)


def best_of_k(p: Problem, keys, ks=C.PRESSURE_KS) -> dict:
    """Unter k gleichverteilt (mit Zurücklegen) aus den modellzulässigen Zuordnungen gezogenen die billigste wählen (Gleichstand: kleinster Index): Erwartung der Kosten, der Überlast,
    der verbotenen Paare und die Wahrscheinlichkeit einer wirklich zulässigen Wahl, exakt aus der Ordnungsstatistik; k = None ist das Optimum."""
    feas = np.flatnonzero(p.feasible(keys))
    if len(feas) == 0:
        return {"ks": list(ks), "cost": [], "p_real": [], "over": [], "forbid": []}
    order = feas[np.argsort(p.cost[feas], kind="stable")]
    real = p.feasible(C.KEYS)[order].astype(float)
    cost, over, forbid = p.cost[order].astype(float), p.over[order].astype(float), p.forbid[order].astype(float)
    n_f = len(order)
    r = np.arange(1, n_f + 1, dtype=float)
    out = {"ks": list(ks), "cost": [], "p_real": [], "over": [], "forbid": []}
    for k in ks:
        if k is None:
            w = np.zeros(n_f)
            w[0] = 1.0
        else:
            w = ((n_f - r + 1) / n_f) ** k - ((n_f - r) / n_f) ** k
        out["cost"].append(float(w @ cost))
        out["p_real"].append(float(w @ real))
        out["over"].append(float(w @ over))
        out["forbid"].append(float(w @ forbid))
    return out
