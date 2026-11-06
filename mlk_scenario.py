"""Szenario: m Aufgaben werden auf n Personen verteilt (jede Aufgabe genau einer Person). Kosten a[i][j] (ganze Zahlen), Zeit b[i][j] (1 bis 9). Alles simuliert.

Die „Wirklichkeit“ hat vier Nebenbedingungen (K Kapazität, B Mindestbesetzung, Q Qualifikation, W Konflikt), das „Modell“ nur eine Auswahl davon.
Die Erzeugung entspricht den Messreihen der Planung (gleiche Seeds, gleiche Reihenfolge der Ziehungen)."""

import math
from dataclasses import dataclass

import numpy as np

import mlk_constants as C


@dataclass(frozen=True)
class Instance:
    n: int
    m: int
    a: tuple                  # Kosten, n Zeilen (Personen) mal m Spalten (Aufgaben)
    b: tuple                  # Zeit
    forb: tuple               # verbotene Paare (Person, Aufgabe) als 0/1
    pairs: tuple              # Konfliktpaare von Aufgaben
    cap: int                  # Kapazität in Stunden

    def arrays(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return np.array(self.a, dtype=np.int64), np.array(self.b, dtype=np.int64), np.array(self.forb, dtype=bool)


def capacity(b: np.ndarray, n: int, cap_pct: int) -> int:
    """Kapazität: aufgerundet f * (Summe der mittleren Zeiten je Aufgabe) / n, f = cap_pct / 100 (Vielfache von 25 sind in float64 exakt)."""
    return int(math.ceil((cap_pct / 100.0) * b.mean(axis=0).sum() / n))


def make_instance(n: int, m: int, family: int, seed: int, cap_pct: int = C.DEFAULT_CAP) -> Instance:
    """Deterministisch aus (n, m, Familie, Seed, Kapazitätsfaktor)."""
    rng = np.random.default_rng(seed)
    if family == 0:
        a = rng.integers(1, 100, (n, m))
    elif family == 1:
        a = rng.integers(0, 41, (n, 1)) + rng.integers(1, 61, (n, m))
    else:
        a = rng.integers(0, 151, (n, 1)) + rng.integers(1, 31, (n, m))
    b = rng.integers(1, 10, (n, m))
    forb = rng.random((n, m)) < C.FORBID_P
    for j in range(m):
        if forb[:, j].all():
            forb[rng.integers(0, n), j] = False
    n_pairs = min(C.MAX_PAIRS, m // 2)
    tasks = rng.permutation(m)[:2 * n_pairs].reshape(n_pairs, 2)
    return Instance(n, m, tuple(tuple(int(x) for x in row) for row in a), tuple(tuple(int(x) for x in row) for row in b), tuple(tuple(int(x) for x in row) for row in forb.astype(int)),
                    tuple((int(p[0]), int(p[1])) for p in tasks), capacity(b, n, cap_pct))
