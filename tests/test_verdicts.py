"""Verdikte: Art und Wortlaut in den Fällen, die sie unterscheiden (DEMO-PLAYBOOK §6): jede Zahl im Text kommt aus der Rechnung."""

import mlk_constants as C
import mlk_evaluation as ev

(P_NONE, P_STAR, P_K, P_Q, P_B, P_TIGHT, P_SMALL, P_ALL) = list(C.PRESETS)


def _settings(name):
    pr = C.PRESETS[name]
    return ev.Settings(n=pr["n"], m=pr["m"], family=pr["family"], seed=pr["seed"], cap=pr["cap"], k_in=pr["K"], b_in=pr["B"], q_in=pr["Q"], w_in=pr["W"])


def _a(name):
    return ev.analyse(_settings(name))


def test_compare_verdict_distinguishes_gap_harmless_and_no_gap():
    kind, text = ev.verdict_compare(ev.compare(_a(P_NONE)))
    assert kind == "warning" and text.startswith("Das Modell ohne Nebenbedingung wählt Kosten **94** und verletzt, was fehlt: **Überlast 16 Stunden, 1 Person ohne Aufgabe, 1 verbotenes Paar, 1 verletzter Konflikt**")
    assert "Das wirkliche Optimum kostet 242" in text and "**61,2 % billiger**" in text and "495 von 65536 Zuordnungen (0,76 %)" in text
    kind, text = ev.verdict_compare(ev.compare(_a(P_K)))
    assert kind == "warning" and "Das Modell mit Mindestbesetzung, Qualifikation, Konflikt wählt Kosten **270**" in text and "**Überlast 12 Stunden**" in text and "**38,6 % billiger**" in text
    kind, text = ev.verdict_compare(ev.compare(_a(P_Q)))
    assert kind == "warning" and "**4 verbotene Paare**" in text and "**51,8 % billiger**" in text
    kind, text = ev.verdict_compare(ev.compare(_a(P_B)))
    assert kind == "success" and text == "Das Modell mit Kapazität, Qualifikation, Konflikt wählt Kosten 146, genau das wirkliche Optimum. Hier ist keine fehlende Nebenbedingung verletzt: das Modell liegt zufällig richtig."
    kind, text = ev.verdict_compare(ev.compare(_a(P_ALL)))
    assert kind == "success" and "genau das wirkliche Optimum. Das Modell kennt alle Nebenbedingungen, die hier zählen: keine Lücke." in text
    kind, text = ev.verdict_compare(ev.compare(_a(P_STAR)))
    assert "3 Personen ohne Aufgabe" in text and "**67,9 % billiger**" in text


def test_compare_verdict_for_a_feasible_but_not_optimal_model():
    """Ein Modell mit Nebenbedingung, die die Wirklichkeit nicht hat (hier: schärfere Kapazität über f in der Instanz) wäre zulässig, aber teurer: der Fall „zulässig, nicht optimal“."""
    c = {"keys": ("K", "B", "Q", "W"), "real": {"cost": 10}, "model": {"cost": 12, "violated": {"K": 0, "B": 0, "Q": 0, "W": 0}}, "n_real": 5, "n_plans": 100, "share_real": 0.05, "saving": -0.2}
    kind, text = ev.verdict_compare(c)
    assert kind == "info" and "zulässig, aber nicht optimal" in text


def test_omit_verdict_names_the_biggest_gap():
    kind, text = ev.verdict_omit(ev.omit_rows(_a(P_NONE)))
    assert kind == "info" and text == ("ohne Kapazität verletzt (Größe 6, Scheinersparnis 48,8 %); ohne Mindestbesetzung nicht verletzt (Scheinersparnis 0,0 %); ohne Qualifikation verletzt (Größe 3, Scheinersparnis 30,6 %); "
                                       "ohne Konflikt nicht verletzt (Scheinersparnis 0,0 %). Die größte Scheinersparnis entsteht ohne Kapazität (48,8 %).")
    assert "Die größte Scheinersparnis entsteht ohne Qualifikation (51,8 %)." in ev.verdict_omit(ev.omit_rows(_a(P_Q)))[1]
    assert "Die größte Scheinersparnis entsteht ohne Konflikt (18,1 %)." in ev.verdict_omit(ev.omit_rows(_a(P_STAR)))[1]


def test_cap_verdict_shows_the_tightness_and_unsolvable_cases():
    kind, text = ev.verdict_cap(ev.cap_rows(_a(P_NONE)))
    assert kind == "info" and "f = 100 %: Kapazität 9 h, Überlast 12 h, Scheinersparnis 60,0 %" in text and "f = 200 %: Kapazität 18 h, Überlast 0 h, Scheinersparnis 0,0 %" in text and "Ab f = 200 % bindet die Kapazität bei dieser Instanz nicht mehr." in text
    kind, text = ev.verdict_cap(ev.cap_rows(_a(P_K)))
    assert "f = 100 %: Kapazität 11 h, unlösbar" in text and text.endswith("Bei keinem f verschwindet die Überlast.")


def test_repair_verdict_counts_rounds_for_both_modes():
    a = _a(P_NONE)
    assert ev.verdict_repair(ev.repair_rows(a, "all"))[1] == ("Nach **1** Runde Prüfen und Nachbessern ist das Optimum wirklich zulässig: die Kosten steigen von 94 auf **242** (61,2 % der wirklichen Kosten waren Schein). "
                                                              "Aufgenommen wurden: Kapazität, Mindestbesetzung, Qualifikation, Konflikt.")
    assert ev.verdict_repair(ev.repair_rows(a, "one"))[1].startswith("Nach **2** Runden Prüfen und Nachbessern") and "Aufgenommen wurden: Kapazität, Qualifikation." in ev.verdict_repair(ev.repair_rows(a, "one"))[1]
    assert "Nach **3** Runden" in ev.verdict_repair(ev.repair_rows(_a(P_STAR), "one"))[1]
    already = [{"keys": (), "idx": 3, "cost": 7, "violated": {"K": 0, "B": 0, "Q": 0, "W": 0}, "add": (), "feasible": True}]
    kind, text = ev.verdict_repair(already)
    assert kind == "success" and "keine Nachbesserung nötig" in text and "Kosten 7" in text
    assert ev.verdict_repair([{"keys": (), "idx": None, "cost": None, "violated": {}, "add": (), "feasible": False}])[0] == "warning"


def test_flag_verdict_cases():
    kind, text = ev.verdict_flag(ev.flag_check(_a(P_NONE)))
    assert kind == "info" and "bei der Modell-Lösung das 2,15-fache der mittleren Last (schlägt an, Schwelle 1,5), beim wirklichen Optimum das 1,21-fache (schlägt nicht an)." in text
    both = {"model": {"flagged": True, "ratio": 2.0, "overload": 3}, "real": {"flagged": True, "ratio": 1.6}}
    kind, text = ev.verdict_flag(both)
    assert kind == "warning" and "Auch das wirkliche Optimum schlägt an" in text
    miss = {"model": {"flagged": False, "ratio": 1.2, "overload": 4}, "real": {"flagged": False, "ratio": 1.1}}
    kind, text = ev.verdict_flag(miss)
    assert kind == "warning" and "schlägt **nicht** an: der Test übersieht sie" in text
    assert ev.verdict_flag({"model": None, "real": None})[0] == "info"


def test_pressure_verdict_states_costs_and_probability():
    kind, text = ev.verdict_pressure(ev.pressure(_a(P_NONE)))
    assert kind == "info" and text.startswith("Mit stärkerem Druck (k von 1 bis ∞) fallen die erwarteten Kosten von 390,0 auf 94,0, und die Wahrscheinlichkeit einer wirklich zulässigen Wahl von 0,76 % auf 0,00 %.")
    assert ev.verdict_pressure({"cost": []})[1] == "Das Modell hat keine zulässige Zuordnung."


def test_sweep_verdicts_carry_the_phase_zero_numbers():
    sw = ev.sweep_all()
    none = {fam: ev.summary_none(recs) for fam, recs in sw.items()}
    assert [none[f]["all_one"] for f in (0, 1, 2)] == [0, 0, 13] and [none[f]["idle3"] for f in (0, 1, 2)] == [0, 0, 13]
    assert "alle 8 bei einer Person in 13 von 20" in ev.verdict_none_sweep(none[2], "star")
    omit = {fam: ev.summary_omit(recs) for fam, recs in sw.items()}
    assert [[omit[f][k]["violated"] for k in C.KEYS] for f in (0, 1, 2)] == [[18, 3, 17, 11], [20, 4, 19, 13], [20, 12, 18, 16]]
    text = ev.verdict_omit_sweep(omit)[1]
    assert "ohne Kapazität: verletzt in 18 von 20, Scheinersparnis Median 15,7 % (Maximum 48,8 %)" in text and "ohne Qualifikation: verletzt in 17 von 20, Scheinersparnis Median 20,0 % (Maximum 62,4 %)" in text
    caps = ev.summary_caps(sw[0])
    assert [(r["cap"], r["violated"], r["unsolvable"]) for r in caps] == [(10, 20, 2), (13, 18, 0), (15, 14, 0), (20, 6, 0)]
    assert "in 2 Instanzen ist mit allen Nebenbedingungen nichts zulässig" in ev.verdict_cap_sweep(caps)[1]
    rep = {fam: ev.summary_repair(recs) for fam, recs in sw.items()}
    assert rep[0]["all"]["hist"] == [0, 11, 8, 1] and rep[0]["one"]["hist"] == [0, 2, 7, 9, 2] and rep[1]["all"]["hist"] == [0, 16, 4] and all(rep[f]["all"]["same"] == 20 for f in (0, 1, 2))
    flag = {fam: ev.summary_flag(recs) for fam, recs in sw.items()}
    assert [(flag[f]["n_over"], flag[f]["flag_over"], flag[f]["real_flag"]) for f in (0, 1, 2)] == [(18, 14, 7), (20, 17, 4), (20, 19, 12)]
    assert "bei Überlast (18 Instanzen) schlägt der Test in 14 an" in ev.verdict_flag_sweep(flag)[1]
    pr = ev.summary_pressure(sw[0])
    assert [round(v * 100, 2) for v in pr["p_real"]] == [0.68, 0.56, 0.59, 0.15, 0.0, 0.0, 0.0, 0.0] and [round(v, 1) for v in pr["cost"]] == [391.1, 314.6, 261.3, 224.5, 198.6, 178.6, 163.9, 147.5]
