"""Jede Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4). Aufzählung und feste Instanzerzeugung sind deterministisch."""

from pathlib import Path

import pytest

import mlk_constants as C
import mlk_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
(P_NONE, P_STAR, P_K, P_Q, P_B, P_TIGHT, P_SMALL, P_ALL) = list(C.PRESETS)


def _claim(text):
    assert text in README, text


def _slash(values, fmt):
    return " / ".join(fmt(v) for v in values)


def _settings(name):
    pr = C.PRESETS[name]
    return ev.Settings(n=pr["n"], m=pr["m"], family=pr["family"], seed=pr["seed"], cap=pr["cap"], k_in=pr["K"], b_in=pr["B"], q_in=pr["Q"], w_in=pr["W"])


@pytest.fixture(scope="module")
def sw():
    return ev.sweep_all()


def _de0(x):
    return ev.de(x, 0)


def thousands(x):
    return f"{int(round(x)):,}".replace(",", " ")


def test_sweep_instances_are_the_documented_ones():
    assert C.SWEEP_SEEDS == tuple(range(100000, 100020)) and (C.SWEEP_N, C.SWEEP_M) == (4, 8) and C.SWEEP_CAPS == (100, 125, 150, 200) and C.DEFAULT_CAP == 125
    _claim("Seeds 100000 bis 100019")


def test_unconstrained_model_claims(sw):
    none = {f: ev.summary_none(sw[f]) for f in (0, 1, 2)}
    assert _slash([none[f]["conc"][i] for f in (0, 1, 2) for i in (0, 1, 2)], _de0) == "2 / 4 / 4 / 3 / 4 / 6 / 4 / 8 / 8"
    _claim("2 / 4 / 4; 3 / 4 / 6; 4 / 8 / 8; **alle 8 bei einer Person in 0 / 0 / 13 von 20**; mindestens 3 Personen ohne Aufgabe in 0 / 0 / 13")
    assert [none[f]["all_one"] for f in (0, 1, 2)] == [0, 0, 13] and [none[f]["idle3"] for f in (0, 1, 2)] == [0, 0, 13]
    over = [" / ".join(_de0(none[f]["over"][i]) for i in (0, 1, 2)) for f in (0, 1, 2)]
    assert over == ["0 / 7 / 19", "2 / 10 / 24", "7 / 26 / 48"]
    _claim("0 / 7 / 19; 2 / 10 / 24; 7 / 26 / 48")
    sav = [" / ".join(ev.pct(none[f]["saving"][i]) for i in (0, 1, 2)) for f in (0, 1, 2)]
    assert sav == ["0,0 % / 33,4 % / 67,4 %", "13,8 % / 26,9 % / 43,9 %", "19,8 % / 42,4 % / 76,2 %"]
    _claim("; ".join(sav))
    assert " / ".join(thousands(none[0]["n_real"][i]) for i in (0, 1, 2)) == "15 / 444 / 1 676" and " / ".join(thousands(none[1]["n_real"][i]) for i in (0, 1, 2)) == "34 / 442 / 914"
    assert [ev.pct(none[0]["share_real"][i], 2) for i in (0, 1, 2)] == ["0,02 %", "0,68 %", "2,56 %"] and [ev.pct(none[1]["share_real"][i], 2) for i in (0, 1, 2)] == ["0,05 %", "0,67 %", "1,39 %"]
    _claim("unabhängig 15 / 444 / 1 676 (0,02 % / 0,68 % / 2,56 %); Person und star 34 / 442 / 914 (0,05 % / 0,67 % / 1,39 %)")


def test_omit_claims(sw):
    om = {f: ev.summary_omit(sw[f]) for f in (0, 1, 2)}
    assert [[om[f][k]["violated"] for f in (0, 1, 2)] for k in C.KEYS] == [[18, 20, 20], [3, 4, 12], [17, 19, 18], [11, 13, 16]]
    _claim("**18 / 20 / 20** von 20")
    _claim("verletzt in **3 / 4 / 12** von 20")
    _claim("verletzt in **17 / 19 / 18** von 20")
    _claim("verletzt in 11 / 13 / 16 von 20")
    assert _slash([om[f]["K"]["size_med"] for f in (0, 1, 2)], lambda v: ev.de(v, 1)) == "5,5 / 8,0 / 11,0" and [om[f]["K"]["size_max"] for f in (0, 1, 2)] == [15, 16, 24]
    _claim("5,5 (15) / 8,0 (16) / 11,0 (24) Stunden")
    assert _slash([om[f]["K"]["saving"][1] for f in (0, 1, 2)], ev.pct) == "15,7 % / 7,4 % / 11,8 %" and _slash([om[f]["K"]["saving"][2] for f in (0, 1, 2)], ev.pct) == "48,8 % / 26,5 % / 24,4 %"
    _claim("15,7 % (48,8 %) / 7,4 % (26,5 %) / 11,8 % (24,4 %)")
    assert _slash([om[f]["B"]["saving"][1] for f in (0, 1, 2)], ev.pct) == "0,0 % / 0,0 % / 0,7 %" and _slash([om[f]["B"]["saving"][2] for f in (0, 1, 2)], ev.pct) == "10,4 % / 4,5 % / 24,1 %"
    _claim("Scheinersparnis Median **0,0 % / 0,0 % / 0,7 %** (Maximum 10,4 % / 4,5 % / 24,1 %)")
    assert [om[f]["Q"]["size_med"] for f in (0, 1, 2)] == [2.0, 2.0, 2.0] and [om[f]["Q"]["size_max"] for f in (0, 1, 2)] == [4, 4, 3]
    assert _slash([om[f]["Q"]["saving"][1] for f in (0, 1, 2)], ev.pct) == "20,0 % / 11,6 % / 5,6 %" and _slash([om[f]["Q"]["saving"][2] for f in (0, 1, 2)], ev.pct) == "62,4 % / 31,0 % / 18,0 %"
    _claim("Median 2 verbotene Paare, Maximum 4 / 4 / 3); Scheinersparnis Median **20,0 % / 11,6 % / 5,6 %** (Maximum **62,4 %** / 31,0 % / 18,0 %)")
    assert _slash([om[f]["W"]["saving"][1] for f in (0, 1, 2)], ev.pct) == "1,7 % / 1,8 % / 2,6 %" and _slash([om[f]["W"]["saving"][2] for f in (0, 1, 2)], ev.pct) == "23,7 % / 10,7 % / 18,1 %"
    _claim("Scheinersparnis Median 1,7 % / 1,8 % / 2,6 % (Maximum 23,7 % / 10,7 % / 18,1 %)")
    assert [om[0][k]["first_ok"] for k in C.KEYS] + [om[0]["none"]["first_ok"]] == [2, 17, 3, 9, 0] and om[0]["none"]["n_opt"][1] == 1.0 and om[0]["K"]["n_opt"][2] == 2.0
    _claim("**2 / 17 / 3 / 9 / 0**; die Optimalmenge hat im Median einen Plan (Maximum 2)")


def test_capacity_claims(sw):
    caps = ev.summary_caps(sw[0])
    assert [(r["cap"], r["violated"], r["unsolvable"]) for r in caps] == [(10, 20, 2), (13, 18, 0), (15, 14, 0), (20, 6, 0)]
    assert _slash([r["over_med"] for r in caps], lambda v: ev.de(v, 1)) == "10,0 / 5,0 / 2,5 / 0,0"
    assert " / ".join(f"{ev.pct(r['saving'][1])} ({ev.pct(r['saving'][2])})" for r in caps) == "29,1 % (60,0 %) / 15,7 % (48,8 %) / 3,1 % (35,4 %) / 0,0 % (11,2 %)"
    _claim("**20 / 18 / 14 / 6** von 20; 10,0 / 5,0 / 2,5 / 0,0; 29,1 % (60,0 %) / 15,7 % (48,8 %) / 3,1 % (35,4 %) / 0,0 % (11,2 %); bei f = 1,0 ist in **2** von 20 Instanzen mit allen vier Nebenbedingungen nichts zulässig (ausgenommen)")


def test_repair_claims(sw):
    rep = {f: ev.summary_repair(sw[f]) for f in (0, 1, 2)}
    assert rep[0]["all"]["rounds"] == (1.0, 1.0, 3.0) and rep[0]["all"]["hist"] == [0, 11, 8, 1] and rep[1]["all"]["rounds"] == (1.0, 1.0, 2.0) and rep[1]["all"]["hist"] == [0, 16, 4]
    assert rep[0]["one"]["rounds"] == (1.0, 3.0, 4.0) and rep[0]["one"]["hist"] == [0, 2, 7, 9, 2] and rep[1]["one"]["rounds"] == (1.0, 3.0, 4.0) and rep[1]["one"]["hist"] == [0, 1, 5, 6, 8]
    assert all(rep[f][m]["same"] == 20 for f in (0, 1, 2) for m in ("all", "one"))
    _claim("unabhängig 1 / 1 / 3; 11 / 8 / 1 von 20; Person 1 / 1 / 2; 16 / 4 / 0; **eine je Runde** unabhängig 1 / 3 / 4 Runden (2 / 7 / 9 / 2 von 20 für 1 bis 4), Person 1 / 3 / 4 (1 / 5 / 6 / 8); Ergebnis gleich dem wirklichen Optimum in **20 / 20**")


def test_flag_claims(sw):
    fl = {f: ev.summary_flag(sw[f]) for f in (0, 1, 2)}
    assert [(fl[f]["flag_over"], fl[f]["n_over"], fl[f]["flag_ok"], fl[f]["n_ok"], fl[f]["real_flag"]) for f in (0, 1, 2)] == [(14, 18, 1, 2, 7), (17, 20, 0, 0, 4), (19, 20, 0, 0, 12)]
    _claim("unabhängig 14 von 18; 1 von 2; **7 von 20**. Person 17 von 20; 0 von 0; **4 von 20**. star 19 von 20; 0 von 0; **12 von 20**")


def test_pressure_claims(sw):
    pr = ev.summary_pressure(sw[0])
    assert _slash(pr["p_real"], lambda v: ev.pct(v, 2)) == "0,68 % / 0,56 % / 0,59 % / 0,15 % / 0,00 % / 0,00 % / 0,00 % / 0,00 %"
    _claim("0,68 % / 0,56 % / 0,59 % / 0,15 % / 0,00 % / 0,00 % / 0,00 % / 0,00 %")
    assert _slash(pr["cost"], lambda v: ev.de(v, 1)) == "391,1 / 314,6 / 261,3 / 224,5 / 198,6 / 178,6 / 163,9 / 147,5" and _slash(pr["over"], lambda v: ev.de(v, 1)) == "6,7 / 6,8 / 6,8 / 6,6 / 6,7 / 6,5 / 6,0 / 7,0"
    _claim("391,1 / 314,6 / 261,3 / 224,5 / 198,6 / 178,6 / 163,9 / 147,5; erwartete Überlast 6,7 / 6,8 / 6,8 / 6,6 / 6,7 / 6,5 / 6,0 / 7,0 Stunden")


def test_preset_claims():
    def run(name):
        a = ev.analyse(_settings(name))
        return a, ev.compare(a)
    a, c = run(P_NONE)
    assert (c["model"]["cost"], c["real"]["cost"], ev.pct(c["saving"]), c["model"]["violated"], c["n_real"], len(ev.repair_rows(a, "all")) - 1, len(ev.repair_rows(a, "one")) - 1) == (94, 242, "61,2 %", {"K": 16, "B": 1, "Q": 1, "W": 1}, 495, 1, 2)
    _claim("Kosten **94** statt **242**, Scheinersparnis **61,2 %**; verletzt: Überlast **16** Stunden, 1 Person ohne Aufgabe, 1 verbotenes Paar, 1 Konflikt; **495** von 65 536 Zuordnungen wirklich zulässig; Nachbessern: **1** Runde (alle) beziehungsweise **2** (eine je Runde)")
    a, c = run(P_STAR)
    assert (c["model"]["cost"], c["real"]["cost"], ev.pct(c["saving"]), list(c["model"]["counts"]), c["model"]["violated"], len(ev.repair_rows(a, "one")) - 1) == (177, 551, "67,9 %", [0, 8, 0, 0], {"K": 22, "B": 3, "Q": 2, "W": 3}, 3)
    _claim("Kosten **177** statt **551** (**67,9 %**), alle 8 Aufgaben bei Person 2, Überlast **22** Stunden, **3** Personen ohne Aufgabe; eine je Runde **3** Runden")
    a, c = run(P_K)
    b, d = run(P_Q)
    assert (c["model"]["cost"], d["model"]["cost"], c["real"]["cost"], ev.pct(c["saving"]), ev.pct(d["saving"]), c["model"]["violated"]["K"], d["model"]["violated"]["Q"], c["n_real"]) == (270, 212, 440, "38,6 %", "51,8 %", 12, 4, 15)
    _claim("ohne K: Kosten **270** statt **440** (**38,6 %**), Überlast **12** Stunden; ohne Q: Kosten **212** statt **440** (**51,8 %**), **4** verbotene Paare")
    _claim("(Seed 100014, **15** zulässige Zuordnungen)")
    a, c = run(P_B)
    assert c["model"]["cost"] == c["real"]["cost"] == 146 and c["saving"] == 0
    _claim("das Modell wählt Kosten **146**, genau das wirkliche Optimum: Scheinersparnis **0**")
    a, c = run(P_TIGHT)
    assert (a.p.inst.cap, c["model"]["violated"]["K"], c["model"]["cost"], c["real"]["cost"], ev.pct(c["saving"])) == (10, 9, 139, 205, "32,2 %")
    _claim("Kapazität **10** Stunden, Überlast **9**, Kosten **139** statt **205** (**32,2 %**)")
    a, c = run(P_SMALL)
    assert (c["n_real"], c["n_plans"], c["model"]["cost"], c["real"]["cost"], ev.pct(c["saving"]), list(c["model"]["counts"]), c["model"]["violated"]["K"]) == (1, 8, 63, 167, "62,3 %", [0, 3], 14)
    _claim("**1** von 8 Zuordnungen zulässig; Kosten **63** statt **167** (**62,3 %**): alle drei Aufgaben bei einer Person, Überlast **14** Stunden")
